import config
from distexprunner import *


server_list = ServerList(
    Server('node01', '127.0.0.1', config.SERVER_PORT),
)



@reg_exp(servers=server_list)
def gdb(servers):
    s = servers[0]

    code = r"""
    #include <stdio.h>
    #include <unistd.h>

    int main(void) {
        int i = 42;
        int *p = NULL;
        *p = i;
        return 0;
    }
    """
    exe = 'unbuffered'

    cmd = s.run_cmd(f'gcc -g -xc - -o {exe}')
    cmd.stdin(code, close=True)
    cmd.wait()

    controller = StdinController()

    output = File('gdb.log', flush=True)
    cmd = s.run_cmd(f'{GDB} ./{exe}', stdout=output, stderr=output, stdin=controller)

    controller.wait()

    cmd.wait()

    s.run_cmd(f'rm -f {exe}').wait()