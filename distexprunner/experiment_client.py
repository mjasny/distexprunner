
import asyncio
import logging
import pathlib
import sys
import traceback
import os
import importlib.util
import itertools
import time

from . import registry
from .enums import Action
from .server_list import ServerList
from .server import Server
from .notification import Notifier
from ._resume_manager import ResumeManager
from . import _progressbar as ProgressBar
from ._exceptions import BadReturnCode


class ExperimentClient:
    def __init__(self, experiments, compatibility_mode, resume, notifier: Notifier, progress: bool):
        self.__compatibility_mode = compatibility_mode
        self.__resume = resume
        self.__notifier = notifier
        self.__progress = progress
        self.__raise = True

        for exp in experiments:
            path = pathlib.Path(exp)
            if path.is_file():
                self.__read_file(path)
            elif path.is_dir():
                self.__read_folder(path)
            else:
                raise Exception(f'{path} is neither a file or directory.')

    def __read_folder(self, folder):
        logging.info(f'Reading folder: {folder.as_posix()}')
        for path in folder.glob('**/*.py'):
            self.__read_file(path)

    def __read_file(self, file):
        if self.__compatibility_mode:
            return self.__read_file_v1(file)

        logging.info(f'Reading file: {file.as_posix()}')

        module_name = file.as_posix()[:-len(file.suffix)].replace('/', '.')
        spec = importlib.util.spec_from_file_location(
            module_name, file.as_posix())
        module = importlib.util.module_from_spec(spec)

        sys.path.append(file.parent.as_posix())
        spec.loader.exec_module(module)
        sys.path.pop()

    def __read_file_v1(self, file):
        from v1_compatibility import experiment, config

        logging.info(
            f'Reading file: {file.as_posix()} (in compatibility mode)')

        module_name = file.as_posix()[:-len(file.suffix)].replace('/', '.')
        spec = importlib.util.spec_from_file_location(
            module_name, file.as_posix())
        module = importlib.util.module_from_spec(spec)

        old_modules = sys.modules
        sys.modules['time'] = experiment.time
        sys.modules['experiment'] = experiment
        sys.modules['config'] = config

        sys.path.append(file.parent.as_posix())
        spec.loader.exec_module(module)
        sys.path.pop()

        sys.modules = old_modules

        for cls in module.__dict__.values():
            if isinstance(cls, type) and issubclass(cls, experiment.Base):
                logging.info(f'Found experiment: {cls.__name__}')
                proxy = experiment.Proxy(cls)
                registry.reg_exp(proxy.server_list)(proxy)

    def __format_duration(self, s):
        hours, remainder = divmod(s, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{hours:02.0f}:{minutes:02.0f}:{seconds:07.4f}'

    def run_experiments(self):
        resume_manager = ResumeManager()
        if not self.__resume:
            resume_manager.reset()
        experiments = registry.ExperimentStore.get()
        logging.info(f'Total experiments: {len(experiments)}')

        if self.__progress:
            ProgressBar.enable_trapping()
            ProgressBar.setup_scroll_area()

        def exception_handler(loop, context):
            loop.default_exception_handler(context)

            exception = context.get('exception')
            if isinstance(exception, BadReturnCode):
                logging.error(exception)
                self.__raise = False
                loop.stop()

        def ignore_exception_handler(loop, context):
            exception = context.get('exception')
            if isinstance(exception, BadReturnCode):
                return
            loop.default_exception_handler(context)

        loop = asyncio.get_event_loop()

        totalstart = time.time()
        for i, (grp_name, name, servers, experiment, params, max_restarts, raise_on_rc, run_always) in enumerate(experiments):

            exp_name = f'{grp_name}__{experiment.__name__}'

            if not run_always and resume_manager.was_run(exp_name, params):
                logging.info(
                    f'Experiment {i+1}/{len(experiments)} ({name}) was already run.')
                if self.__progress:
                    ProgressBar.draw_progress_bar((i+1)*100//len(experiments))
                continue

            logging.info(
                f'Running experiment {i+1}/{len(experiments)} ({name})')

            if raise_on_rc:
                loop.set_exception_handler(exception_handler)
            else:
                loop.set_exception_handler(ignore_exception_handler)

            try:
                servers._connect_to_all()
            except Exception as e:
                ProgressBar.destroy_scroll_area()
                raise

            start = time.time()

            restarts = range(
                max_restarts) if max_restarts != 0 else itertools.count(start=0)
            for _ in restarts:
                try:
                    ret = experiment(servers, **params)
                except Exception as e:
                    ProgressBar.destroy_scroll_area()
                    raise
                if ret != Action.RESTART:
                    break
                logging.info(f'Restarting experiment {name}')

                loop.run_until_complete(asyncio.sleep(1))

            servers._disconnect_from_all()
            if not run_always:
                resume_manager.add_run(exp_name, params)
            logging.info(
                f'Experiment {name} finished in {time.time()-start:.4f} seconds.')

            if self.__progress:
                ProgressBar.draw_progress_bar((i+1)*100//len(experiments))

        duration = self.__format_duration(time.time() - totalstart)
        logging.info(f'Finished {len(experiments)} experiments in {duration}')

        if self.__progress:
            ProgressBar.destroy_scroll_area()
        # if not self.__resume:
        #     # keep history if resume is not set
        #     resume_manager.reset()

        self.__notifier.on_finish(len(experiments))

    def start(self):
        try:
            self.run_experiments()
        except KeyboardInterrupt:
            logging.error('Terminating Client caused by Ctrl-C')
        except RuntimeError:
            if self.__raise:
                ProgressBar.destroy_scroll_area()
                raise
        finally:
            import asyncio
            from contextlib import suppress

            loop = asyncio.get_event_loop()
            tasks = asyncio.all_tasks(loop=loop)
            for task in tasks:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    loop.run_until_complete(task)
            logging.info(f'Cancelled {len(tasks)} running tasks.')
            loop.close()
