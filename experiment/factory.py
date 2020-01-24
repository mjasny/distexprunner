import itertools
import logging
import experiment


generated_experiments = []


class Grid:
    def __init__(self, factory_fn, *args):
        for params in itertools.product(*args):
            cls = factory_fn(*params)

            if not issubclass(cls, experiment.Base):
                raise Exception('Factory needs to return a child of experiment.Base')

            suffix = '_'.join(map(str, params))
            cls.__name__ += f'_{suffix}'
            logging.info(f'Generated experiment: {cls.__name__}')
            generated_experiments.append(cls)



class Generator:
    def __init__(self, factory_fn, generator):
        for params in generator:
            cls = factory_fn(*params)

            if not issubclass(cls, experiment.Base):
                raise Exception('Factory needs to return a child of experiment.Base')

            suffix = '_'.join(map(str, params))
            cls.__name__ += f'_{suffix}'
            logging.info(f'Generated experiment: {cls.__name__}')
            generated_experiments.append(cls)