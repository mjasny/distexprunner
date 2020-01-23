class Printer:
    def __init__(self, fmt='{line}', rstrip=False, end=''):
        self.fmt = fmt
        self.rstrip = rstrip
        self.end = end

    def __call__(self, line):
        if self.rstrip:
            line = line.rstrip()
        print(self.fmt.format(line=line), end=self.end)


class Logfile:
    def __init__(self, filename, append=False):
        mode = 'a' if append else 'w'
        self.file = open(filename, mode)

    def __del__(self):
        self.file.close()

    def __call__(self, line):
        self.file.write(line)