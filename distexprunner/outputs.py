import logging
import asyncio
import os
import re


LOG_LEVEL_CMD = 100
logging.addLevelName(LOG_LEVEL_CMD, 'CONSOLE')


class Console:
    def __init__(self, fmt='%s'):
        self.fmt = fmt

    def __call__(self, line):
        logging.log(LOG_LEVEL_CMD, self.fmt % line.rstrip())


class File:
    def __init__(self, filename, append=False, flush=False):
        mode = 'a' if append else 'w'
        self.file = open(filename, mode)
        self.flush = flush

    def __del__(self):
        self.file.close()

    def __call__(self, line):
        self.file.write(line)
        if self.flush:
            self.file.flush()


class SubstrMatcher:
    def __init__(self, substr):
        self.substr = substr
        self.reset()

    def __call__(self, line):
        if self.__future.done():
            return  # TODO maybe make resetable
        if self.substr in line:
            self.__future.set_result(None)

    def wait(self):
        self.__loop.run_until_complete(self.__future)
        return True

    def reset(self):
        self.__loop = asyncio.get_event_loop()
        self.__future = self.__loop.create_future()


class EnvParser:
    def __call__(self, line):
        name, value = line.split('=', 1)
        self.__dict__[name] = value.rstrip()

    def __getitem__(self, key):
        return self.__dict__[key]



class CSVGenerator:
    """
    Generates CSV files from stdout/stderr.
    Takes a list of regexes with named groups, outputs csv to file or .header/.row.
    Use in conjuction with IterClassGen:
    
    csvs = IterClassGen(CSVGenerator, [
        r'total_table_agents=(?P<total_table_agents>\d+)',
    ])
    s.run_cmd('bin', stdout=next(csvs)).wait()
    for csv in csvs:
        csv.write('file.csv')
    """
    class Array:
        def __init__(self, regex):
            self.regex = regex


    def __init__(self, regexs):
        self.__header = []
        self.__compiled_regexs = []
        self.__row = {}
        self.__is_array = set()

        for regex in regexs:
            is_array = isinstance(regex, self.Array)
            if is_array:
                regex = regex.regex
            regex = re.compile(regex)
            for key in regex.groupindex.keys():
                if key in self.__header:
                    raise Exception(f'{key} already in header set {self.__header}')
                self.__header.append(key)

                if is_array:
                    self.__is_array.add(key)
            self.__compiled_regexs.append(regex)

    def __call__(self, line):
        for regex in self.__compiled_regexs:
            match = regex.search(line)
            if not match:
                continue
            for k, v in match.groupdict().items():
                if k in self.__is_array:
                    if k not in self.__row:
                        self.__row [k] = []
                    self.__row[k].append(v)
                else:    
                    self.__row[k] = v


    @property
    def header(self):
        return ','.join(self.__header)

    @property
    def row(self):
        values = [self.__row.get(col) for col in self.__header]
        values = [value for value in values if value is not None]
        if len(values) != len(self.__header):
            raise Exception(f'Not enough values for row:\n{set(self.__header)-set(self.__row.keys())}')
        return ','.join(map(lambda v: "|".join(v) if isinstance(v, list) else v, values))


    def write(self, file):
        write_header = not os.path.exists(file)
        with open(file, 'a+') as f:
            if write_header:
                f.write(f'{self.header}\n')
            f.write(f'{self.row}\n')