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
            try:
                with fitz.open(pdf_path) as doc:
                    for page_num, page in enumerate(doc):
                        # Extract text in text mode (not HTML or XML) to avoid markup
                        page_text = page.get_text("text")
                        # Filter out control characters and non-printable characters
                        clean_text = ''.join(char for char in page_text if ord(char) >= 32 or char in '\n\t\r')
                        # Only add page separator if there's actually content
                        if clean_text.strip():
                            text += f"Page {page_num + 1}:\n{clean_text}\n"
                            text += "=" * 40 + "\n"  # Page separator
                
                # Final cleanup to remove any overly long lines (likely binary data)
                lines = []
                for line in text.splitlines():
                    if len(line) > 1000:  # If line is suspiciously long
                        continue
                    lines.append(line)
                
                return "\n".join(lines)
            except Exception as e:
                self.console.print(f"[red][*] Error extracting text from PDF: {str(e)}[/red]")
                return "Error extracting text from PDF"

        def extract_text_from_docx(docx_path):
            """
            Extracts text from a DOCX file.
            """
            text = ""
            try:
                doc = docx.Document(docx_path)
                
                # Extract header/footer content if available
                try:
                    for section in doc.sections:
                        # Get headers
                        for header in section.header.paragraphs:
                            if header.text.strip():
                                text += f"Header: {header.text}\n"
                        
                        # Get footers
                        for footer in section.footer.paragraphs:
                            if footer.text.strip():
                                text += f"Footer: {footer.text}\n"
                except:
                    pass  # Headers/footers might not be accessible
                
                # Get document title if available
                if doc.core_properties.title:
                    text += f"Title: {doc.core_properties.title}\n\n"
                
                # Get document paragraphs
                for para in doc.paragraphs:
                    if para.text.strip():
                        # Include styling information for highlighted text
                        formatted_text = para.text
                        text += formatted_text + "\n"
                
                # Extract table content
                for table in doc.tables:
                    text += "Table Content:\n"
                    for row in table.rows:
                        row_text = " | ".join([cell.text for cell in row.cells if cell.text.strip()])
                        if row_text.strip():
                            text += row_text + "\n"
                    text += "\n"
                
                return text
            except Exception as e:
                self.console.print(f"[red][*] Error extracting text from DOCX: {str(e)}[/red]")
                return "Error extracting text from DOCX"

        def extract_text_from_xlsx(xlsx_path):
            """
            Extracts text from an XLSX file.
            """
            text = ""
            try:
                wb = openpyxl.load_workbook(xlsx_path, data_only=True)  # data_only=True to get values instead of formulas
                
                for sheet_name in wb.sheetnames:
                    sheet = wb[sheet_name]
                    text += f"\nSheet: {sheet_name}\n"
                    text += "=" * 40 + "\n"
                    
                    # Get the maximum row and column indices to avoid empty cells
                    max_row = sheet.max_row
                    max_col = sheet.max_column
                    
                    # Extract data from cells
                    for row in range(1, max_row + 1):
                        row_data = []
                        has_data = False
                        
                        for col in range(1, max_col + 1):
                            cell = sheet.cell(row=row, column=col)
                            value = cell.value
                            
                            if value is not None:
                                has_data = True
                                row_data.append(str(value))
                            else:
                                row_data.append("")
                        
                        if has_data:
                            text += " | ".join(row_data) + "\n"
                
                return text
            except Exception as e:
                self.console.print(f"[red][*] Error extracting text from XLSX: {str(e)}[/red]")
                return "Error extracting text from XLSX"

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
