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
    
    def is_binary(self, file_path):
        """
        Check if a file is binary by looking at the first 8KB of data.
        Returns True if the file appears to be binary, False otherwise.
        """
        try:
            chunk_size = 8192  # 8KB
            with open(file_path, 'rb') as f:
                chunk = f.read(chunk_size)
                # Check for null bytes or high concentration of non-printable characters
                if b'\x00' in chunk:
                    return True
                # Count the percentage of non-text bytes
                text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
                non_text_chars = sum(1 for byte in chunk if byte not in text_chars)
                if len(chunk) > 0 and non_text_chars / len(chunk) > 0.3:  # 30% threshold
                    return True
            return False
        except Exception:
            # If there's any error reading the file, treat it as non-binary
            return False
    
    def read_file(self, file: File):
        # Skip binary files if configured
        if hasattr(self.config, 'check_binarys') and self.config.check_binarys and self.is_binary(file.local_path):
            # Log that we're skipping a binary file
            self.console.print(f"[yellow][*] Skipping binary file: {file.path}[/yellow]")
            return
        
        # Process text files
        try:
            with open(file.local_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    yield line.strip()
        except Exception as e:
            self.console.print(f"[red][*] Error reading file {file.path}: {str(e)}[/red]")
            return

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