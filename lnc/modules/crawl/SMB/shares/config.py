from lnc.modules.base.network.SMB.config import Config as ConfigBase, CONFIG_PREFIX

CONFIG_PREFIX+="shares_"
CHECK_READ:bool = True
CHECK_WRITE:bool = False
OUTPUT_FILE_NAME_PREFIX = "_smb_share_list"

class Config(ConfigBase):
    check_read:bool = None
    check_write:bool = None
    def __init__(self):
        super().__init__()
        self.check_read = CHECK_READ
        self.check_write = CHECK_WRITE
        self.output+=OUTPUT_FILE_NAME_PREFIX
        
    @classmethod
    def from_dict(cls, config_dict: dict):
        config = super().from_dict(config_dict)
        config.check_read = config_dict.get(CONFIG_PREFIX+"check_read", CHECK_READ)
        config.check_write = config_dict.get(CONFIG_PREFIX+"check_write", CHECK_WRITE)
        config.output+=OUTPUT_FILE_NAME_PREFIX
        return config