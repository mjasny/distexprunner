
import logging
import pathlib
import sys
import importlib.util
import time

from . import registry
from .server_list import ServerList
from .server import Server
from .utils import sleep #, forward_stdin_to


class ExperimentClient:
    def __init__(self, experiments):
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

        name = file.as_posix()[:-len(file.suffix)].replace('/', '.')
        print(name)
        spec = importlib.util.spec_from_file_location(name, file.as_posix())
        module = importlib.util.module_from_spec(spec)
        sys.path.append(file.parent.as_posix())
        spec.loader.exec_module(module)
        sys.path.pop()


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