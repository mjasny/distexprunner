import sys
import shutil
import math


class Progress:
    def __init__(self, max_steps, output=sys.stdout, disable_stdout=True):
        self.steps = 0
        self.max_steps = max_steps
        self.current_step = None
        self.output=sys.stdout
        if disable_stdout:
            sys.stdout = open('/dev/null', 'w')
            sys.stderr = open('/dev/null', 'w')
    
    def step(self, name=None):
        if self.current_step is not None:
            CHECK_MARK='\033[0;32m\u2714\033[0m'
            #RED_CROSS='\033[0;31m\u2718\033[0m'
            self.output.write('\033[1A\033[K')  # 1 up, clear line
            self.output.write(f'{self.current_step} {CHECK_MARK}\n')
            self.steps += 1
        if name:
            self.output.write('\033[K')  # clear line
            self.output.write(f'{name} ...\n\033[K\n')
            self.current_step = name
        else:
            self.output.write(f'\n\033[K')

        width, _ = shutil.get_terminal_size((80, 20))

        percent = self.steps/self.max_steps
        steps_width = len(str(self.max_steps))
        prefix = f'Progress: [{self.steps:{steps_width}d}/{self.max_steps} {percent:4.0%}]'

        if len(prefix)+8 > width:
          self.output.write('\033[0;31mWidth too small!\033[0m\n')
          return

        width_left = width - len(prefix) - 3
        hashes = math.floor(width_left*percent)
        dots = (width_left-hashes)
        suffix = f'[{"#"*hashes}{"."*dots}]'

        progress = f'\033[0;42;30m{prefix}\033[0m {suffix}'
        self.output.write(progress)
        if self.steps < self.max_steps:
          self.output.write('\033[1A\r')  #1 up, start
        self.output.flush()

    
    def finish(self):
        self.step()