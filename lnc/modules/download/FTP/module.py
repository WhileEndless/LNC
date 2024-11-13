from lnc.modules.base.network.FTP.module import FTP_Module
from lnc.modules.crawl.FTP.module import File as FTP_File
from lnc.modules.download.file import File as Download_File
from lnc.modules.base.file import normalize_path
from lnc.modules.download.FTP.config import Config
from lnc.modules.base.module import Module_Type
from threading import Lock
from rich.console import Console
from uuid import uuid4
from os.path import exists, join, basename
from os import makedirs, rename, remove
from time import sleep
import ftplib

PROTOCOL = 'FTP'

class File(FTP_File, Download_File):
    def __init__(self) -> None:
        Download_File.__init__(self)
        FTP_File.__init__(self)
    
    @classmethod
    def from_dict(cls, file_dict:dict):
        file_ftp = FTP_File.from_dict(file_dict)
        file_download = Download_File.from_dict(file_dict)
        combined_file = cls()
        combined_file.__dict__.update(file_ftp.__dict__)
        combined_file.__dict__.update(file_download.__dict__)
        return combined_file
    
    def to_dict(self) -> dict:
        file_ftp = FTP_File.to_dict(self)
        file_download = Download_File.to_dict(self)
        combined_file = file_ftp
        combined_file.update(file_download)
        return combined_file

class FTP_Download(FTP_Module):
    total:int = 0
    total_lock:Lock = Lock()

    module_run_type = Module_Type.MULTI

    config:Config = None
    downloader_id:str = None

    def __init__(self, config: Config, console:Console, target: str, username: str = None, password: str = None, domain: str = None) -> None:
        super().__init__(config, console, target, username, password, domain)
        self.downloader_id = str(uuid4())
        if not exists(self.config.download_folder):
            try:
                makedirs(self.config.download_folder)
            except:
                pass
    
    def run(self,file:File) -> File:
        if self.config.max_download_size < file.size:
            self.console.print(f'[yellow][*] Ignoring too large file: {file.url}[/yellow]')
            return
        if file.size == 0:
            return
        return self.download(file, temp=not (self.config.always_download != [] and any(regex.search(basename(file.path).lower()) for regex in self.config.always_download)))

    def download(self, file:File, temp:bool=True, r:int=0) -> File:
        try:
            if file.local_path and exists(file.local_path):
                return file
        except:
            pass
        file_path = join(self.config.download_folder, 'temp_' + self.downloader_id) if temp else join(self.config.download_folder, normalize_path(file))
        try:
            with open(file_path, 'wb') as temp_file:
                self.connection.retrbinary(f'RETR {file.path}', temp_file.write)
            file.local_path = file_path
            with FTP_Download.total_lock:
                FTP_Download.total += 1
            return file
            
        except Exception as e:
            if "550 Failed" in str(e):
                self.remove()
                self.write_error(f'Error downloading file {file.url}. Error: {str(e)}')
                return
            if r < self.config.retry_count:
                self.console.print(f'[yellow][*] Error downloading file {file.url}. Retrying...[/yellow]')
                self.close()
                sleep(self.config.delay_before_retry)
                self.connect()
                return self.download(file, temp, r+1)
            self.write_error(f'Error downloading file {file.url}. Error: {str(e)}')
            self.remove()

    def rename(self, file:File) -> File:
        locale_path = join(self.config.download_folder, normalize_path(file))
        if exists(locale_path):
            return file
        rename(join(self.config.download_folder, 'temp_' + self.downloader_id), locale_path)
        file.local_path = locale_path
        return file
    
    def remove(self):
        if exists(join(self.config.download_folder, 'temp_' + self.downloader_id)):
            remove(join(self.config.download_folder, 'temp_' + self.downloader_id))
            return True