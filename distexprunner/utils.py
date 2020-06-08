import asyncio
import sys, tty, termios
import logging



def sleep(delay):
    """sequential sleep without blocking event loop processing"""

    loop = asyncio.get_event_loop()
    async def task():
        await asyncio.sleep(delay)
    loop.run_until_complete(task())


def forward_stdin_to(cmd, esc='\x1b'): # \x02 ESC \x03 Ctrl-C
    """foward console stdin to running command"""

    logging.info(f'Interfacing with command in progress... Press ESC to quit.')

    loop = asyncio.get_event_loop()
    async def task():
        future = loop.create_future()

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setraw(fd)

        def on_stdin():
            c = sys.stdin.read(1)
            # print(repr(c))

            if c == '\r':
                c = '\n'

            cmd.async_stdin(c)

            if c == esc:
                future.set_result(None)

        loop.add_reader(fd, on_stdin)
        await future
        loop.remove_reader(fd)

        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    loop.run_until_complete(task())
    