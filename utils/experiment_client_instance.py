class ExperimentClientInstance:
    def __init__(self):
        self.__handlers = {}

    def _add_handler(self, cmd_id, handler):
        assert(cmd_id not in self.__handlers)
        self.__handlers[cmd_id] = handler

    def _clear_handlers(self):
        self.__handlers.clear()

    def _dispatch(self, method, params):
        cmd_id = params[0]
        params = params[1:]
        if cmd_id not in self.__handlers:
            return
        handler = self.__handlers[cmd_id]
        return getattr(handler, f'_{method}')(*params)