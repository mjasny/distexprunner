import config
from distexprunner import *


server_list = ServerList(
    Server('node01', '127.0.0.1', config.SERVER_PORT),
)


@reg_exp(servers=server_list)
def buffered_stdout(servers):
    s = servers[0]

    code = r"""
    #include <stdio.h>
    #include <unistd.h>

    int main(void) {
        for (int i = 0; i < 10; i++) {
            printf("%d\n", i);
            usleep(1000000);
        }
    }
    """
    exe = 'unbuffered'

    cmd = s.run_cmd(f'gcc -xc - -o {exe}')
    cmd.stdin(code, close=True)
    cmd.wait()

    s.run_cmd(f'./{exe}', stdout=Console()).wait()
    s.run_cmd(f'rm -f {exe}').wait()