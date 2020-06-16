import config
from distexprunner import *


server_list = ServerList(
    Server('node01', '127.0.0.1', config.SERVER_PORT),
)

@reg_exp(servers=server_list, max_restarts=3)
def restart(servers):
    for s in servers:
        cmd = s.run_cmd(f'date && sleep 0.1 && exit 1', stdout=Console(fmt=f'{s.id}: %s'))
        if cmd.wait() != 0:
            return Action.RESTART