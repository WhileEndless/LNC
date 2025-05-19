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
        """
        Process data and return result count.
        
        Returns:
            int: The total number of items processed or None if not applicable
        """
        pass
    
    def clean_up(self):
        """
        Perform any necessary cleanup before the handler is destroyed.
        Override this method in derived classes to handle specific cleanup tasks.
        """
        # Base implementation does nothing
        pass