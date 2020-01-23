import config
from utils import AttrDict

class Server:
    def __init__(self, id, ip, port=config.SERVER_PORT, **kwargs):
        self.id = id
        self.ip = ip
        self.port = port
        self.data = AttrDict(kwargs)
