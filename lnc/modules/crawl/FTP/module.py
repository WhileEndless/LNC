from lnc.modules.crawl.FTP.config import Config
from lnc.modules.base.network.FTP.module import FTP_Module
from lnc.modules.base.module import Module_Type
from lnc.modules.base.file import File as FileBase
from rich.console import Console
from threading import Lock
from time import sleep
from os.path import basename
PROTOCOL = 'FTP'

class File(FileBase):
    def __init__(self) -> None:
        super().__init__()
    
    def to_dict(self) -> dict:
        return super().to_dict()
    
    @classmethod
    def from_dict(cls, file_dict: dict):
        return super().from_dict(file_dict)

class FTP_Files(FTP_Module):
    module_run_type = Module_Type.MULTI
    total: int = 0
    total_lock: Lock = Lock()
    config: Config = None
    
    def __init__(self, config: Config, console: Console, target: str, username: str = None, password: str = None, domain: str = None) -> None:
        super().__init__(config, console, target, username, password, domain)

    def run(self, folder: str = '/'):
        for file in self.list_path(folder):
            filename: str = file
            if self.is_file(file) and self.get_filesize(file) > 0:
                data = File()
                data.target = self.target
                data.port = self.config.port
                data.protocol = PROTOCOL
                data.url = f'{PROTOCOL.lower()}://{self.target}{filename}'
                data.size = self.get_filesize(file)
                data.path = f"{folder}{basename(filename)}"
                self.write(text_data=data.url, dict_data=data.to_dict())
                with FTP_Files.total_lock:
                    FTP_Files.total += 1
                yield data
            elif self.is_directory(file) and filename not in ['.', '..'] and not any(regex.search(basename(filename).lower()) for regex in self.config.ignore_folder_name_contains):
                yield from self.run(f"{folder}{basename(filename)}/")
            else:
                #print("else: ",filename)
                pass

    def list_path(self, folder: str, r=0):
        try:
            return self.connection.nlst(folder)
        except Exception as e:
            if r < self.config.retry_count:
                sleep(self.config.delay_before_retry)
                self.connect()
                return self.list_path(folder, r + 1)
            else:
                self.write_error(f'Unable to get files from {PROTOCOL.lower()}://{self.target}{folder}. Error: {str(e)}')
                self.close()
                return []

    def is_file(self, file: str) -> bool:
        try:
            self.connection.size(file)
            return True
        except:
            return False

    def is_directory(self, file: str) -> bool:
        current = self.connection.pwd()
        try:
            self.connection.cwd(file)
            self.connection.cwd(current)
            return True
        except:
            self.connection.cwd(current)
            return False

    def get_filesize(self, file: str) -> int:
        try:
            return self.connection.size(file)
        except:
            return 0
