import config
from distexprunner import *




@exp_reg(servers=ServerList())
def only_local(servers):
    File('simple_grid.log', append=False)('empty\n')



server_list = ServerList(
    Server('node01', '127.0.0.1', config.SERVER_PORT),
)
parameter_grid = ParameterGrid(
    a=range(1, 5),
    b=[2, 4],
    to_file=[True, False]
)

@exp_reg(servers=server_list, params=parameter_grid)
def simple_grid(servers, a, b, to_file):
    for s in servers:
        stdout = File('simple_grid.log', append=True)
        if not to_file:
            stdout = [stdout, Console(fmt=f'{s.id}: %s')]

        s.run_cmd(f'echo {a} {b}', stdout=stdout).wait()



'''
TODO
- restart
- resume
- slack notification
- documentation
'''