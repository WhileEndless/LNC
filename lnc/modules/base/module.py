from lnc.modules.base.config import Config
from typing import List
from threading import Lock
from json import dumps
from rich.console import Console

class Module:
    config: Config = None
    console:Console = None
    write_lock:Lock=Lock()

    def __init__(self,config:Config, console:Console) -> None:
        self.config=config
        self.console=console

    def write(self,text_data:str,dict_data:dict,add_file_name:str=None):
        output_file_name = self.config.output
        if add_file_name:
            output_file_name = f"{output_file_name}_{add_file_name}"
        if not self.config.disable_output_end_prefix:
            output_file_name = f"{output_file_name}_{self.config.output_end}"
        if not self.config.disable_output_json:
            if dict_data!={}:
                json_file_name=f"{output_file_name}.json"
                with Module.write_lock:
                    with open(json_file_name, "a") as json_file:
                        json_file.write(dumps(dict_data)+"\n")
        if not self.config.disable_output_text:
            text_file_name = f"{output_file_name}.txt"
            with Module.write_lock:
                with open(text_file_name, "a") as text_file:
                    text_file.write(text_data+"\n")
    
    def write_error(self,error:str):
        if self.config.enable_error_output:
            self.console.print(f'[red][*] {error}[/red]')
        if self.config.write_errors_to_file:
            if self.config.disable_output_end_prefix:
                error_file_name = f"{self.config.output}_errors.txt"
            else:
                error_file_name = f"{self.config.output}_{self.config.output_end}_errors.txt"
            with Module.write_lock:
                with open(error_file_name, "a") as error_file:
                    error_file.write(error+"\n")

from enum import Enum

class Module_Type(Enum):
    SINGLE = 1
    MULTI = 2