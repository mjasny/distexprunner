#!/usr/bin/env python3

import argparse
import logging

from distexprunner.experiment_client import ExperimentClient


__author__ = 'mjasny'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Distributed Experiment Runner Client Instance')
    parser.add_argument('-v', '--verbose', action="count", default=0, help='-v WARN -vv INFO -vvv DEBUG')
    # parser.add_argument('--resume', action='store_true', help='Resume execution of experiments from last run')
    parser.add_argument('--compatibility-mode', action='store_true', default=False, help='Activate compatibiliy mode for class x(experiment.Base)')
    parser.add_argument('experiment', nargs='+', type=str, help='path to experiments, folders are searched recursively, order is important')
    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=max(4 - args.verbose, 0) * 10
    )

    client = ExperimentClient(args.experiment, args.compatibility_mode)
    client.start()
