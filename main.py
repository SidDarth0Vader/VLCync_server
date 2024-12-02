from scripts.server_core import ClsServerCore
from scripts.config_handler import ClsConfigParser
from scripts.server_connector import ClsServerConnector


def main():
    with ClsConfigParser() as config:
        with ClsServerConnector(config) as connection_handler:
            server = ClsServerCore(config, connection_handler)
            server.run()


if __name__ == '__main__':
    main()
