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
    def __init__(self):
        self.experiments = []

    def run(self):
        for Experiment in self.experiments:
            experiment = Experiment()
            experiment.run()

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
        fn = lambda x: any(fnmatch.fnmatch(x.__name__, f) for f in filters)
        self.experiments = filter(fn, self.experiments)


    def __experiments_from_file(self, file):
        spec = importlib.util.spec_from_file_location(file, file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for _, cls in module.__dict__.items():
            if isinstance(cls, type) and issubclass(cls, experiment.Base):
                logging.info(f'Found experiment: {cls.__name__}')
                yield cls



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Distributed Experiment Runner Client Instance')
    parser.add_argument('--filter', action='append', type=str, help='filter experiments by name')
    parser.add_argument('folder', nargs='?', type=str, default=config.CLIENT_EXPERIMENT_FOLDER, help='experiment folder')
    args = parser.parse_args()

    logging.basicConfig(format='[%(asctime)s]: %(message)s', level=logging.DEBUG)

    client = Client()

    client.add_experiments(args.folder)
    if args.filter:
        client.filter_experiments(args.filter)

    client.run()