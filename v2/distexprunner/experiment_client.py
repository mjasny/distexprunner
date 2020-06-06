
import logging
import pathlib
import sys
import os
import importlib.util
import time

from . import registry
from .server_list import ServerList
from .server import Server
from . import utils


class ExperimentClient:
    def __init__(self, experiments, compatibility_mode):
        self.__compatibility_mode = compatibility_mode
        self.tmp = []
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
        logging.info(f'Reading file: {file.as_posix()}')

        module_name = file.as_posix()[:-len(file.suffix)].replace('/', '.')
        spec = importlib.util.spec_from_file_location(module_name, file.as_posix())
        module = importlib.util.module_from_spec(spec)

        if self.__compatibility_mode:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'v1_compatibility'))
            old_time = sys.modules['time']
            class new_time:
                @staticmethod
                def sleep(delay):
                    utils.sleep(delay)

            sys.modules['time'] = new_time #maybe other modules in same style

        sys.path.append(file.parent.as_posix())
        spec.loader.exec_module(module)
        sys.path.pop()

        if self.__compatibility_mode:
            sys.modules['time'] = old_time
            import experiment
            sys.path.pop(0)
            
            for cls in module.__dict__.values():
                if isinstance(cls, type) and issubclass(cls, experiment.Base):
                    logging.info(f'Found experiment: {cls.__name__}')
                    proxy = experiment.Proxy(cls)
                    registry.exp_reg(proxy.server_list)(proxy)



    def __format_duration(self, s):
        hours, remainder = divmod(s, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{hours:02.0f}:{minutes:02.0f}:{seconds:07.4f}'


    def start(self):
        logging.info(f'Total experiments: {len(registry.EXPERIMENTS)}')

        totalstart = time.time()
        for i, (name, servers, experiment) in enumerate(registry.EXPERIMENTS):
            servers.connect_to_all()
            logging.info(f'Running experiment {i+1}/{len(registry.EXPERIMENTS)} ({name})')

            start = time.time()
            experiment(servers)

            logging.info(f'Experiment {name} finished in {time.time()-start:.4f} seconds.')

            servers.disconnect_from_all()

        duration = self.__format_duration(time.time() - totalstart)
        logging.info(f'Finished {len(registry.EXPERIMENTS)} experiments in {duration}')