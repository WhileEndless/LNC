from rich.console import Console
from lnc.modules.extract.base.config import Config
from lnc.modules.base.module import Module

class Extrack(Module):
    def __init__(self, config: Config, console: Console) -> None:
        super().__init__(config, console)