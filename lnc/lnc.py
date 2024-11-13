import argparse
import json
import yaml
from rich.console import Console
from lnc.multi.multi_thread_manager import MultiThreadManager
from lnc.multi.generator import *
from os.path import exists
import shutil
import warnings
warnings.filterwarnings('ignore', category=SyntaxWarning)

console=Console()

default_values={
    "username": None,
    "password": None,
    "domain": None,
    "enable_error_output": False,
    "output_end": None,
    "output": "output",
    "disable_output_json": False,
    "disable_output_text": False,
    "write_errors_to_file": False,
    "disable_error_output": False,
    "max_parallel_job": 5,
    "retry_count": 3,
    "delay_before_retry": 0.1,
    "smb_port": 445,
    "smb_shares_check_read": True,
    "smb_shares_check_write": True,
    "smb_files_ignore_shares": [
        "ipc$",
        "print$"
    ],
    "always_download": [
        r"\.config$",
        r"\.ini$",
        r"\.dll$",
        r"\.metadata$",
        r"\.db$",
        r"\.rsc$"
    ],
    "download_folder": "./downloads/",
    "max_download_size": 10,
    "patterns": {
        "password": [
            "password",
            "pwd=",
            "şifre",
            "parola",
            "sifre",
            "contentHash"
        ],
        "TCKN":[
            "[1-9][0-9]{10}", 
        ],
        "credit_card": [  
            r"4[0-9]{12}(?:[0-9]{3})?", 
            r"5[1-5][0-9]{14}", 
            r"6(?:011|5[0-9]{2})[0-9]{12}", 
            r"3[47][0-9]{13}", 
            r"3(?:0[0-5]|[68][0-9])[0-9]{11}", 
            r"(?:2131|1800|35\d{3})\d{11}"
        ]
    },
    "add-filename-to-analyze": True,
    "check_binarys": True,
    "take_before": 50,
    "take_after": 50,
    "thread": 10,
    "timeout": 0.1,
    "disable_output_end_prefix": False,
    "ignore_folder_name_contains": ["audio", "bin", "boot", "dev", "etc", "lib", "lib64", "lost+found", "media", "opt", "proc", "run", "sbin", "srv", "sys", "tmp", "usr", "snap", "swapfile", "vmlinuz"],
    "ftp_port": 21
}

def parse_args():
    def load_config(config_path):
        try:
            with open(config_path, 'r') as file:
                config_data = file.read()
                config = yaml.safe_load(config_data)
            return config
        except Exception as e:
            console.print(f'[red]Error:[/red] {e}')
            exit(1)
    def merge_configs(defaults, config, args):
        merged = defaults.copy()
        if config:
            merged.update(config)
        for key, value in vars(args).items():
            if value is not None:
                merged[key] = value
        return merged
    def add_authentication_args(parser):
        auth_group = parser.add_argument_group('Authentication')
        auth_group.add_argument('-u', '--username', type=str, help='Username for authentication')
        auth_group.add_argument('-p', '--password', type=str, help='Password for authentication')
        auth_group.add_argument('-d', '--domain', type=str, help='Domain for authentication')
        return auth_group
    def add_connection_args(parser, parallel:bool=True):
        connection_group = parser.add_argument_group('Connection settings')
        connection_group.add_argument('--retry', type=int, dest='retry_count', help='Number of retry attempts')
        connection_group.add_argument('--delay', type=float, dest='delay_before_retry', help='Delay in seconds before retrying')
        connection_group.add_argument('--timeout', type=float, help='Connection timeout in seconds')
        if parallel:
            connection_group.add_argument('--max-jobs', type=int, dest='max_parallel_job', help='Maximum number of parallel jobs')
        return connection_group
    def add_thread_args(parser):
        operation_group = parser.add_argument_group('Operation settings')
        operation_group.add_argument('-w', '--threads', type=int, dest='thread', help='Number of threads to use')
        return operation_group
    def add_settings_args(parser):
        setting_group = parser.add_argument_group('Settings')
        setting_group.add_argument('-c', '--config', type=str, help='Path to the configuration file')
        setting_group.add_argument('-o', '--output', type=str, help='Name of the output file')
        setting_group.add_argument('--no-text-output', action='store_true', dest='disable_output_text', help='Disable text output')
        setting_group.add_argument('--enable-error-output', action='store_true', help='Enable error output')
        setting_group.add_argument('--enable-end-prefix', action='store_false', dest='disable_output_end_prefix', help='Disable output end prefix')
        setting_group.add_argument('--log-errors', action='store_true', dest='write_errors_to_file', help='Write errors to a log file')
        return setting_group
    def add_download_settings_args(parser):
        parser.add_argument('--download_folder', type=str, help='Folder to download files')
    def add_target_args(parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('-t', '--target', type=str, help='Target IP')
        group.add_argument('-tf', '--targets_file', type=str, help='Targets file')
        return group
    def add_smb_share_target_args(parser):
        return add_target_args(parser)
    def add_smb_crawl_target_args(parser):
        group = add_target_args(parser)
        group.add_argument('-f', '--shares_file', type=str, help='Shares json file')
        return group
    def add_ftp_download_target_args(parser):
        group = add_target_args(parser)
        group.add_argument('-f', '--files_file', type=str, help='Files json file')
        return group
    def add_smb_download_target_args(parser):
        group = add_target_args(parser)
        group.add_argument('-f', '--files_file', type=str, help='Files json file')
        return group
    def add_filter_group(parser):
        filter_group = parser.add_argument_group('Filter settings')
        return filter_group
    def add_download_filter_args(parser):
        parser.add_argument('--ignore_folder_name_contains', type=str, nargs='+', help='Ignore folders that contains. Usage: --ignore_folder_name_contains audio bin boot ...')
        return parser
    def add_smb_shares_filter_args(parser):
        parser.add_argument('--ignore_shares', dest='smb_files_ignore_shares', type=str, nargs='+', help='Shares to ignore when listing files. Usage: --ignore_shares ipc$ print$ ...')
    def add_download_always_args(parser):
        parser.add_argument('--always_download', type=str, nargs='+', help=r'Always download files with regex. Usage: --always_download \.txt$ \.docx$ ...')
        parser.add_argument('--max_download_size', type=int, help='Max file size to download in bytes')
    def add_smb_args(parser):
        parser.add_argument('--port', dest="smb_port", type=int, help='SMB Port')
    
    def add_ftp_args(parser):
        parser.add_argument('--port', dest="ftp_port", type=int, help='FTP Port')

    def add_analyze_args(parser):
        analyze_group = parser.add_argument_group('Analyze settings')
        analyze_group.add_argument('--take_after',dest="take-after", type=int, help='Take after match')
        analyze_group.add_argument('--take_before',dest="take-before", type=int, help='Take before match')
        analyze_group.add_argument('--patterns', type=str, help='JSON string of patterns')
        analyze_group.add_argument('--add_filename_to_analyze', dest='add-filename-to-analyze', action='store_true', help='Add filename to analyze')
        analyze_group.add_argument('--always_keep_extracted_files', dest='always-keep-extracted-files', action='store_true', help='Always keep extracted files')
        analyze_group.add_argument('--keep_extracted_files', dest='keep-extracted-files', action='store_true', help='Keep if match found')
        

    parser = argparse.ArgumentParser(
        description="LNC - Locale Network Crawler",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', help='Sub-command help', required=True)
    

    smb_parser = subparsers.add_parser('smb', help='SMB help')

    smb_subparsers = smb_parser.add_subparsers(dest='smb_command', help='SMB Sub-command help', required=True)

    smb_shares_parser = smb_subparsers.add_parser('share', help='List Shares')
    add_smb_share_target_args(smb_shares_parser)
    add_authentication_args(smb_shares_parser)
    add_connection_args(smb_shares_parser)
    add_thread_args(smb_shares_parser)
    add_settings_args(smb_shares_parser)
    add_smb_args(smb_shares_parser)


    smb_crawl_parser = smb_subparsers.add_parser('crawl', help='Crawl Shares')
    add_smb_crawl_target_args(smb_crawl_parser)
    add_authentication_args(smb_crawl_parser)
    add_connection_args(smb_crawl_parser)
    add_thread_args(smb_crawl_parser)
    add_settings_args(smb_crawl_parser)
    add_smb_args(smb_crawl_parser)
    shares_filter_group = add_filter_group(smb_crawl_parser)
    add_download_filter_args(shares_filter_group)
    add_smb_shares_filter_args(shares_filter_group)


    smb_download_parser = smb_subparsers.add_parser('download', help='Download Files')
    add_smb_download_target_args(smb_download_parser)
    add_authentication_args(smb_download_parser)
    add_connection_args(smb_download_parser)
    add_thread_args(smb_download_parser)
    download_settings_group = add_settings_args(smb_download_parser)
    add_download_settings_args(download_settings_group)
    add_smb_args(smb_download_parser)
    download_filter_group = add_filter_group(smb_download_parser)
    add_download_filter_args(download_filter_group)
    add_smb_shares_filter_args(download_filter_group)
    add_download_always_args(download_filter_group)


    smb_analyze_parser = smb_subparsers.add_parser('analyze', help='Analyze Files')
    add_smb_download_target_args(smb_analyze_parser)
    add_authentication_args(smb_analyze_parser)
    add_connection_args(smb_analyze_parser)
    add_thread_args(smb_analyze_parser)
    analyze_download_settings_group = add_settings_args(smb_analyze_parser)
    add_download_settings_args(analyze_download_settings_group)
    add_smb_args(smb_analyze_parser)
    analyze_download_filter_group = add_filter_group(smb_analyze_parser)
    add_download_filter_args(analyze_download_filter_group)
    add_smb_shares_filter_args(analyze_download_filter_group)
    add_download_always_args(analyze_download_filter_group)
    add_analyze_args(smb_analyze_parser)


    ftp_parser = subparsers.add_parser('ftp', help='FTP help')
    ftp_subparsers = ftp_parser.add_subparsers(dest='ftp_command', help='FTP FTP-command help', required=True)


    ftp_crawl_parser = ftp_subparsers.add_parser('crawl', help='Crawl FTP')
    add_target_args(ftp_crawl_parser)
    add_authentication_args(ftp_crawl_parser)
    add_connection_args(ftp_crawl_parser)
    add_thread_args(ftp_crawl_parser)
    add_settings_args(ftp_crawl_parser)
    add_ftp_args(ftp_crawl_parser)
    ftp_crawl_filter_group = add_filter_group(ftp_crawl_parser)
    add_download_filter_args(ftp_crawl_filter_group)


    ftp_download_parser = ftp_subparsers.add_parser('download', help='Download FTP')
    add_ftp_download_target_args(ftp_download_parser)
    add_authentication_args(ftp_download_parser)
    add_connection_args(ftp_download_parser)
    add_thread_args(ftp_download_parser)
    add_settings_args(ftp_download_parser)
    add_ftp_args(ftp_download_parser)
    ftp_download_filter_group = add_filter_group(ftp_download_parser)
    add_download_filter_args(ftp_download_filter_group)
    add_download_always_args(ftp_download_filter_group)


    ftp_analyze_parser = ftp_subparsers.add_parser('analyze', help='Analyze FTP')
    add_ftp_download_target_args(ftp_analyze_parser)
    add_authentication_args(ftp_analyze_parser)
    add_connection_args(ftp_analyze_parser)
    add_thread_args(ftp_analyze_parser)
    add_settings_args(ftp_analyze_parser)
    add_ftp_args(ftp_analyze_parser)
    ftp_analyze_filter_group = add_filter_group(ftp_analyze_parser)
    add_download_filter_args(ftp_analyze_filter_group)
    add_download_always_args(ftp_analyze_filter_group)
    add_analyze_args(ftp_analyze_parser)
    
    
    analyze_parser = subparsers.add_parser('analyze', help='Analyze help')
    analyze_parser.add_argument('-f', '--file', type=str, help='File or Folder path',required=True)
    add_analyze_args(analyze_parser)
    add_settings_args(analyze_parser)
    add_thread_args(analyze_parser)

    args = parser.parse_args()
    config = {}
    if args.config:
        config = load_config(args.config)
    merged_config = merge_configs(default_values, config, args)
    merged_config['max_connection_to_host'] = merged_config['max_parallel_job']
    merged_config['output_end'] = str(uuid4())
    return merged_config

def smb_shares_list(config:dict):
    from lnc.multi.SMB.smb_shares import Handler as SMB_Shares_Handler
    data_generator = None
    total=0
    if 'target' in config:
        data_generator,total=single_data_generaor(data=config['target'],console=console)
    elif config['targets_file']:
        data_generator,total=text_generator(file_path=config['targets_file'],console=console)
    
    manager=MultiThreadManager("SMB Shares Listing",console=console,datas=data_generator,handler=SMB_Shares_Handler,thread_count=config['thread'],max_parallel_generators=1, total_data=total,config=config,custom_columns=[{"name": "Found", "color": "cyan"}])
    manager.start()
    

def smb_files_crawl(config:dict):
    from lnc.multi.SMB.smb_files import Handler as SMB_Files_Handler
    if 'targets_file' in config or 'target' in config:
        smb_shares_list(config=config)
        from lnc.modules.crawl.SMB.shares.config import OUTPUT_FILE_NAME_PREFIX
        if config['disable_output_end_prefix']:
            config['shares_file'] = f"{config['output']}{OUTPUT_FILE_NAME_PREFIX}.json"
        else:
            config['shares_file'] = f"{config['output']}{OUTPUT_FILE_NAME_PREFIX}_{config['output_end']}.json"
    if not exists(config['shares_file']):
        console.print(f"[green][+] No shares found![/green]")
        exit(0)
    data_generator, total, uid = json_generator(file_path=config['shares_file'],console=console)
    manager = MultiThreadManager("SMB Files Crawling", console=console, datas=data_generator, handler=SMB_Files_Handler, thread_count=config['thread'], max_parallel_generators=config['max_parallel_job'], total_data=total, config=config, custom_columns=[{"name": "Found", "color": "cyan"}],before_force_stop=(clear_temp_files, {'uid': uid}))
    manager.start()

def smb_files_download(config:dict):
    from lnc.multi.SMB.smb_download import Handler as SMB_Download_Handler, Filter
    if 'targets_file' in config or 'target' in config:
        smb_files_crawl(config=config)
        from lnc.modules.crawl.SMB.files.config import OUTPUT_FILE_NAME_PREFIX
        if config['disable_output_end_prefix']:
            config['files_file'] = f"{config['output']}{OUTPUT_FILE_NAME_PREFIX}.json"
        else:
            config['files_file'] = f"{config['output']}{OUTPUT_FILE_NAME_PREFIX}_{config['output_end']}.json"
    if not exists(config['files_file']):
        console.print("[green][+] No file found![/green]")
        exit(0)
    filter = Filter(config_dict=config)
    data_generator, total, uid = json_generator(file_path=config['files_file'], console=console,filter=filter)
    manager = MultiThreadManager("SMB Files Download", console=console, datas=data_generator, handler=SMB_Download_Handler, thread_count=config['thread'], max_parallel_generators=config['max_parallel_job'], total_data=total, config=config, before_force_stop=(clear_temp_files, {'uid': uid}))
    manager.start()

def smb_files_analyze(config:dict):
    from lnc.multi.SMB.smb_analyze import Handler as SMB_Analyze_Handler
    if 'targets_file' in config or 'target' in config:
        smb_files_crawl(config=config)
        from lnc.modules.crawl.SMB.files.config import OUTPUT_FILE_NAME_PREFIX
        if config['disable_output_end_prefix']:
            config['files_file'] = f"{config['output']}{OUTPUT_FILE_NAME_PREFIX}.json"
        else:
            config['files_file'] = f"{config['output']}{OUTPUT_FILE_NAME_PREFIX}_{config['output_end']}.json"
    if not exists(config['files_file']):
        console.print("[green][+] No file found![/green]")
        exit(0)
    data_generator, total, uid = json_generator(file_path=config['files_file'], console=console)
    
    custom_columns=[]   
    for pattern in config['patterns']:
        custom_columns.append({"name": pattern.capitalize(), "color": "cyan"})
    manager = MultiThreadManager("SMB Files Analyze", console=console, datas=data_generator, handler=SMB_Analyze_Handler, thread_count=config['thread'], max_parallel_generators=config['max_parallel_job'], total_data=total, config=config,custom_columns=custom_columns, before_force_stop=(clear_temp_files, {'uid': uid}))
    manager.start()


def ftp_files_crawl(config:dict):
    from lnc.multi.FTP.ftp_files import Handler as FTP_Files_Handler
    data_generaor = None
    total=0

    if 'target' in config:
        data_generaor,total=single_data_generaor(data=config['target'],console=console)
    elif config['targets_file']:
        data_generaor,total=text_generator(file_path=config['targets_file'],console=console)
    
    manager = MultiThreadManager(process_name="FTP Files Crawling", console=console, datas=data_generaor, handler=FTP_Files_Handler, thread_count=config['thread'], max_parallel_generators=1, total_data=total, config=config, custom_columns=[{"name": "Found", "color": "cyan"}])
    manager.start()

def ftp_files_download(config:dict):
    from lnc.multi.FTP.ftp_download import Handler as FTP_Download_Handler, Filter
    if 'targets_file' in config or 'target' in config:
        ftp_files_crawl(config=config)
        from lnc.modules.crawl.FTP.config import OUTPUT_FILE_NAME_PREFIX
        if config['disable_output_end_prefix']:
            config['files_file'] = f"{config['output']}{OUTPUT_FILE_NAME_PREFIX}.json"
        else:
            config['files_file'] = f"{config['output']}{OUTPUT_FILE_NAME_PREFIX}_{config['output_end']}.json"
    if not exists(config['files_file']):
        console.print("[green][+] No file found![/green]")
        exit(0)
    filter = Filter(config_dict=config)
    data_generator, total, uid = json_generator(file_path=config['files_file'], console=console,filter=filter)
    manager = MultiThreadManager("FTP Files Download", console=console, datas=data_generator, handler=FTP_Download_Handler, thread_count=config['thread'], max_parallel_generators=config['max_parallel_job'], total_data=total, config=config, before_force_stop=(clear_temp_files, {'uid': uid}))
    manager.start()

def ftp_files_analyze(config:dict):
    from lnc.multi.FTP.ftp_analyze import Handler as FTP_Analyze_Handler
    if 'targets_file' in config or 'target' in config:
        ftp_files_crawl(config=config)
        from lnc.modules.crawl.FTP.config import OUTPUT_FILE_NAME_PREFIX
        if config['disable_output_end_prefix']:
            config['files_file'] = f"{config['output']}{OUTPUT_FILE_NAME_PREFIX}.json"
        else:
            config['files_file'] = f"{config['output']}{OUTPUT_FILE_NAME_PREFIX}_{config['output_end']}.json"
    if not exists(config['files_file']):
        console.print("[green][+] No file found![/green]")
        exit(0)
    data_generator, total, uid = json_generator(file_path=config['files_file'], console=console)
    
    custom_columns=[]   
    for pattern in config['patterns']:
        custom_columns.append({"name": pattern.capitalize(), "color": "cyan"})
    manager = MultiThreadManager("FTP Files Analyze", console=console, datas=data_generator, handler=FTP_Analyze_Handler, thread_count=config['thread'], max_parallel_generators=config['max_parallel_job'], total_data=total, config=config,custom_columns=custom_columns, before_force_stop=(clear_temp_files, {'uid': uid}))
    manager.start()

def analyze_folder(config:dict):
    from lnc.multi.analyze import Handler as Analyze_Handler

    from lnc.modules.download.file import File
    import os
    import glob

    file_path = config['file']
    data_generator=None
    if os.path.isdir(file_path):
        all_files = glob.glob(os.path.join(file_path, '**'), recursive=True)
        all_files = [File.from_dict({"local_path":f,"target":None,"port":None,"protocol":None,"url":f,"size":os.path.getsize(f),"path":f}) for f in all_files if os.path.isfile(f)] 
        data_generator, total = list_data_generator(data_list=all_files,console=console)
        
    elif os.path.isfile(file_path):
        data_generator, total = list_data_generator(data_list=[File.from_dict({"local_path":file_path,"target":None,"port":None,"protocol":None,"url":file_path,"size":os.path.getsize(file_path),"path":file_path})],console=console)
    else:
        console.print(f"[red]Error:[/red] {file_path} is not found.")
        exit(1)
    custom_columns=[]   
    for pattern in config['patterns']:
        custom_columns.append({"name": pattern.capitalize(), "color": "cyan"})
    
        manager = MultiThreadManager("Analyze Files", console=console, datas=data_generator, handler=Analyze_Handler, thread_count=config['thread'], max_parallel_generators=1, total_data=total, config=config, custom_columns=custom_columns)
    manager.start()

def print_banner():
    print(r"""
    __    _   ________
   / /   / | / / ____/
  / /   /  |/ / /     
 / /___/ /|  / /___   
/_____/_/ |_/\\____/     v1.0.0

        https://github.com/WhileEndless/LNC
    """)


def main():
    print_banner()
    config=parse_args()
    if config['command']=='smb':
        if config['smb_command']=='share':
            smb_shares_list(config=config)
        elif config['smb_command']=='crawl':
            smb_files_crawl(config=config)
        elif config['smb_command']=='download':
            smb_files_download(config=config)
        elif config['smb_command']=='analyze':
            smb_files_analyze(config=config)
    elif config['command']=='ftp':
        if config['ftp_command']=='crawl':
            ftp_files_crawl(config=config)
        elif config['ftp_command']=='download':
            ftp_files_download(config=config)
        elif config['ftp_command']=='analyze':
            ftp_files_analyze(config=config)
    elif config['command']=='analyze':
        analyze_folder(config=config)
    console.print("[green][+] Done![/green]")

if __name__ == '__main__':
    main()
