from lnc.modules.base.module import Module as ModuleBase
from lnc.modules.base.network.base.config import Config
from threading import Lock
from uuid import uuid4
from time import sleep
from queue import Queue
from rich.console import Console
import socket


class Network_Module(ModuleBase):
    config: Config = None
    active_connections={}
    active_connections_lock = Lock()
    target:str=None
    connection_id:str = None

    def __init__(self, config: Config, console:Console, target:str) -> None:
        super().__init__(config, console)
        self.target=target
        self.connection_id = str(uuid4())
    def check_access(self,target:str) -> bool:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.config.timeout)
        try:
            sock.connect((target, self.config.port))
        except (socket.timeout, socket.error):
            return False
        finally:
            sock.close()
        return True

    def connect(self) -> bool:
        with Network_Module.active_connections_lock:
            if self.target not in Network_Module.active_connections:
                Network_Module.active_connections[self.target] = {}

            if self.config.port not in Network_Module.active_connections[self.target]:
                Network_Module.active_connections[self.target][self.config.port] = {"q": Queue(maxsize=self.config.max_connection_to_host), "connection_ids": []}

            if self.connection_id not in Network_Module.active_connections[self.target][self.config.port]["connection_ids"]:
                if not Network_Module.active_connections[self.target][self.config.port]["q"].full():
                    Network_Module.active_connections[self.target][self.config.port]["q"].put(1)
                    Network_Module.active_connections[self.target][self.config.port]["connection_ids"].append(self.connection_id)
                    return True
                else:
                    pass
        
    def close(self):
        with Network_Module.active_connections_lock:
            if self.target in Network_Module.active_connections and self.config.port in Network_Module.active_connections[self.target]:
                if self.connection_id in Network_Module.active_connections[self.target][self.config.port]["connection_ids"]:
                    Network_Module.active_connections[self.target][self.config.port]["q"].get()
                    Network_Module.active_connections[self.target][self.config.port]["connection_ids"].remove(self.connection_id)
                    if Network_Module.active_connections[self.target][self.config.port]["q"].empty():
                        del Network_Module.active_connections[self.target][self.config.port]
                        if not Network_Module.active_connections[self.target]:
                            del Network_Module.active_connections[self.target]