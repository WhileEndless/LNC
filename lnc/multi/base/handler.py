from rich.progress import Progress
from rich.console import Console

class Handler:
    config_dict:dict=None
    config=None
    console: Console
    def __init__(self,console, progress, task) -> None:
        self.console=console
        self.progress: Progress = progress
        self.task = task
        self.config_dict=None
        self.config=None
        
    def run(self, data, config:dict) -> int:
        pass