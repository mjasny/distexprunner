import threading
import logging
import xmlrpc.client
import subprocess
import time
import shlex
import os
import functools

from utils import LinePipe


class LineProxy:
    def __init__(self, id, method, addr):
        self.proxy = xmlrpc.client.ServerProxy(addr)
        self.remote = functools.partial(getattr(self.proxy, method), id)
    
    def __call__(self, line):
        if self.proxy is None:
            return
        try:
            self.remote(line)
        except ConnectionRefusedError:
            self.proxy = None


class ServerProcess(threading.Thread):
    def __init__(self, id, cmd, env, callback_addr):
        super().__init__()
        self.id = id
        self.cmd = cmd
        self.env = env
        self.callback_addr = callback_addr
        self.rc = None
        self.p = None

        self.daemon = False
        self.start()

    
    def run(self):
        logging.info(f'Running cmd: {self.cmd}')
        stdout = LinePipe(callback=LineProxy(self.id, 'cmd_stdout', self.callback_addr)) #TODO change to partial
        stderr = LinePipe(callback=LineProxy(self.id, 'cmd_stderr', self.callback_addr))

        environ = os.environ.copy()
        environ.update({k: str(v) for k, v in self.env.items()})
        self.p = subprocess.Popen(shlex.split(self.cmd), stdout=stdout, stderr=stderr, stdin=subprocess.PIPE, bufsize=1, universal_newlines=True, shell=False, env=environ)

        self.p.wait()
        self.rc = self.p.returncode
        logging.info(f'Cmd {self.id} ({self.cmd}) exited with: {self.p.returncode}')

        try:
            with xmlrpc.client.ServerProxy(self.callback_addr) as proxy:
                proxy.cmd_rc(self.id, self.p.returncode)
        except ConnectionRefusedError:
            pass

        stdout.close()
        stderr.close()

    def stdin(self, line):
        if self.rc:
            raise Exception(f'Process alreading terminated could not send stdin: {line}')

        self.__wait_for_p()
        self.p.stdin.write(line)
        self.p.stdin.flush()


    def kill(self):
        if self.rc:
            return

        self.__wait_for_p()
        self.p.kill()
        self.p.wait()


    def __wait_for_p(self):
        while self.p is None:   # TODO better solution, wait for unstarted process
            time.sleep(0.01)


    def cleanup(self):
        self.kill()
