from lnc.modules.base.network.FTP.config import Config
from lnc.modules.base.network.base.module import Network_Module
from ftplib import FTP, error_perm
from rich.console import Console
from time import sleep

class FTP_Module(Network_Module):
    config: Config = None
    username: str = None
    password: str = None
    domain: str = None
    connection: FTP = None
    
    def __init__(self, config: Config, console: Console, target: str, username: str = None, password: str = None, domain: str = None) -> None:
        super().__init__(config, console, target)
        self.username = username
        self.password = password
        self.domain = domain
        self.connection = None
        self.console = console

    def connect(self, r=0) -> bool:
        if not self.check_access(self.target):
            if r < self.config.retry_count:
                sleep(self.config.delay_before_retry)
                return self.connect(r + 1)
            self.write_error(f"Unable to access port {self.target}:{self.config.port}")
            return False
        try:
            self.connection = FTP()
            self.connection.connect(self.target, self.config.port, timeout=self.config.timeout)
        except Exception as e:
            if r < self.config.retry_count:
                sleep(self.config.delay_before_retry)
                return self.connect(r + 1)
            self.write_error(f"Unable to connect to ftp://{self.target}:{self.config.port}. Error: {str(e)}")
            return False
        try:
            username = self.username or ''
            password = self.password or ''
            if self.domain:
                username = f"{self.domain}\\{username}"
            self.connection.login(username, password)
        except error_perm as e:
            self.write_error(f"Unable to login to ftp://{self.target}:{self.config.port}. Error: {str(e)}")
            return False
        super().connect()
        return True

    def close(self):
        try:
            if self.connection:
                self.connection.quit()
        except:
            pass
        return super().close()
