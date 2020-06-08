#!/usr/bin/env python3

import argparse
import logging

from distexprunner.experiment_server import ExperimentServer


__author__ = 'mjasny'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Distributed Experiment Runner Server')
    parser.add_argument('-v', '--verbose', action="count", default=0, help='-v WARN -vv INFO -vvv DEBUG')
    parser.add_argument('-ip', '--ip', default='0.0.0.0', help='Listening ip')
    parser.add_argument('-p', '--port', default=20000, help='Listening port')
    parser.add_argument('-rf', '--run-forever', default=False, action='store_true', help='Disable auto termination of server')
    parser.add_argument('-mi', '--max-idle', default=3600, type=int, help='Maximum idle time before auto termination (in seconds). Default 1 hour.')
    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=max(4 - args.verbose, 0) * 10
    )


    server = ExperimentServer(
        ip=args.ip,
        port=args.port,
        max_idle=0 if args.run_forever else args.max_idle
    )
    server.start()