import shutil
import time
import paramiko
from . import channel


class ParamikoChannel(channel.Channel):

    def __init__(self, ch: paramiko.Channel) -> None:
        self.ch = ch

        self.ch.get_pty("xterm-256color", 80, 25, 1024, 1024)
        self.ch.invoke_shell()

        super().__init__()

    def send(self, data: str) -> None:
        if data == "":
            return

        data_bytes = data.encode("utf-8")
        length = len(data_bytes)
        c = 0
        while c < length:
            b = self.ch.send(data_bytes[c:])
            if b == 0:
                raise channel.ChannelClosedException()
            c += b

    def recv(self) -> str:
        # Wait until at least one byte is available
        while not self.ch.recv_ready():
            time.sleep(0.1)

        buf = b""
        while self.ch.recv_ready():
            buf += self.ch.recv(1000)

        if buf == b"":
            raise channel.ChannelClosedException()

        s: str
        try:
            s = buf.decode("utf-8")
        except UnicodeDecodeError as e:
            if e.start > len(buf) - 4:
                # The failure occured at the end of the string, most likely because
                # only half of a unicode char was written
                for _ in range(6):
                    time.sleep(0.05)
                    buf += self.ch.recv(1)
                    try:
                        s = buf.decode("utf-8")
                        break
                    except UnicodeDecodeError:
                        pass
            else:
                # Fall back to latin-1 if unicode decoding fails ... This is not perfect
                # but it does not stop a test run just because of an invalid character
                s = buf.decode("latin_1")

        return s

    def close(self) -> None:
        self.ch.close()

    def fileno(self) -> int:
        return self.ch.fileno()

    def _interactive_setup(self) -> None:
        size = shutil.get_terminal_size()
        self.ch.resize_pty(size.columns, size.lines, 1024, 1024)
        self.ch.settimeout(0.0)

    def _interactive_teardown(self) -> None:
        self.ch.settimeout(None)
