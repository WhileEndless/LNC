from lnc.modules.base.config import Config as ConfigBase
from typing import List
import re
from threading import Lock

PATTERNS = {
    "password": [
        "password",
        "pwd=",
        "şifre",
        "parola",
        "sifre",
        "contentHash"
    ],
    "sensitive":[
        "[1-9][0-9]{10}",
        "4[0-9]{12}(?:[0-9]{3})?",
        "5[1-5][0-9]{14}",
        "6(?:011|5[0-9]{2})[0-9]{12}",
        "3[47][0-9]{13}",
        "3(?:0[0-5]|[68][0-9])[0-9]{11}",
        "(?:2131|1800|35\\d{3})\\d{11}"
    ]
}
TAKE_AFTER = 50
TAKE_BEFORE = 50
KEEP_EXTRACTED_FILES = False
ALWAYS_KEEP_EXTRACTED_FILES = False
ADD_FILENAME_TO_ANALYZE = True

class Config(ConfigBase):
    patterns:dict = None
    take_before:int = 10
    take_after:int = 10
    keep_extracted_files:bool = False
    always_keep_extracted_files:bool = False
    add_filename_to_analyze:bool = True
    def __init__(self):
        super().__init__()
        self.patterns={}
        self.take_after = TAKE_AFTER
        self.take_before = TAKE_BEFORE
        self.keep_extracted_files = KEEP_EXTRACTED_FILES
        self.always_keep_extracted_files = ALWAYS_KEEP_EXTRACTED_FILES
        self.add_filename_to_analyze = ADD_FILENAME_TO_ANALYZE
        
        for key in PATTERNS:
            self.patterns[key]={}
            self.patterns[key]["pattern"] = compile_regex_patterns(PATTERNS[key],self)
            self.patterns[key]["lock"] = Lock()
            self.patterns[key]["total"] = 0
    
    @classmethod
    def from_dict(cls, config_dict: dict):
        config= super().from_dict(config_dict)
        config.patterns={}
        patterns=config_dict.get("patterns",PATTERNS)
        for key in patterns:
            if key not in config.patterns:
                config.patterns[key]={}
            config.patterns[key]["pattern"] = compile_regex_patterns(patterns[key], config)
            config.patterns[key]["lock"] = Lock()
            config.patterns[key]["total"] = 0
        config.take_after = config_dict.get("take-after",TAKE_AFTER)
        config.take_before = config_dict.get("take-before",TAKE_BEFORE)
        config.keep_extracted_files = config_dict.get("keep-extracted-files",KEEP_EXTRACTED_FILES)
        config.always_keep_extracted_files = config_dict.get("always-keep-extracted-files",ALWAYS_KEEP_EXTRACTED_FILES)
        config.add_filename_to_analyze = config_dict.get("add-filename-to-analyze",ADD_FILENAME_TO_ANALYZE)
        return config

def compile_regex_patterns(patterns: List[str], config:Config) -> re.Pattern:
    combined_pattern = "|".join([f".{{0,{config.take_before}}}{pattern}.{{0,{config.take_after}}}" for pattern in patterns])
    return re.compile(combined_pattern, re.IGNORECASE)