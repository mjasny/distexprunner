import asyncio
import logging
import os
import sys
import signal
import subprocess
import atexit
import base64
import hashlib
import contextlib

from ._server_interface import ServerInterface
from ._client_interface import ClientInterface
from ._rpc import RPCReader, RPCWriter


class ServerImpl(ServerInterface):
    def __init__(self, reader, writer):
        # RPC wiring
        self.__rpc_reader = RPCReader(reader, writer, self)
        self.rpc = RPCWriter(ClientInterface)(writer)

        self.pings = 0
        self.__procs = {}   # uuid -> asyncio.subprocess.Process
        self.__pgids = {}   # uuid -> recorded process group id (int)
        self.__cwd = None

        # Cache stdbuf's LD_PRELOAD once; if unavailable it's empty
        try:
            self.__stdbuf_so = subprocess.check_output(
                "stdbuf -oL env | awk -F'=' '/^LD_PRELOAD=/ {print $2}'",
                shell=True,
                encoding='utf-8'
            ).strip()
        except subprocess.CalledProcessError:
            self.__stdbuf_so = ""

        atexit.register(self.__at_exit)

    async def _on_disconnect(self):
        # Best-effort: kill any remaining child groups,
        # then remove the at-exit hook so we don't double-run it.
        uuids = list(self.__procs.keys())
        for uuid in uuids:
            try:
                await self.kill_cmd(uuid)
            except Exception:
                logging.exception(
                    f"_on_disconnect: kill_cmd failed for {uuid}")
        with contextlib.suppress(Exception):
            atexit.unregister(self.__at_exit)

    # ---------- helpers ----------

    def __sudo_is_passwordless(self):
        try:
            subprocess.check_output("sudo -n true", shell=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def __record_proc(self, uuid, proc: asyncio.subprocess.Process):
        """Record the process and its group id immediately after spawn."""
        self.__procs[uuid] = proc
        try:
            self.__pgids[uuid] = os.getpgid(proc.pid)
        except ProcessLookupError:
            # Already gone between spawn and record; unlikely but possible
            self.__pgids[uuid] = None

    def __cleanup_proc(self, uuid):
        """Remove bookkeeping for a uuid."""
        self.__procs.pop(uuid, None)
        self.__pgids.pop(uuid, None)

    def __killpg(self, pgid: int, sig: int, allow_sudo: bool = True) -> bool:
        """Signal a process group; optionally fall back to sudo on EPERM."""
        try:
            os.killpg(pgid, sig)
            return True
        except PermissionError:
            if allow_sudo and self.__sudo_is_passwordless():
                try:
                    subprocess.check_output(
                        f"sudo kill -{sig} -{pgid}", shell=True)
                    return True
                except subprocess.CalledProcessError:
                    return False
            return False
        except ProcessLookupError:
            # Group already gone
            return True
        except Exception:
            logging.exception(f"killpg({pgid}, {sig}) failed")
            return False

    def __is_same_group(self, pid: int, expected_pgid: int):
        """
        Return (bool, detail_string) indicating if 'pid' is alive and still
        in 'expected_pgid'. If pid no longer exists, returns (False, 'no-such-pid').
        """
        if expected_pgid is None:
            return False, "no-recorded-pgid"
        try:
            current = os.getpgid(pid)
        except ProcessLookupError:
            return False, "no-such-pid"
        return (current == expected_pgid), f"pgid-now={current},pgid-recorded={expected_pgid}"

    def __at_exit(self):
        # Fast best-effort shutdown; avoid sudo here
        for uuid, proc in list(self.__procs.items()):
            pgid = self.__pgids.get(uuid)
            same, _detail = self.__is_same_group(proc.pid, pgid)
            if same and pgid is not None:
                # TERM then KILL without blocking long
                self.__killpg(pgid, signal.SIGTERM, allow_sudo=False)
                self.__killpg(pgid, signal.SIGKILL, allow_sudo=False)
        logging.info(
            f"At-exit cleanup: attempted to kill {len(self.__procs)} running process(es)")

    # ---------- RPC methods ----------

    async def ping(self, *args, **kwargs):
        self.pings += 1
        await self.rpc.pong(*args, **kwargs)

    async def cd(self, directory):
        self.__cwd = directory

    async def send_file(self, source, target, checksum, mode):
        data = base64.b64decode(source)
        checksum_received = hashlib.md5(data).hexdigest()
        logging.info(
            f"Received file source=... target={target} checksum={checksum} "
            f"checksumReceived={checksum_received} mode={mode}"
        )

        if checksum != checksum_received:
            raise RuntimeError("Checksums of sent file do not match!")

        target_path = os.path.join(
            self.__cwd, target) if self.__cwd else target
        with open(target_path, "wb") as target_file:
            target_file.write(data)
        os.chmod(target_path, mode)

    async def run_cmd(self, uuid, cmd, env={}):
        """
        Spawn a command in its own session (start_new_session=True),
        stream stdout/stderr back to the client, and only return once
        the process has exited and rc has been sent — matching the
        original semantics to avoid hanging the server.
        """
        logging.info(f"uuid={uuid} cmd={cmd}")

        async def _pump(stream, rpc_fn):
            try:
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    text = line.decode("utf-8", errors="replace")
                    sys.stdout.write(text)
                    await rpc_fn(uuid, text)
            except asyncio.CancelledError:
                pass
            except Exception:
                logging.exception(f"_pump failed for {uuid}")

        environ = os.environ.copy()
        environ.update({k: str(v) for k, v in env.items()})
        environ["_STDBUF_O"] = "L"
        if self.__stdbuf_so:
            ld = environ.get("LD_PRELOAD", "")
            environ["LD_PRELOAD"] = f"{ld}:{self.__stdbuf_so}" if ld else self.__stdbuf_so

        cwd = os.path.expanduser(self.__cwd) if self.__cwd else None

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            env=environ,
            cwd=cwd,
            start_new_session=True,  # safer than preexec_fn=os.setsid
        )
        self.__record_proc(uuid, process)

        logging.info(f"Attach gdb: gdb -p {process.pid}")
        await self.rpc.pid(uuid, process.pid)

        # Start pumps
        t_out = asyncio.create_task(_pump(process.stdout, self.rpc.stdout))
        t_err = asyncio.create_task(_pump(process.stderr, self.rpc.stderr))

        try:
            rc = await process.wait()
            logging.info(f"Got rc={rc} for: {repr(cmd)}")
            await self.rpc.rc(uuid, rc)
        finally:
            # Ensure pumps finish and cleanup maps
            for t in (t_out, t_err):
                if not t.done():
                    t.cancel()
                    with contextlib.suppress(Exception):
                        await t
            self.__cleanup_proc(uuid)

    async def __process_startup(self, uuid, timeout=1.0):
        # wait up to 'timeout' seconds for the process to appear
        attempts = max(1, int(timeout / 0.05))
        for _ in range(attempts):
            if uuid in self.__procs:
                return True
            await asyncio.sleep(0.05)
        logging.error(f"{uuid} did never startup")
        return False

    async def kill_cmd(self, uuid):
        if not await self.__process_startup(uuid):
            return
        proc = self.__procs.get(uuid)
        if not proc:
            return
        pgid = self.__pgids.get(uuid)

        same, detail = self.__is_same_group(proc.pid, pgid)
        if not same:
            # If process already gone or group changed, nothing to kill here
            logging.warning(f"[{uuid}] not killing: {detail}")
            return

        # TERM, wait briefly, then KILL
        self.__killpg(pgid, signal.SIGTERM, allow_sudo=True)
        try:
            await asyncio.wait_for(proc.wait(), timeout=1.0)
            return
        except asyncio.TimeoutError:
            pass
        self.__killpg(pgid, signal.SIGKILL, allow_sudo=True)

    async def stdin_cmd(self, uuid, line, close=False):
        if not await self.__process_startup(uuid):
            return
        p = self.__procs.get(uuid)
        if not p:
            return

        if p.stdin.is_closing():
            logging.error(f"{uuid} has stdin closed")
            return

        sys.stdout.write(line)
        sys.stdout.flush()

        p.stdin.write(line.encode())
        if close:
            with contextlib.suppress(Exception):
                p.stdin.write_eof()

        try:
            await p.stdin.drain()
        except (ConnectionResetError, BrokenPipeError):
            logging.error("stdin drain failed")

    async def signal_cmd(self, uuid, sig):
        if not await self.__process_startup(uuid):
            return
        proc = self.__procs.get(uuid)
        if not proc:
            return
        pgid = self.__pgids.get(uuid)

        same, detail = self.__is_same_group(proc.pid, pgid)
        if not same:
            logging.warning(f"[{uuid}] not signaling: {detail}")
            return

        self.__killpg(pgid, sig, allow_sudo=True)
        logging.info(f"uuid={uuid} sent signal: {sig}")
