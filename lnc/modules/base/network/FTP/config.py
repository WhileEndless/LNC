from lnc.modules.base.network.base.config import Config as ConfigBase

PORT:int = 21
CONFIG_PREFIX:str = "ftp_"

class Config(ConfigBase):
    def __init__(self):
        super().__init__()
        self.port = PORT

    @classmethod
    def from_dict(cls, config_dict: dict):
        config = super().from_dict(config_dict)
        config.port = config_dict.get(CONFIG_PREFIX+"port", PORT)
        return config

