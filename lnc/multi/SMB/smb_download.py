from lnc.modules.download.SMB.config import Config
from lnc.modules.download.SMB.module import SMB_Download, File
from lnc.multi.base.handler import Handler
from rich.console import Console

class Handler(Handler):
    config_dict:dict=None
    config: Config = None
    module: SMB_Download = None
    connection_status: bool = False
    target:dict = None
    def __init__(self, console:Console, progress, task) -> None:
        super().__init__(console, progress, task)
        self.target=None
        self.connection_status = False
    
    def run(self, file:dict, config_dict: dict) -> int:
        target=file['target']
        if config_dict!=self.config_dict or target!=self.target:
            try:
                self.module.close()
            except:
                pass
            self.target=target
            self.config=Config.from_dict(config_dict)
            self.module = SMB_Download(config=self.config, console=self.console, target=self.target, username=config_dict['username'], password=config_dict['password'], domain=config_dict['domain'])
            self.config_dict=config_dict
            if not self.module.connect():
                self.connection_status=False
                return SMB_Download.total
            self.connection_status=True
        if self.connection_status:
            file = File.from_dict(file)
            if self.module.run(file=file):
                if not self.config.disable_output_text:
                    self.console.print(f"[green][+] File: {file.url}[/green] [blue]Size: {file.size}[/blue]")
            self.progress.update(self.task)
        return SMB_Download.total

    def __del__(self):
        if self.module:
            self.module.close()

class Filter:
    def __init__(self,config_dict:dict) -> None:
        self.config=Config.from_dict(config_dict)

    def check(self,data:dict) -> bool:
        return (self.config.always_download != [] and any(regex.search(data['path'].lower()) for regex in self.config.always_download))