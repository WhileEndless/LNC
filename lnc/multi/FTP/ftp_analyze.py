from lnc.modules.download.FTP.config import Config
from lnc.modules.download.FTP.module import FTP_Download, File
from lnc.multi.base.handler import Handler as HandlerBase
from rich.console import Console
from lnc.multi.analyze import Handler as AnalyzeHandler

class Handler(HandlerBase):
    config_dict:dict=None
    config: Config = None
    module: FTP_Download = None
    connection_status: bool = False
    target:dict = None
    analayzer:AnalyzeHandler=None
    def __init__(self, console:Console, progress, task) -> None:
        super().__init__(console, progress, task)
        self.target=None
        self.connection_status = False
        self.analayzer=None
        
    def run(self, file:dict, config_dict:dict) -> int:
        target=file['target']
        if config_dict!=self.config_dict or target!=self.target:
            self.target=target
            self.config=Config.from_dict(config_dict)
            self.module=FTP_Download(config=self.config, console=self.console, target=target, username=config_dict['username'], password=config_dict['password'], domain=config_dict['domain'])
            self.config_dict=config_dict
            if not self.module.connect():
                self.connection_status=False
                return FTP_Download.total
            self.connection_status=True
            self.analayzer=AnalyzeHandler(console=self.console,progress=self.progress,task=self.task)
        if self.connection_status:
            file = File.from_dict(file)
            if self.module.run(file=file):
                if not self.config.disable_output_text:
                    self.console.print(f"[green][+] File: {file.url}[/green] [blue]Size: {file.size}[/blue]")
                if self.analayzer.run(file=file,config_dict=self.config_dict):
                    self.module.rename(file)
                else:
                    self.module.remove()
                self.progress.update(self.task)
        return FTP_Download.total