class File:
    target:str = None
    port:int = None
    protocol:str = None
    url:str = None
    size:int = None
    path:str = None

    def __init__(self) -> None:
        self.target = None
        self.port = None
        self.protocol = None
        self.url = None
        self.size = None
        self.path = None

    
    def to_dict(self) -> dict:
        return {
            'target':self.target,
            'port':self.port,
            'protocol':self.protocol,
            'url':self.url,
            'size':self.size,
            'path':self.path
        }
    
    @classmethod
    def from_dict(cls, file_dict:dict):
        file = cls()
        file.target = file_dict.get('target')
        file.port = file_dict.get('port')
        file.protocol = file_dict.get('protocol')
        file.url = file_dict.get('url')
        file.size = file_dict.get('size')
        file.path = file_dict.get('path')
        return file

def normalize_path(file:File) -> str:
    if file.protocol is None:
        return "locale_"+file.url.replace('/', '_')
    return file.protocol.lower()+"_"+file.url[3+len(file.protocol):].replace('/', '_')