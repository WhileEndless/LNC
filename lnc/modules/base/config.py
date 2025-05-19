from typing import List
import re
from uuid import uuid4

OUTPUT = "output"

DISABLE_OUTPUT_JSON = False
DISABLE_OUTPUT_TEXT = False
WRITE_ERRORS_TO_FILE = False
ENABLE_ERROR_OUTPUT = False
DISABLE_OUTPUT_END_PREFIX = False
class Config:
    output:str = None
    output_end:str = None
    disable_output_json:bool = None
    disable_output_text:bool = None
    disable_output_end_prefix:bool = None
    enable_error_output:bool = None
    write_errors_to_file:bool = None
    

    def __init__(self):
        self.output = OUTPUT
        self.output_end = str(uuid4())
        self.disable_output_json = DISABLE_OUTPUT_JSON
        self.disable_output_text = DISABLE_OUTPUT_TEXT
        self.write_errors_to_file = WRITE_ERRORS_TO_FILE
        self.enable_error_output = ENABLE_ERROR_OUTPUT
        self.disable_output_end_prefix = DISABLE_OUTPUT_END_PREFIX

    @classmethod
    def from_dict(cls, config_dict: dict):
        config = cls()
        config.output = config_dict.get("output", OUTPUT)
        config.output_end = config_dict.get("output_end", str(uuid4()))
        config.disable_output_json = config_dict.get("disable_output_json", DISABLE_OUTPUT_JSON)
        config.disable_output_text = config_dict.get("disable_output_text", DISABLE_OUTPUT_TEXT)
        config.write_errors_to_file = config_dict.get("write_errors_to_file", WRITE_ERRORS_TO_FILE)
        config.enable_error_output = config_dict.get("enable_error_output", ENABLE_ERROR_OUTPUT)
        config.disable_output_end_prefix = config_dict.get("disable_output_end_prefix", DISABLE_OUTPUT_END_PREFIX)
        return config