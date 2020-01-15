import os
import threading


class LinePipe(threading.Thread):
    def __init__(self, callback):
        super().__init__()
        self.daemon = False
        self.callback = callback
        self.fdRead, self.fdWrite = os.pipe()
        self.pipeReader = os.fdopen(self.fdRead)
        self.start()

    def fileno(self):
        return self.fdWrite

    def run(self):
        for line in iter(self.pipeReader.readline, ''):
            self.callback(line)
        self.pipeReader.close()

    def close(self):
        os.close(self.fdWrite)