from lnc.modules.base.network.SMB.config import Config as SmbConfigBase
from lnc.modules.download.config import Config as DownloadConfigBase
from re import compile

class Config(SmbConfigBase, DownloadConfigBase):
    def __init__(self):
        DownloadConfigBase.__init__(self)
        SmbConfigBase.__init__(self)
    
    @classmethod
    def from_dict(cls, config_dict: dict):
        download_config = DownloadConfigBase.from_dict(config_dict)
        smb_config = SmbConfigBase.from_dict(config_dict)
    
        combined_config = cls()
        
        combined_config.__dict__.update(download_config.__dict__)
        combined_config.__dict__.update(smb_config.__dict__)
        
        return combined_config