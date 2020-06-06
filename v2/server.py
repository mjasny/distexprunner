import argparse
import logging

from distexprunner import ExperimentServer



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Distributed Experiment Runner Server')
    parser.add_argument('-v', '--verbose', action="count", default=0, help='-v WARN -vv INFO -vvv DEBUG')
    parser.add_argument('-ip', '--ip', default='0.0.0.0', help='Listening ip')
    parser.add_argument('-p', '--port', default=20000, help='Listening port')
    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=max(4 - args.verbose, 0) * 10
    )
    logging.basicConfig(level=logging.DEBUG)

    server = ExperimentServer(ip=args.ip, port=args.port)
    server.start()