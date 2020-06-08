import sys


class Console:
    def __init__(self, fmt='%s', rstrip=False, end=''):
        self.fmt = fmt + end
        self.rstrip = rstrip

    def __call__(self, line):
        if self.rstrip:
            line = line.rstrip()
        sys.stdout.write(self.fmt % line)


class File:
    def __init__(self, filename, append=False):
        mode = 'a' if append else 'w'
        self.file = open(filename, mode)

    def __del__(self):
        self.file.close()

    def __call__(self, line):
        self.file.write(line)