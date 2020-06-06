import sys

class Output:
    pass


class Console(Output):
    def __init__(self, fmt='%s', rstrip=False, end=''):
        self.__fmt = fmt + end
        self.__rstrip = rstrip
        self.__end = end

    def __call__(self, line):
        if self.__rstrip:
            line = line.rstrip()
        sys.stdout.write(self.__fmt % line)


class File(Output):
    def __init__(self, filename, append=False):
        mode = 'a' if append else 'w'
        self.file = open(filename, mode)

    def __del__(self):
        self.file.close()

    def __call__(self, line):
        self.file.write(line)