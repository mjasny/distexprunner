
import asyncio
import logging
import pathlib
import sys
import os
import importlib.util
import time

from . import registry
from .enums import Action
from .server_list import ServerList
from .server import Server
from .notification import Notifier
from ._resume_manager import ResumeManager
from ._progressbar import Progress
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
            else:
                self.__read_folder(path)


    def __read_folder(self, folder):
        logging.info(f'Reading folder: {folder.as_posix()}')
        for path in folder.glob('**/*.py'):
            self.__read_file(path)


    def __read_file(self, file):
        if self.__compatibility_mode:
            return self.__read_file_v1(file)
        
        logging.info(f'Reading file: {file.as_posix()}')

        module_name = file.as_posix()[:-len(file.suffix)].replace('/', '.')
        spec = importlib.util.spec_from_file_location(module_name, file.as_posix())
        module = importlib.util.module_from_spec(spec)

        sys.path.append(file.parent.as_posix())
        spec.loader.exec_module(module)
        sys.path.pop()


    def __read_file_v1(self, file):
        from v1_compatibility import experiment, config

        logging.info(f'Reading file: {file.as_posix()} (in compatibility mode)')

        module_name = file.as_posix()[:-len(file.suffix)].replace('/', '.')
        spec = importlib.util.spec_from_file_location(module_name, file.as_posix())
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
        experiments = registry.ExperimentStore.get()
        logging.info(f'Total experiments: {len(experiments)}')

        if self.__progress:
            self.__progressbar = Progress(len(experiments))


        def exception_handler(loop, context):
            loop.default_exception_handler(context)

            exception = context.get('exception')
            if isinstance(exception, BadReturnCode):
                if self.__progress:
                    self.__progressbar.step(error=exception)
                else:
                    logging.error(exception)
                self.__raise = False
                loop.stop()
            
        loop = asyncio.get_event_loop()

        totalstart = time.time()
        for i, (name, servers, experiment, max_restarts, raise_on_rc) in enumerate(experiments):
            if self.__progress:
                self.__progressbar.step(name)

            if self.__resume and resume_manager.was_run(name):
                logging.info(f'Experiment {i+1}/{len(experiments)} ({name}) was already run.')
                continue

            logging.info(f'Running experiment {i+1}/{len(experiments)} ({name})')

            if raise_on_rc:
                loop.set_exception_handler(exception_handler)
            else:
                loop.set_exception_handler(None)

            servers._connect_to_all()

            start = time.time()

            # iter(int, 1) => infinite
            restarts = range(max_restarts) if max_restarts != 0 else iter(int, 1) 
            for _ in restarts:
                ret = experiment(servers)
                if ret != Action.RESTART:
                    break
                logging.info(f'Restarting experiment {name}')

            servers._disconnect_from_all()
            resume_manager.add_run(name)
            logging.info(f'Experiment {name} finished in {time.time()-start:.4f} seconds.')


        duration = self.__format_duration(time.time() - totalstart)
        logging.info(f'Finished {len(experiments)} experiments in {duration}')
        resume_manager.reset()
        if self.__progress:
            self.__progressbar.finish()

        self.__notifier.on_finish(len(experiments))


    def start(self):
        try:
            self.run_experiments()
        except KeyboardInterrupt:
            logging.error('Terminating Client caused by Ctrl-C')
            if self.__progress:
                self.__progressbar.step(error='KeyboardInterrupt')
        except RuntimeError:
            if self.__raise:
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

    