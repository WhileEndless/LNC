from json import loads, JSONDecodeError
from uuid import uuid4
from rich.console import Console
from typing import Tuple
from sys import exit
import ipaddress

def group_by_target(file_path,filter=None):
    uid=str(uuid4())
    file_names=[]
    total=0
    with open(file_path, 'r') as file:
        for line in file:
            try:
                data = loads(line.strip())
                if filter:
                    if not filter.check(data):
                        continue
                target = data.get('target')
                if target:
                    with open(f"._target_goroup_{target}_{uid}.json", 'a') as target_file:
                        target_file.write(line)
                    if f"._target_goroup_{target}_{uid}.json" not in file_names:
                        file_names.append(f"._target_goroup_{target}_{uid}.json")
                    total+=1
            except JSONDecodeError:
                print(f"Error decoding JSON: {line}")
    return file_names,total,uid

def json_generator(file_path:str,console:Console,filter=None) -> Tuple[object,int]:
    console.print(f"[yellow][*] Grouping by target...[/yellow]")
    file_names,total,uid=group_by_target(file_path, filter)
    console.print(f"[yellow][*] Grouping completed...[/yellow]")
    def generate_file_names():
        def generate_json_line(file_name):
            with open(file_name, 'r') as file:
                for line in file:
                    if line.strip() != "":
                        yield loads(line)
        for file_name in file_names:
            yield generate_json_line(file_name)
    return generate_file_names(),total,uid

def clear_temp_files(uid):
    from os import remove
    from glob import glob
    for file in glob(f".*_target_goroup_*_{uid}.json"):
        remove(file)

def ip_adress_generator(data:str):
    if "," in data:
        datas = data.split(",")
        try:
            for d in datas:
                for ip in ipaddress.ip_network(d):
                    yield str(ip)
            return
        except:
            for d in datas:
                yield d
            return
    try:
        for ip in ipaddress.ip_network(data):
            yield str(ip)
    except:
        yield data

def text_generator(file_path:str,console:Console) -> Tuple[object,int]:
    total=0
    try:
        with open(file_path, 'r') as file:
            for line in file:
                if line.strip() != "":
                    total += len(list(ip_adress_generator(line.strip())))
    except Exception as e:
        console.print(f'[red]Error:[/red] {e}')
        exit(1)
    def generate_file_names():
        def generate_text_line(data):
            yield data
        with open(file_path, 'r') as file:
            for line in file:
                if line.strip() != "":
                    try:
                        for ip in ip_adress_generator(line.strip()):
                            yield generate_text_line(str(ip))
                    except:
                        yield generate_text_line(line.strip())
    return generate_file_names(),total

def list_data_generator(data_list:list,console:Console) -> Tuple[object,int]:
    total=len(data_list)
    def generate_data():
        def generate_data_line(data):
            yield data
        for data in data_list:
            yield generate_data_line(data)
    return generate_data(),total

def single_data_generaor(data:str, console:Console) -> Tuple[object,int]:
    total=1
    if data==None:
        console.print(f'[red]Error:[/red] Target is empty')
        exit(1)
    total = len(list(ip_adress_generator(data)))
    def generate_single_data():
        def generate_single_line(data):
            yield str(data)
        for ip in ip_adress_generator(data):
            yield generate_single_line(ip)
    return generate_single_data(),total
