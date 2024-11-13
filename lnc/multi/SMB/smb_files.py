from lnc.modules.crawl.SMB.files.config import Config
from lnc.modules.crawl.SMB.files.module import SMB_Files, Share
from lnc.multi.base.handler import Handler
from rich.console import Console

class Handler(Handler):
    config_dict:dict=None
    config: Config = None
    module: SMB_Files = None
    connection_status: bool = False
    target:dict = None
    def __init__(self, console:Console, progress, task) -> None:
        super().__init__(console, progress, task)
        self.target=None
        self.connection_status = False
    
    def run(self, share:dict, config_dict: dict) -> int:
        target=share['target']
        if config_dict!=self.config_dict or target!=self.target:
            self.target=target
            self.config=Config.from_dict(config_dict)
            self.module=SMB_Files(config=self.config, console=self.console, target=target, username=config_dict['username'], password=config_dict['password'], domain=config_dict['domain'])
            self.config_dict=config_dict
            if not self.module.connect():
                self.connection_status=False
                return SMB_Files.total
            self.connection_status=True
        if self.connection_status:
            for file in self.module.run(Share.from_dict(share)):
                if not self.config.disable_output_text:
                    self.console.print(f"[green][+] File: {file.url}[/green] [blue]Size: {file.size}[/blue]")
                self.progress.update(self.task, Found=SMB_Files.total)
        return SMB_Files.total
    def __del__(self):
        if self.module:
            self.module.close()