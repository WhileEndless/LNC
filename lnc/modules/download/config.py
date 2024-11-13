from lnc.modules.base.network.base.config import Config as ConfigBase
from re import compile

ALWAYS_DOWNLOAD=['.config$','.ini$','.dll$','.txt$','.metadata$']
DOWNLOAD_FOLDER="./donwloads/"
MAX_DOWNLOAD_SIZE = 10

class Config(ConfigBase):
    ignore_filename_contains:list = None
    always_download:list = None
    download_folder:str = None
    max_download_size:int = None
    def __init__(self):
        super().__init__()
        self.always_download = [compile(pattern) for pattern in ALWAYS_DOWNLOAD]
        self.download_folder = DOWNLOAD_FOLDER
        self.max_download_size = MAX_DOWNLOAD_SIZE * 1024 * 1024
        
    @classmethod
    def from_dict(cls, config_dict: dict):
        config = super().from_dict(config_dict)
        config.always_download = [compile(pattern) for pattern in config_dict.get("always_download", ALWAYS_DOWNLOAD)]
        config.download_folder = config_dict.get("download_folder", DOWNLOAD_FOLDER)
        config.max_download_size = config_dict.get("max_download_size", MAX_DOWNLOAD_SIZE) * 1024 * 1024
        return config