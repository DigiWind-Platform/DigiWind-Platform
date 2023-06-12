import logging
import os
import threading

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.filesystems import AbstractedFS
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer


class FtpServer:
    def __init__(self, ftp_user: str, ftp_password: str, ftp_directory: str, ftp_port: int, ftp_passive_port_range, _logging: int):
        logging.basicConfig(format="%(asctime)s: %(message)s", level=_logging,
                            datefmt="%H:%M:%S")
        self.FTP_DIRECTORY = ftp_directory
        self.authorizer = DummyAuthorizer()
        # Define a new user having full r/w permissions.
        self.authorizer.add_user(ftp_user, ftp_password, self.FTP_DIRECTORY, perm='elradfmw')
        self.handler = FTPHandler
        self.server = ThreadedFTPServer(('0.0.0.0', ftp_port), self.handler)

        self.handler.authorizer = self.authorizer

        # Define a customized banner (string returned when client connects)
        self.handler.banner = "Model Management Service ready."

        # Optionally specify range of ports to use for passive connections.
        self.handler.passive_ports = range(int(ftp_passive_port_range[0]), int(ftp_passive_port_range[1]))

        # list files, https://pyftpdlib.readthedocs.io/en/latest/api.html
        self.fs = AbstractedFS(self.FTP_DIRECTORY, self.handler)

        self.server.max_cons = 32
        self.server.max_cons_per_ip = 20
        logging.info("FTPServer:  : Will listen on: " + str(self.server.address))

    def start(self):
        srv = threading.Thread(target=self.server.serve_forever)
        srv.start()
        logging.info("FTPServer:  : FTP server started")

    def stop(self):
        self.server.close_all()
        logging.info("FTPServer:  : FTP server stopped")

    def get_content_in_root(self):
        return self.fs.listdir(self.FTP_DIRECTORY)

    def get_content_in_folder(self, path):
        return self.fs.listdir(self.FTP_DIRECTORY + os.sep + path)
