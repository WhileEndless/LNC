from lnc.modules.crawl.SMB.files.config import Config
from lnc.modules.base.network.SMB.module import SMB_Module
from lnc.modules.crawl.SMB.shares.module import Share
from lnc.modules.base.module import Module_Type
from lnc.modules.base.file import File as FileBase
from rich.console import Console
from threading import Lock
from time import sleep

PROTOCOL = 'SMB'

class File(FileBase):
    share:Share = None
    def __init__(self) -> None:
        super().__init__()
        self.share = None
    
    def to_dict(self) -> dict:
        orjdict = super().to_dict()
        orjdict['share'] = self.share.to_dict()
        return orjdict
    
    @classmethod
    def from_dict(cls, file_dict:dict):
        file = super().from_dict(file_dict)
        file.share = Share.from_dict(file_dict.get('share'))
        return file

class SMB_Files(SMB_Module):
    module_run_type = Module_Type.MULTI
    total:int = 0
    total_lock:Lock = Lock()
    config: Config = None
    def __init__(self, config: Config, console:Console, target: str, username: str = None, password: str = None, domain: str = None) -> None:
        super().__init__(config, console, target, username, password, domain)
    def run(self, share:Share, folder:str=''):
        if share.name.lower() in self.config.ignore_shares:
            self.console.print(f'[yellow][*] Ignoring share {PROTOCOL.lower()}://{self.target}/{share.name}[/yellow]')
            return
        
        for file in self.list_path(share, folder):
            filename:str = file.get_longname()
            if not file.is_directory() and file.get_filesize() > 0:
                data = File()
                data.target = self.target
                data.port = self.config.port
                data.protocol = PROTOCOL
                data.url = f'{PROTOCOL.lower()}://{self.target}/{share.name}{folder}/{filename}'
                data.size = file.get_filesize()
                data.share = share
                data.path = f'{folder}/{filename}'
                self.write(text_data=data.url,dict_data=data.to_dict())
                with SMB_Files.total_lock:
                    SMB_Files.total+=1
                yield data 

            elif file.is_directory() and filename not in ['.', '..'] and not any(regex.search(filename.lower()) for regex in self.config.ignore_folder_name_contains):
                yield from self.run(share, f"{folder}/{filename}")

            else:
                if filename not in ['.', '..']:
                    if file.get_filesize() == 0:
                        self.console.print(f'[yellow][*] Ignoring empty file {PROTOCOL.lower()}://{self.target}/{share.name}{folder}/{filename}[/yellow]')

                    else:    
                        self.console.print(f'[yellow][*] Ignoring {PROTOCOL.lower()}://{self.target}/{share.name}/{folder}{filename}[/yellow]')

    def list_path(self, share:Share, folder:str, r=0):
        try:
            for file in self.connection.listPath(share.name, folder + '/*'):
                yield file
        except Exception as e:
            if r < self.config.retry_count:
                sleep(self.config.delay_before_retry)
                self.connect()
                yield from self.list_path(share, folder, r+1)
            else:
                self.write_error(f'Unable to get files from {PROTOCOL.lower()}://{self.target}/{share.name}{folder}. Error: {str(e)}')
                self.close()