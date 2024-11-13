from lnc.modules.base.network.SMB.config import Config
from lnc.modules.base.network.base.module import Network_Module
from impacket.smbconnection import SMBConnection
from rich.console import Console
from time import sleep

class SMB_Module(Network_Module):
    config: Config = None
    username:str=None
    password:str=None
    domain:str=None
    connection:SMBConnection = None
    
    def __init__(self, config: Config, console:Console, target: str, username:str=None,password:str=None,domain:str=None) -> None:
        super().__init__(config, console, target)
        self.username=username
        self.password=password
        self.domain=domain
        self.connection = None
        self.console=console

    def connect(self,r=0) -> bool:
        if not self.check_access(self.target):
            if r<self.config.retry_count:
                sleep(self.config.delay_before_retry)
                return self.connect(r+1)
            self.write_error(f"Unable to access port {self.target}:{self.config.port}")
            return False
        try:
            self.connection = SMBConnection(self.target,self.target,sess_port=self.config.port,timeout=self.config.timeout)
        except Exception as e:
            if r<self.config.retry_count:
                sleep(self.config.delay_before_retry)
                return self.connect(r+1)
            self.write_error(f"Unable to connect to smb://{self.target}:{self.config.port}. Error: {str(e)}")
            return False
        try:
            username = '' if self.username == None else self.username
            password = '' if self.password == None else self.password
            domain = '' if self.domain == None else self.domain
            self.connection.login(username,password,domain)
        except:
            self.write_error(f"Unable to login to smb://{self.target}:{self.config.port}")
            return False
        super().connect()
        return True

    def close(self):
        try:
            self.connection.logoff()
        except:
            pass
        try:
            self.connection.close()
        except:
            pass
        return super().close()