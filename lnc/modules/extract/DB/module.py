from rich.console import Console
from lnc.modules.extract.base.config import Config
from lnc.modules.extract.base.module import Extrack as ExtrackBase
from lnc.modules.extract.DB.config import Config
from lnc.modules.download.file import File
import os
import random
import string
import copy
import sqlite3
from typing import List
from lnc.modules.base.file import normalize_path
class DB(ExtrackBase):
    def __init__(self, config: Config, console: Console) -> None:
        super().__init__(config, console)
    
    def run(self, file_path: File) -> File:
        """
        Extracts text from a DB or SQLite file and writes it to a text file.
        Returns a File object for the extracted text file with updated paths and URLs.

        :param file_path: Path to the file.
        :param extract_to: Directory to save the extracted text file.
        :return: Copied File object with updated paths and URLs.
        """
        extract_to = self.config.download_folder
        def generate_random_string(length=20):
            """
            Generates a random string of fixed length.
            """
            letters_and_digits = string.ascii_letters + string.digits
            return ''.join(random.choice(letters_and_digits) for i in range(length))

        def extract_text_from_db(db_path):
            """
            Extracts text from a DB or SQLite file.
            """
            text = ""
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            for table_name in tables:
                table_name = table_name[0]
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()

                text += f"Table: {table_name}\n"
                for row in rows:
                    row_text = "\t".join([str(cell) for cell in row if cell is not None])
                    if row_text.strip():
                        text += row_text + "\n"
                text += "\n"

            conn.close()
            return text

        file_extension = os.path.splitext(file_path.path)[1].lower()
        extract_text_func = {
            '.db': extract_text_from_db,
            '.sqlite': extract_text_from_db,
        }.get(file_extension)

        if extract_text_func is None:
            raise ValueError(f"Unsupported file extension: {file_extension}")

        file_name = os.path.basename(file_path.path)
        random_prefix = generate_random_string()
        new_extract_to = os.path.join(extract_to, f"{random_prefix}_{normalize_path(file_path)}_{file_name}")
        os.makedirs(new_extract_to, exist_ok=True)

        extracted_text = extract_text_func(file_path.local_path)
        text_file_path = os.path.join(new_extract_to, "text.txt")
        with open(text_file_path, 'w', encoding='utf-8') as text_file:
            text_file.write(extracted_text)

        extracted_file = copy.deepcopy(file_path)
        extracted_file.local_path = text_file_path
        extracted_file.path = f"{file_path.path}$text"
        extracted_file.url = f"{file_path.url}$text"
        
        return extracted_file
