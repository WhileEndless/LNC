from rich.console import Console
from lnc.modules.extract.base.module import Extrack as ExtrackBase
from lnc.modules.extract.DOC.config import Config
from lnc.modules.download.file import File
import os
import random
import string
import copy
from typing import List
import docx
import openpyxl
from lnc.modules.base.file import normalize_path
import fitz

class DOC(ExtrackBase):
    config: Config = None
    def __init__(self, config: Config, console: Console) -> None:
        super().__init__(config, console)
    
    def run(self, file_path: File) -> File:
        """
        Extracts text from a PDF, DOCX, or XLSX file and writes it to a text file.
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

        def extract_text_from_pdf(pdf_path):
            """
            Extracts text from a PDF file.
            """
            text = ""
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    text += page.get_text()
            return "\n".join([line for line in text.splitlines() if line.strip()])

        def extract_text_from_docx(docx_path):
            """
            Extracts text from a DOCX file.
            """
            text = ""
            doc = docx.Document(docx_path)
            for para in doc.paragraphs:
                if para.text.strip():
                    text += para.text + "\n"
            return text

        def extract_text_from_xlsx(xlsx_path):
            """
            Extracts text from an XLSX file.
            """
            text = ""
            wb = openpyxl.load_workbook(xlsx_path)
            for sheet in wb:
                for row in sheet.iter_rows():
                    row_text = "\t".join([str(cell.value) for cell in row if cell.value is not None])
                    if row_text.strip():
                        text += row_text + "\n"
            return text

        file_extension = os.path.splitext(file_path.path)[1].lower()
        extract_text_func = {
            '.pdf': extract_text_from_pdf,
            '.docx': extract_text_from_docx,
            '.xlsx': extract_text_from_xlsx,
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
