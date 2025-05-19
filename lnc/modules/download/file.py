from lnc.modules.base.file import File as FileBase

class File(FileBase):
    local_path:str = None
    def __init__(self) -> None:
        super().__init__()
        self.local_path = None
    
    def to_dict(self) -> dict:
        orjdict = super().to_dict()
        orjdict['local_path'] = self.local_path
        return orjdict
    
    @classmethod
    def from_dict(cls, file_dict:dict):
        file = super().from_dict(file_dict)
        file.local_path = file_dict.get('local_path')
        return file