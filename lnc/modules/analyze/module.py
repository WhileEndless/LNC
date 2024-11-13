from rich.console import Console
from lnc.modules.analyze.config import Config
from lnc.modules.base.module import Module as ModuleBase
from lnc.modules.download.file import File

class Analyze(ModuleBase):
    config: Config = None
    def __init__(self, config: Config, console: Console) -> None:
        super().__init__(config, console)
    
    def run(self, file:File):
        line_number = 0
        for line in self.read_file(file):
            if line_number==0 and self.config.add_filename_to_analyze:
                line = file.path.split("/")[-1]+" : "+line
            for key in self.config.patterns:
                for match in self.config.patterns[key]["pattern"].findall(line):
                    found = Found()
                    found.file = file
                    found.line = line_number
                    found.match = match
                    found.type = key
                    with self.config.patterns[key]["lock"]:
                        self.config.patterns[key]["total"] += 1
                        self.write(f"{found.file.url}: {found.match}", found.to_dict(), key)
                    yield found
            line_number += 1
    
    def read_file(self, file: File):
        with open(file.local_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                yield line.strip()

class Found:
    file:File = None
    match:str = None
    line:int = None
    type:str = None
    def __init__(self) -> None:
        self.file = None
        self.match = None
        self.line = None
    
    def to_dict(self) -> dict:
        return {
            'file':self.file.to_dict(),
            'match':self.match,
            'line':self.line,
            'type':self.type
        }
    def to_json(self) -> str:
        return {
            'file':self.file.to_dict(),
            'match':self.match,
            'line':self.line,
            'type':self.type
        }