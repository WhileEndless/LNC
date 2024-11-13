from lnc.modules.extract.base.config import Config as ConfigBase

class Config(ConfigBase):
    def __init__(self):
        super().__init__()

    def write(self, data: dict):
        super().write(data)