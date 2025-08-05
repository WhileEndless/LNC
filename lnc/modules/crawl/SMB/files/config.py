from lnc.modules.base.network.SMB.config import Config as ConfigBase, CONFIG_PREFIX
from re import compile

CONFIG_PREFIX+="files_"
OUTPUT_FILE_NAME_PREFIX = "_smb_files"

IGNORE_FOLDER_NAME_CONTAINS = [
    "audio",
    "bin",
    "boot",
    "dev",
    "etc",
    "lib",
    "lib64",
    "lost\\+found",
    "media",
    "opt",
    "proc",
    "run",
    "sbin",
    "srv",
    "sys",
    "tmp",
    "usr",
    "snap",
    "swapfile",
    "vmlinuz",
    "windows",
    "program files",
    "programdata",
]
IGNORE_SHARES = ["ipc$","print$"]
MAX_FILE_AGE_DAYS = 365

class Config(ConfigBase):
    ignore_folder_name_contains:list = None
    ignore_shares:list = None
    max_file_age_days:int = None
    def __init__(self):
        super().__init__()
        self.ignore_folder_name_contains = [compile(pattern) for pattern in IGNORE_FOLDER_NAME_CONTAINS]
        self.ignore_shares = IGNORE_SHARES
        self.max_file_age_days = MAX_FILE_AGE_DAYS
        self.output+=OUTPUT_FILE_NAME_PREFIX
        
    @classmethod
    def from_dict(cls, config_dict: dict):
        config = super().from_dict(config_dict)
        config.ignore_folder_name_contains = [compile(pattern) for pattern in config_dict.get("ignore_folder_name_contains", IGNORE_FOLDER_NAME_CONTAINS)]
        config.ignore_shares = config_dict.get(CONFIG_PREFIX+"ignore_shares", IGNORE_SHARES)
        config.max_file_age_days = config_dict.get("max_file_age_days", MAX_FILE_AGE_DAYS)
        config.output+=OUTPUT_FILE_NAME_PREFIX
        return config