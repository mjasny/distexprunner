import logging
import pathlib


class ResumeManager:
    def __init__(self):
        self.path = pathlib.Path('.distexprunner')
        self.already_run = set()
        if self.path.exists():
            with self.path.open('r') as f:
                self.already_run = set(l for l in f.read().splitlines() if len(l) > 0)
        



    def was_run(self, name):
        return name in self.already_run
        # try:
        #     self.already_run.remove(name)
        #     return True
        # except KeyError:
        #     return False


    def add_run(self, name):
        with self.path.open('a+') as f:
            f.write(f'{name}\n')

    
    def reset(self):
        self.already_run = set()
        if self.path.exists():
            self.path.unlink()
