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

        def safe_extract_members(extract_func, archive_path, extract_to, members=None):
            """
            Safely extract archive members, filtering out potentially dangerous paths.
            """
            extraction_path = extract_to
            try:
                # Create the extraction directory if it doesn't exist
                os.makedirs(extraction_path, exist_ok=True)
                
                if members:
                    # Filter out dangerous paths
                    safe_members = []
                    for member in members:
                        # Skip absolute paths and paths with ..
                        if os.path.isabs(member) or '..' in member:
                            self.console.print(f"[yellow][*] Skipping potentially unsafe path: {member}[/yellow]")
                            continue
                        
                        # Validate that the extracted path will be within the extraction directory
                        target_path = os.path.join(extraction_path, member)
                        if not is_within_directory(extraction_path, target_path):
                            self.console.print(f"[yellow][*] Skipping path traversal attempt: {member}[/yellow]")
                            continue
                        
                        safe_members.append(member)
                    
                    # Extract only safe members
                    extract_func(archive_path, extraction_path, safe_members)
                else:
                    # Extract all with safety checks in the archive's internal logic
                    extract_func(archive_path, extraction_path)
                
                return True
            except Exception as e:
                self.console.print(f"[red][*] Extraction error: {str(e)}[/red]")
                return False

        def extract_zip(zip_path, extract_to):
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Get list of members to check for safety
                    members = zip_ref.namelist()
                    safe_members = []
                    
                    # Check each member for safety
                    for member in members:
                        if os.path.isabs(member) or '..' in member:
                            self.console.print(f"[yellow][*] Skipping potentially unsafe ZIP entry: {member}[/yellow]")
                            continue
                        
                        # Validate extraction path
                        target_path = os.path.join(extract_to, member)
                        if not is_within_directory(extract_to, target_path):
                            self.console.print(f"[yellow][*] Skipping ZIP path traversal attempt: {member}[/yellow]")
                            continue
                        
                        safe_members.append(member)
                    
                    # Extract only safe members
                    for member in safe_members:
                        try:
                            zip_ref.extract(member, extract_to)
                        except Exception as e:
                            self.console.print(f"[yellow][*] Error extracting {member}: {str(e)}[/yellow]")
            except Exception as e:
                self.console.print(f"[red][*] Error processing ZIP archive: {str(e)}[/red]")

        def extract_rar(rar_path, extract_to):
            try:
                with rarfile.RarFile(rar_path, 'r') as rar_ref:
                    # Get list of members to check for safety
                    members = rar_ref.namelist()
                    safe_members = []
                    
                    # Check each member for safety
                    for member in members:
                        if os.path.isabs(member) or '..' in member:
                            self.console.print(f"[yellow][*] Skipping potentially unsafe RAR entry: {member}[/yellow]")
                            continue
                        
                        # Validate extraction path
                        target_path = os.path.join(extract_to, member)
                        if not is_within_directory(extract_to, target_path):
                            self.console.print(f"[yellow][*] Skipping RAR path traversal attempt: {member}[/yellow]")
                            continue
                        
                        safe_members.append(member)
                    
                    # Extract only safe members
                    for member in safe_members:
                        try:
                            rar_ref.extract(member, extract_to)
                        except Exception as e:
                            self.console.print(f"[yellow][*] Error extracting {member}: {str(e)}[/yellow]")
            except Exception as e:
                self.console.print(f"[red][*] Error processing RAR archive: {str(e)}[/red]")

        def extract_7z(sevenz_path, extract_to):
            try:
                with py7zr.SevenZipFile(sevenz_path, mode='r') as sevenz_ref:
                    # py7zr doesn't support extracting individual files easily
                    # so we'll iterate over the members and extract them
                    archive_members = sevenz_ref.getnames()
                    safe_members = []
                    
                    # Check each member for safety
                    for member in archive_members:
                        if os.path.isabs(member) or '..' in member:
                            self.console.print(f"[yellow][*] Skipping potentially unsafe 7z entry: {member}[/yellow]")
                            continue
                        
                        # Validate extraction path
                        target_path = os.path.join(extract_to, member)
                        if not is_within_directory(extract_to, target_path):
                            self.console.print(f"[yellow][*] Skipping 7z path traversal attempt: {member}[/yellow]")
                            continue
                        
                        safe_members.append(member)
                    
                    # Extract only safe members if possible, otherwise all
                    try:
                        if safe_members:
                            # Check if all members are safe
                            if len(safe_members) == len(archive_members):
                                sevenz_ref.extractall(extract_to)
                            else:
                                # Extract only safe members (if the library supports it)
                                try:
                                    sevenz_ref.extract(extract_to, safe_members)
                                except:
                                    self.console.print("[yellow][*] Cannot extract selective members, extracting all 7z contents with caution[/yellow]")
                                    sevenz_ref.extractall(extract_to)
                    except Exception as e:
                        self.console.print(f"[red][*] Error extracting 7z: {str(e)}[/red]")
            except Exception as e:
                self.console.print(f"[red][*] Error processing 7z archive: {str(e)}[/red]")

        def extract_tar(tar_path, extract_to):
            try:
                with tarfile.open(tar_path, 'r:*') as tar_ref:
                    # Security check
                    members = tar_ref.getmembers()
                    safe_members = []
                    
                    for member in members:
                        if member.isdev():  # Skip device files
                            self.console.print(f"[yellow][*] Skipping device file in TAR: {member.name}[/yellow]")
                            continue
                            
                        if member.name.startswith('/') or '..' in member.name:
                            self.console.print(f"[yellow][*] Skipping potentially unsafe TAR entry: {member.name}[/yellow]")
                            continue
                            
                        # Validate extraction path
                        target_path = os.path.join(extract_to, member.name)
                        if not is_within_directory(extract_to, target_path):
                            self.console.print(f"[yellow][*] Skipping TAR path traversal attempt: {member.name}[/yellow]")
                            continue
                            
                        safe_members.append(member)
                    
                    # Extract only safe members
                    for member in safe_members:
                        try:
                            tar_ref.extract(member, extract_to)
                        except Exception as e:
                            self.console.print(f"[yellow][*] Error extracting {member.name}: {str(e)}[/yellow]")
            except Exception as e:
                self.console.print(f"[red][*] Error processing TAR archive: {str(e)}[/red]")

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

