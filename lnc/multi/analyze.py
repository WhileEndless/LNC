from lnc.multi.base.handler import Handler as HandlerBase
from rich.console import Console
from lnc.modules.extract.DOC.module import DOC
from lnc.modules.extract.DOC.config import Config as DOC_Config
from lnc.modules.extract.ZIP.module import ZIP
from lnc.modules.extract.ZIP.config import Config as ZIP_Config
from lnc.modules.extract.DB.module import DB
from lnc.modules.extract.DB.config import Config as DB_Config
from lnc.modules.analyze.config import Config
from lnc.modules.analyze.module import Analyze
from lnc.modules.download.file import File
import os
import shutil
class Handler(HandlerBase):
    config_dict:dict=None
    config: Config = None
    module: Analyze = None
    doc:DOC=None
    zip:ZIP=None
    db:DB=None
    analayzer:Analyze=None
    def __init__(self, console, progress, task) -> None:
        super().__init__(console, progress, task)
        self.doc = None
        self.zip = None
        self.db = None
        self.analayzer = None
    
    def run(self, file:File, config_dict: dict) -> int:
        if config_dict!=self.config_dict:
            self.config=Config.from_dict(config_dict)
            self.module = Analyze(config=self.config, console=self.console)
            self.config_dict=config_dict
            doc_config=DOC_Config.from_dict(config_dict)
            self.doc=DOC(config=doc_config,console=self.console)
            zip_config=ZIP_Config.from_dict(config_dict)
            self.zip=ZIP(config=zip_config,console=self.console)
            db_config=DB_Config.from_dict(config_dict)
            self.db=DB(config=db_config,console=self.console)
            analayzer_config=Config.from_dict(config_dict)
            self.analayzer=Analyze(config=analayzer_config,console=self.console)
            
        _file = file
        analayze_files = self.extrack_file(_file)
        flag=False
        if analayze_files:
            for f in analayze_files:
                in_flag=False
                for found in self.analayzer.run(f):
                    self.progress.update(self.task, **{found.type.capitalize(): self.analayzer.config.patterns[found.type]["total"]})
                    if not self.config.disable_output_text:
                        self.console.print(f"[green][+] File: {found.file.url}[/green] [blue]Line: {found.line}[/blue] [green]Match: {found.match}[/green] [yellow]Type: {found.type}[/yellow]")
                    flag=True
                    in_flag=True
                if self.config.always_keep_extracted_files==False and in_flag==False or self.config.keep_extracted_files==False and self.config.always_keep_extracted_files==False:
                    if not f.local_path.startswith(os.path.join(config_dict['download_folder'], "temp_")) and _file.local_path!=f.local_path:
                        if os.path.isfile(f.local_path):
                            os.remove(f.local_path)
            try:
                folder = analayze_files[0].local_path.split(config_dict['download_folder'])[1].split("/")[0]
            except:
                folder = analayze_files[0].local_path.split(config_dict['file'])[1].split("/")[0]    
            if self.config.always_keep_extracted_files==False and flag==False or self.config.keep_extracted_files==False and self.config.always_keep_extracted_files==False:
                try:
                    folder = analayze_files[0].local_path.split(config_dict['download_folder'])[1].split("/")[0]
                except:
                    folder = analayze_files[0].local_path.split(config_dict['file'])[1].split("/")[0]    
                if os.path.isdir(os.path.join(config_dict['download_folder'], folder)):
                    shutil.rmtree(os.path.join(config_dict['download_folder'], folder))
            
            if os.path.isdir(os.path.join(config_dict['download_folder'], folder)): 
                remove_empty_directories(os.path.join(config_dict['download_folder'], folder))
            
            self.progress.update(self.task)
        return flag

    def extrack_file(self, file:File, locale=False):
        path=None
        if locale:
            path=file.local_path
        else:
            path=file.path
        analayze_files = [file]
        if path.endswith(".zip") or path.endswith(".rar") or path.endswith(".7z") or path.endswith(".tar") or path.endswith(".tar.gz") or path.endswith(".tar.xz"):
            analayze_files = self.zip.run(file)
        elif path.endswith(".pdf") or path.endswith(".docx") or path.endswith(".xlsx"):
            analayze_files = [self.doc.run(file)]
        elif path.endswith(".db") or path.endswith(".sqlite"):
            analayze_files = [self.db.run(file)]
        else:
            if locale:
                return None
            else:
                return [file]
        analayze_files_last=[]
        for f in analayze_files:
            r=self.extrack_file(f, locale=True)
            if r:
                analayze_files_last.extend(r)
            else:
                analayze_files_last.append(f)
        return analayze_files_last
    
def remove_empty_directories(directory):
    for dirpath, dirnames, _ in os.walk(directory, topdown=False):
        for dirname in dirnames:
            dir_to_check = os.path.join(dirpath, dirname)
            if not os.listdir(dir_to_check):
                os.rmdir(dir_to_check)
