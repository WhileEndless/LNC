from lnc.modules.base.network.SMB.config import Config
from lnc.modules.base.network.base.module import Network_Module
from impacket.smbconnection import SMBConnection
from rich.console import Console
from time import sleep
from lnc.multi.accessibility_manager import AccessibilityManager

class SMB_Module(Network_Module):
    config: Config = None
    username:str=None
    password:str=None
    domain:str=None
    lmhash:str=None
    nthash:str=None
    connection:SMBConnection = None
    
    def __init__(self, config: Config, console:Console, target: str, username:str=None,password:str=None,domain:str=None,lmhash:str=None,nthash:str=None) -> None:
        super().__init__(config, console, target)
        self.username=username
        self.password=password
        self.domain=domain
        self.lmhash=lmhash
        self.nthash=nthash
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
            lmhash = '' if self.lmhash == None else self.lmhash
            nthash = '' if self.nthash == None else self.nthash
            
            # Use hash authentication if hashes are provided
            if lmhash or nthash:
                self.connection.login(username, '', domain, lmhash, nthash)
            else:
                self.connection.login(username, password, domain)
        except Exception as e:
            auth_method = "hash" if (self.lmhash or self.nthash) else "password"
            self.write_error(f"Unable to login to smb://{self.target}:{self.config.port} using {auth_method} authentication. Error: {str(e)}")
            return False
        super().connect()
        
        # Record successful connection for accessibility checking
        checker = AccessibilityManager.get_instance()
        if checker:
            checker.record_success(
                self.target, 
                self.config.port, 
                'smb',
                username=self.username,
                password=self.password,
                domain=self.domain,
                lmhash=self.lmhash,
                nthash=self.nthash
            )
        
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