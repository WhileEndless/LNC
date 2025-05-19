from lnc.modules.crawl.SMB.shares.config import Config
from lnc.modules.base.network.SMB.module import SMB_Module
from lnc.modules.base.module import Module_Type
from rich.console import Console
from threading import Lock
from time import sleep
from json import dumps


PROTOCOL = 'SMB'

class Share:
    name:str = None
    read_access:bool = None
    write_access:bool = None
    def __init__(self) -> None:
        self.name = None
        self.read_access = None
        self.write_access = None
    
    def to_dict(self) -> dict:
        return {
            'name':self.name,
            'read_access':self.read_access,
            'write_access':self.write_access
        }
    
    @classmethod
    def from_dict(cls, share_dict: dict):
        share = cls()
        share.name = share_dict.get('name', None)
        share.read_access = share_dict.get('read_access', None)
        share.write_access = share_dict.get('write_access', None)
        return share

class SMB_Shares(SMB_Module):
    module_run_type = Module_Type.SINGLE
    total:int = 0
    total_lock:Lock = Lock()
    config: Config = None
    
    def __init__(self, config: Config, console:Console, target: str, username: str = None, password: str = None, domain: str = None) -> None:
        super().__init__(config, console, target, username, password, domain)
    
    def list_shares(self,r=0):
        try:
            shares_info = self.connection.listShares()
            for share in shares_info:
                yield share['shi1_netname'][:-1]
        except Exception as e:
            self.write_error(f"Unable to get shares from {PROTOCOL.lower()}://{self.target}:{self.config.port}. Error: {str(e)}")
            self.connect()
            if r<self.config.retry_count:
                sleep(self.config.delay_before_retry)
                yield from self.list_shares(r+1)

    def run(self,r=0):
        try:
            for share in self.list_shares():
                data=Share()
                data.name = share
                if self.config.check_read:
                    self.read_test(data)
                if self.config.check_write:
                    self.write_test(data)
                d= data.to_dict()
                d['target']=self.target
                d['port']=self.config.port
                d['protocol']=PROTOCOL
                text_data=f"{self.target}:{self.config.port} - {data.name}"
                if self.config.check_read:
                    text_data+=f" - Read Access: {data.read_access}"
                if self.config.check_write:
                    text_data+=f" - Write Access: {data.write_access}"
                self.write(text_data=text_data, dict_data=d)
                with SMB_Shares.total_lock:
                    SMB_Shares.total+=1
                yield data
        except Exception as e:
            self.write_error(f"Unable to get shares from {PROTOCOL.lower()}://{self.target}:{self.config.port}. Error: {str(e)}")
            self.connect()
            if r<self.config.retry_count:
                yield from self.run(r+1)

    def read_test(self,share:Share,r=0):
        try:
            self.connection.listPath(share.name, '*')
            share.read_access=True
            return
        except Exception as e:
            if "STATUS_ACCESS_DENIED" in str(e):
                share.read_access=False
                return
            sleep(self.config.delay_before_retry)
            self.connect()
            if r<self.config.retry_count:
                self.read_test(share,r+1)
        share.read_access=False
    
    def write_test(self,share:Share,r=0):
        try:
            self.connection.createDirectory(share.name, 'kljdkghdsjkfhsdkjhfajksh')
            self.connection.deleteDirectory(share.name, 'kljdkghdsjkfhsdkjhfajksh')
            share.write_access=True
            return
        except Exception as e:
            if "STATUS_ACCESS_DENIED" in str(e):
                share.write_access = False
                return
            sleep(self.config.delay_before_retry)
            self.connect()
            if r<self.config.retry_count:
                self.write_test(share,r+1)
        share.write_access = False