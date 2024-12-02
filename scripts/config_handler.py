import os
import ctypes
from configparser import ConfigParser
from scripts.common_toolkit import ClsCommonToolkit as CTK


class ClsConfigParser:
    def __init__(self) -> None:
        self.config_file_name = "config.ini"
        self.config = ConfigParser()
        if not os.path.exists(self.config_file_name):
            ctypes.windll.user32.MessageBoxW(
                0,
                u"Config file not found.\nGenerating fresh config.",
                u"VLCync error",
                0
            )
            self.generate_fresh_config()

        self.config.read(self.config_file_name)

    def __enter__(self):
        return self

    @CTK.verify_request
    def get_value(self, section, option):
        return self.config.get(section, option)

    def generate_fresh_config(self):
        self.config.read_dict({
            "default": {
                "hostip": "127.0.0.1",
                "hostport": 42000,
                "newconnectionacceptancetimeout": 1,
            }
        })
        self.save_config()

    def save_config(self):
        if self.config.has_section("user-gen"):
            for option in self.config.options("user-gen"):
                if not self.config.has_option("default", option):
                    continue

                if (
                    not self.config["default"][option] ==
                    self.config["user-gen"][option]
                ):
                    continue

                self.config.remove_option("user-gen", option)

        with open(self.config_file_name, "w") as f:
            self.config.write(f)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.save_config()
