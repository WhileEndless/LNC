import os
import sys
import pytest
from rich.console import Console

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lnc.modules.base.network.SMB.config import Config
from lnc.modules.base.network.SMB.module import SMB_Module

class DummyConn:
    def __init__(self, *args, **kwargs):
        pass
    def login(self, *args, **kwargs):
        raise Exception(("Unpacked data doesn't match constant value 'b'jY]\\xf2'' should be ''þSMB''", "When unpacking field 'ProtocolID"))
    def logoff(self):
        pass
    def close(self):
        pass

@pytest.fixture
def module(monkeypatch):
    cfg = Config()
    console = Console()
    m = SMB_Module(cfg, console, target="127.0.0.1")
    monkeypatch.setattr(m, "check_access", lambda target: True)
    monkeypatch.setattr('lnc.modules.base.network.SMB.module.SMBConnection', DummyConn)
    errors = []
    monkeypatch.setattr(m, "write_error", lambda msg: errors.append(msg))
    return m, errors

def test_connect_handles_invalid_protocol_id(module):
    m, errors = module
    assert m.connect() is False
    assert any("Invalid SMB response" in e or "did not return a valid SMB header" in e for e in errors)
