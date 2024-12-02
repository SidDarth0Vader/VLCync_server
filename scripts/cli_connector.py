import socket
# import time
import pickle

from scripts.logger import VLCync_Logger

HEADER_SIZE = 10


class ClsCliConnector:
    def __init__(self, config):
        self.logger = VLCync_Logger.get_logger('Server')
        self.cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_connected = False
        self.def_host = config.cfg["default"]["serverip"]
        self.def_port = config.cfg["default"]["serverport"]

    def __enter__(self):
        return self

    def connect(self, host, port, pack):
        try:
            self.cli_sock.connect((host, int(port)))
            self.cli_sock.send(pickle.dumps(pack))
            self.is_connected = True
        except ConnectionRefusedError:
            self.logger.info(
                f"Server(addr: {host}) refused connection at port {port}"
            )

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.cli_sock.close()
        self.logger.info("Socket closed")
