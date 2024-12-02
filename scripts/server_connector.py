import select
import socket
import errno
import secrets
from random import randrange
from scripts.logger import VLCync_Logger
from scripts.com_packet import CommPacket
from scripts.encryption import ClsEncryptTool


class ClsServerConnector:
    def __init__(self, config):
        self.config = config
        self.logger = VLCync_Logger.get_logger("Server")
        self.exit = False
        self.serv_addr = self.config.get_value('default', 'hostip')
        self.serv_port = int(self.config.get_value('default', 'hostport'))
        self.participants = 0
        self.NCAT = float(
            self.config.get_value('default', 'newConnectionAcceptanceTimeout')
        )
        self.sock_list = []
        self.header_size = randrange(30, 50)
        self.key = secrets.token_urlsafe(10)
        self.codec = ClsEncryptTool(self.key)
        self.logger.debug(f"{self.codec.key=}")

    def __enter__(self):
        return self

    def host(self):
        try:
            self.serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.serv_sock.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1
            )
            self.serv_sock.bind((self.serv_addr, self.serv_port))
            self.serv_sock.listen(self.participants)
            self.serv_sock.setblocking(False)
            self.sock_list.append(self.serv_sock)
            self.logger.info(
                f"Server started at {self.serv_addr}:{self.serv_port} "
                f"with password {self.key}"
            )
            self.logger.info("Awaiting Connections")
            self.clients = {}

        except Exception as e:
            self.logger.error(str(e))
            self.exit = True

    def connect(
            self,
            connectionProcessor: callable,
            streamProcessor: callable,
            disconnectionProcessor: callable
    ):
        self.participants = len(self.clients)
        read_sockets, _, exception_sockets = select.select(
            self.sock_list, [], self.sock_list, 0.2
        )
        for notified_socket in read_sockets:
            if notified_socket == self.serv_sock:
                # self.logger.info(f"Socket notified {notified_socket}")
                cli, addr = self.serv_sock.accept()
                self.logger.info(f"Accepted connection from {addr}")
                cli.send(
                    CommPacket.to_stream(
                        None,
                        self.codec,
                        (
                            "SERVER",
                            f"HEADER_SIZE={self.header_size:<64}", False
                        ),
                        init=True
                    )
                )
                self.logger.info("Awaiting client username")
                while True:
                    user = self.receive(cli)
                    if user is True:
                        continue

                    if user is False:
                        continue

                    break

                name, _, _ = user

                if self.usn_conflict(name):
                    cli.send(
                        CommPacket.to_stream(
                            self,
                            self.codec,
                            (
                                "SERVER",
                                f"Username \"{name}\" is already in use",
                                False
                            )
                        )
                    )
                    break

                cli.send(
                    CommPacket.to_stream(
                        self,
                        self.codec,
                        ("SERVER", f"Welcome to the server, {name}", False)
                    )
                )
                self.logger.info(f"{name}({addr}) has joined the server.")
                self.clients[cli] = (name, addr)
                self.sock_list.append(cli)
                self.broadcast(
                    "SERVER", f"{name} has joined the server.", False
                )
                connectionProcessor(name)

            elif notified_socket in self.clients.keys():
                stream = self.receive(notified_socket)
                if stream is True:
                    continue

                if stream is False:
                    name, addr = self.clients[notified_socket]
                    self.sock_list.remove(notified_socket)
                    disconnectionProcessor(self.clients[notified_socket][0])
                    del self.clients[notified_socket]
                    self.logger.info(f"{name}({addr}) has left the server.")
                    self.broadcast(
                        "SERVER", f"{name} has left the server.", False
                    )
                    self.broadcast("SERVER", "toggle_play", True)
                    continue

                streamProcessor(stream)

        for notified_socket in exception_sockets:
            self.sock_list.remove(notified_socket)
            del self.clients[notified_socket]

    def broadcast(self, name, msg, for_vlc):
        for sock in self.clients.keys():
            sock.send(
                CommPacket.to_stream(self, self.codec, (name, msg, for_vlc))
            )

        self.logger.debug(
            f"Broadcast ({name}, {msg}, {for_vlc}) "
            f"sent to {self.clients.values()}"
        )

    def broadcast_all_but_one(self, name, msg, for_vlc):
        for sock in self.clients.keys():
            # self.logger.debug(f"{self.clients[sock][0] = }, {name = }")
            if self.clients[sock][0] == name:
                # self.logger.debug("Inside condition")
                continue

            # self.logger.debug("Outside below condition")
            sock.send(
                CommPacket.to_stream(self, self.codec, (name, msg, for_vlc))
            )

        self.logger.debug(
            f"broadcast_all_but_one ({name}, {msg}, {for_vlc}) sent to "
            f"{[val for val in self.clients.values() if val[0] != name]}"
        )

    def receive(self, cli_sock):
        try:
            msg_len = cli_sock.recv(self.header_size)
            if not len(msg_len):
                return False

            stream = cli_sock.recv(int(msg_len.decode('utf-8').strip()))
            return CommPacket.from_stream(stream, self.codec)

        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                self.logger.error(f"Reading error: {str(e)}")
                raise e
            return True

    def usn_conflict(self, usn):
        if usn in [cli[0] for cli in self.clients.values()]:
            return True

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.serv_sock.close()
        self.logger.info("Socket closed.")
