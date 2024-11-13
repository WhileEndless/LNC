from lnc.multi.base.handler import Handler
from lnc.modules.crawl.SMB.shares.config import Config
from lnc.modules.crawl.SMB.shares.module import SMB_Shares
from rich.console import Console

class Handler(Handler):
    config_dict:dict=None
    config: Config = None
    module: SMB_Shares = None
    connection_status: bool = False
    target:str = None
    def __init__(self, console:Console, progress, task) -> None:
        super().__init__(console, progress, task)
        self.target=None
        self.connection_status = False

    def run(self, target, config_dict: dict) -> int:
        if config_dict!=self.config_dict or target!=self.target:
            self.target=target
            self.config=Config.from_dict(config_dict)
            self.module=SMB_Shares(config=self.config, console=self.console, target=target, username=config_dict['username'], password=config_dict['password'], domain=config_dict['domain'])
            self.config_dict=config_dict
            if not self.module.connect():
                self.connection_status=False
                return SMB_Shares.total
            self.connection_status=True
        if self.connection_status:
            for share in self.module.run():
                if not self.config.disable_output_text:
                    text = f"[green][+] Share: {target}:{self.config.port} - {share.name} - "
                    if share.read_access:
                        text += "Read Access: True - "
                    else:
                        text += "[/green][red]Read Access: False - [/red][green]"
                    if share.write_access:
                        text += "Write Access: True"
                    else:
                        text += "[/green][red]Write Access: False[/red]"
                    self.console.print(text)
                self.progress.update(self.task, Found=SMB_Shares.total)
        return SMB_Shares.total

    def __del__(self):
        if self.module:
            self.module.close()