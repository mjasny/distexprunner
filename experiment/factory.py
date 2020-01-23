import itertools
import logging
import experiment


generated_experiments = []


class Grid:
    def __init__(self, factory_fn, *args):
        for params in itertools.product(*args):
            suffix = '_'.join(map(str, params))
            cls = factory_fn(*params)

            if not issubclass(cls, experiment.Base):
                raise Exception('Factory needs to return a child of experiment.Base')

            cls.__name__ += f'_{suffix}'
            logging.info(f'Generated experiment: {cls.__name__}')
            generated_experiments.append(cls)



class Generator:
    pass