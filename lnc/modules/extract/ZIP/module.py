from rich.console import Console
from lnc.modules.extract.base.module import Extrack as ExtrackBase
from lnc.modules.extract.ZIP.config import Config
from lnc.modules.download.file import File
import zipfile
import tarfile
import os
import random
import string
import shutil
import copy
from typing import List
import rarfile
import py7zr
from lnc.modules.base.file import normalize_path

class ZIP(ExtrackBase):
    config: Config = None

    def __init__(self, config: Config, console: Console) -> None:
        super().__init__(config, console)
    
    def run(self, zip_path: File) -> List[File]:
        """
        Extracts a compressed file to a specified directory while preserving directory structure.
        Ensures path traversal vulnerabilities are mitigated.
        Returns a list of copied File objects for the extracted files with updated paths and URLs.

        :param zip_path: Path to the compressed file.
        :param extract_to: Directory to extract the contents.
        :return: List of copied File objects with updated paths and URLs.
        """
        extract_to = self.config.download_folder
        def is_within_directory(directory, target):
            """
            Check if a target path is within a given directory to avoid path traversal vulnerabilities.
            """
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
            return os.path.commonprefix([abs_directory, abs_target]) == abs_directory

        def generate_random_string(length=20):
            """
            Generates a random string of fixed length.
            """
            letters_and_digits = string.ascii_letters + string.digits
            return ''.join(random.choice(letters_and_digits) for i in range(length))

        def extract_zip(zip_path, extract_to):
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)

        def extract_rar(rar_path, extract_to):
            with rarfile.RarFile(rar_path, 'r') as rar_ref:
                rar_ref.extractall(extract_to)

        def extract_7z(sevenz_path, extract_to):
            with py7zr.SevenZipFile(sevenz_path, mode='r') as sevenz_ref:
                sevenz_ref.extractall(extract_to)

        def extract_tar(tar_path, extract_to):
            with tarfile.open(tar_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_to)

        file_extension = os.path.splitext(zip_path.path)[1].lower()
        extract_func = {
            '.zip': extract_zip,
            '.rar': extract_rar,
            '.7z': extract_7z,
            '.tar': extract_tar,
            '.gz': extract_tar,
            '.xz': extract_tar,
        }.get(file_extension)

        if extract_func is None:
            raise ValueError(f"Unsupported file extension: {file_extension}")

        zip_name = os.path.basename(zip_path.path)
        random_prefix = generate_random_string()
        new_extract_to = os.path.join(extract_to, f"{random_prefix}_{normalize_path(zip_path)}_{zip_name}")
        os.makedirs(new_extract_to, exist_ok=True)

        extracted_files = []

        extract_func(zip_path.local_path, new_extract_to)

        for root, _, files in os.walk(new_extract_to):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, new_extract_to)
                if not is_within_directory(new_extract_to, file_path):
                    raise Exception(f"Path traversal attempt detected: {file_path}")
                
                extracted_file = copy.deepcopy(zip_path)
                extracted_file.local_path = file_path
                extracted_file.path = f"{zip_path.path}${relative_path}"
                extracted_file.url = f"{zip_path.url}${relative_path}"
                
                extracted_files.append(extracted_file)

        return extracted_files

