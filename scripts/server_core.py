from scripts.logger import VLCync_Logger
from time import sleep


class ClsServerCore:
    def __init__(self, config, connection_handler):
        self.config = config
        self.connection_handler = connection_handler
        self.logger = VLCync_Logger.get_logger("Server")
        self.resume_point = 0
        self.global_playback = False
        self.pause_times = {}
        self.file_hashes = {}
        self.votes = {}

    def run(self):
        self.connection_handler.host()

        while not self.connection_handler.exit:
            try:
                self.connection_handler.connect(
                    self.process_connection,
                    self.process_stream,
                    self.process_disconnection
                )

            except KeyboardInterrupt:
                self.connection_handler.exit = True

    def process_connection(self, name):
        self.votes[name] = 0

    def process_disconnection(self, name):
        if name in self.votes.keys():
            self.votes.pop(name)

        if name in self.file_hashes.keys():
            self.file_hashes.pop(name)
            self.connection_handler.broadcast(
                "SERVER", "HASH BOOL RESET", False
            )
            self.global_playback = False

    def process_stream(self, stream):
        name, msg, for_vlc = stream
        self.logger.debug(f"Received => {name}, {msg}, {for_vlc}")
        if for_vlc:
            self.connection_handler.broadcast_all_but_one(name, msg, for_vlc)

        else:
            if "SELECTED FILE HASH" in msg:
                self.hash_comparator(name, msg)

            elif "VOTE" in msg or "UNVOTE" in msg:
                self.register_vote(name, msg)

            elif "CURRTIME" in msg:
                self.compute_resume_point(name, msg)

    def hash_comparator(self, name, msg):
        msg = msg.split("=")[1]
        self.file_hashes[name] = msg

        self.connection_handler.broadcast(
            "SERVER",
            (
                f"{name} has selected a file to play "
                f"({len(self.file_hashes.keys())}/"
                f"{self.connection_handler.participants})"
            ),
            False
        )

        if len(self.file_hashes) == self.connection_handler.participants:
            self.file_hashes
            if len(list(set(self.file_hashes.values()))) == 1:
                self.connection_handler.broadcast(
                    "SERVER", "HASHES MATCH", False
                )
                return

            # elif len(list(set(self.file_hashes.values())))!=1:
            self.connection_handler.broadcast(
                "SERVER", "HASHES DO NOT MATCH", False
            )

    def register_vote(self, name, msg):
        if msg == "VOTE":
            self.connection_handler.broadcast(
                "SERVER", f"{name} has voted to start", False
            )
            self.votes[name] = 1

        elif msg == "UNVOTE":
            self.connection_handler.broadcast(
                "SERVER", f"{name} has withdrawn their vote", False
            )
            self.votes[name] = 0

        if sum(self.votes.values()) == self.connection_handler.participants:
            self.connection_handler.broadcast(
                "SERVER", "EVERYONE HAS VOTED", False
            )
            self.global_playback = True
            if self.resume_point > 0:
                sleep(1)
                self.connection_handler.broadcast(
                    "SERVER", f"seek {self.resume_point}", True
                )

    def compute_resume_point(self, name, msg):
        self.pause_times[name] = int(msg.split()[-1])

        if len(self.pause_times) == self.connection_handler.participants:
            self.resume_point = sorted(self.pause_times.values())[0] - 1
