import config
from distexprunner import *



server_list = ServerList(
    Server('node01', '127.0.0.1', config.SERVER_PORT, optional_field=True),
)


@reg_exp(servers=server_list)
def environment_variables(servers):
    for s in servers:
        s.run_cmd('env', env={'OMP_NUM_THREADS': 8}).wait()

