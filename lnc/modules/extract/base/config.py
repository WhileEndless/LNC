from lnc.modules.download.config import Config as ConfigBase

EXTRACKTION_PATH_PREFIX = 'EXTRACKTION_FILE'

class Config(ConfigBase):
    extracktion_path_prefix:str = EXTRACKTION_PATH_PREFIX
    def __init__(self):
        super().__init__()

    def write(self, data: dict):
        super().write(data)