#!/usr/bin/env python3

import os
import sys
import argparse
import importlib.util
import logging
import fnmatch
import re

import config
import experiment


class Client:
    def __init__(self, resume):
        self.experiments = []
        self.resume = resume

    def run(self):
        self.__prep_resume()

        logging.warning(f'Total experiments to run: {len(self.experiments)}')
        for i, Experiment in enumerate(self.experiments):
            logging.warning(f'Running experiment: {i+1}/{len(self.experiments)} ({(i+1)/len(self.experiments):.0%})')

            experiment = Experiment()
            experiment.run()

            with open(config.CLIENT_RESUME_FILE, 'a+') as f:
                f.write(f'{Experiment.__name__}\n')

        if os.path.exists(config.CLIENT_RESUME_FILE):
            os.remove(config.CLIENT_RESUME_FILE)

    def add_experiments(self, folder):
        if not os.path.exists(folder):
            logging.error(f'Could not find any experiments in: "{folder}"')

        for root, _, files in os.walk(folder):
            for file in files:
                if not file.endswith('.py'):
                    continue

                logging.info(f'Reading file: {os.path.join(root, file)}')
                experiments = self.__experiments_from_file(os.path.join(root, file))
                self.experiments.extend(experiments)

        self.experiments.extend(experiment.factory.generated_experiments)

        def atof(text):
            try:
                return float(text)
            except ValueError:
                return text

        def natural_keys(text):
            return [atof(c) for c in re.split(r'[+-]?([0-9]+(?:[.][0-9]*)?|[.][0-9]+)', text)]

        self.experiments.sort(key=lambda x: natural_keys(x.__name__))


    def filter_experiments(self, filters):
        fn = lambda x: any(fnmatch.fnmatch(x.__name__, f) for f in filters) or x.RUN_ALWAYS
        self.experiments = list(filter(fn, self.experiments))


    def __experiments_from_file(self, file):
        spec = importlib.util.spec_from_file_location(file, file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for _, cls in module.__dict__.items():
            if isinstance(cls, type) and issubclass(cls, experiment.Base):
                logging.info(f'Found experiment: {cls.__name__}')
                yield cls


    def __prep_resume(self):
        if not self.resume:
            return

        def read_resume_file():
            if not os.path.exists(config.CLIENT_RESUME_FILE):
                return []
            with open(config.CLIENT_RESUME_FILE, 'r') as f:
                return [line for line in f.read().splitlines() if len(line) > 0]
        
        run_exps = read_resume_file()
        if len(run_exps) == 0:
            return

        fn = lambda x: x.__name__ not in run_exps or x.RUN_ALWAYS
        self.experiments = list(filter(fn, self.experiments))
        logging.warning(f'Removed already run experiments: {", ".join(run_exps)}')
            
        



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Distributed Experiment Runner Client Instance')
    parser.add_argument('--filter', action='append', type=str, help='filter experiments by name')
    parser.add_argument('--resume', action='store_true', help='Resume execution of experiments from last failure')
    parser.add_argument('folder', nargs='?', type=str, default=config.CLIENT_EXPERIMENT_FOLDER, help='experiment folder')
    args = parser.parse_args()

    logging.basicConfig(format='[%(asctime)s]: %(message)s', level=logging.DEBUG)

    client = Client(args.resume)

    client.add_experiments(args.folder)
    if args.filter:
        client.filter_experiments(args.filter)

    client.run()