from lnc.modules.crawl.SMB.files.config import Config
from lnc.modules.crawl.SMB.files.module import SMB_Files, Share
from lnc.multi.base.handler import Handler
from lnc.multi.accessibility_manager import AccessibilityManager
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
            # Keep track of files we've seen in this run
            previous_total = SMB_Files.total  
            
            for file in self.module.run(Share.from_dict(share)):
                if not self.config.disable_output_text:
                    self.console.print(f"[green][+] File: {file.url}[/green] [blue]Size: {file.size}[/blue]")
                
                # Mark item as processed for duplicate prevention
                checker = AccessibilityManager.get_instance()
                if checker:
                    checker.mark_item_processed(file.url)
                
                # Only update progress when total actually changes
                if previous_total != SMB_Files.total:
                    previous_total = SMB_Files.total
                    self.progress.update(self.task, Found=SMB_Files.total)
            
        # Return current total - this ensures we always have the most up-to-date count
        return SMB_Files.total
    def __del__(self):
        try:
            self.clean_up()
        except:
            pass
    
    def clean_up(self):
        """Clean up resources properly"""
        if self.module:
            self.module.close()