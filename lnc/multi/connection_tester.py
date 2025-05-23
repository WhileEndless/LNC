"""
Connection Tester Module

Provides protocol-specific connection testing for network accessibility checks.
"""

from typing import Optional, Tuple
from dataclasses import dataclass
import socket
from ftplib import FTP
from impacket.smbconnection import SMBConnection
from time import sleep


@dataclass
class ConnectionInfo:
    """Connection information for testing"""
    target: str
    port: int
    protocol: str  # 'smb', 'ftp'
    username: Optional[str] = None
    password: Optional[str] = None
    domain: Optional[str] = None
    lmhash: Optional[str] = None
    nthash: Optional[str] = None
    timeout: int = 5


class ConnectionTester:
    """Test connections for different protocols"""
    
    @staticmethod
    def test_connection(conn_info: ConnectionInfo) -> Tuple[bool, str]:
        """
        Test connection based on protocol type
        
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        if conn_info.protocol == 'smb':
            return ConnectionTester._test_smb(conn_info)
        elif conn_info.protocol == 'ftp':
            return ConnectionTester._test_ftp(conn_info)
        else:
            return ConnectionTester._test_tcp(conn_info)
    
    @staticmethod
    def _test_tcp(conn_info: ConnectionInfo) -> Tuple[bool, str]:
        """Basic TCP port test"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(conn_info.timeout)
        try:
            sock.connect((conn_info.target, conn_info.port))
            return True, ""
        except socket.timeout:
            return False, "Connection timeout"
        except socket.error as e:
            return False, f"Socket error: {str(e)}"
        finally:
            sock.close()
    
    @staticmethod
    def _test_smb(conn_info: ConnectionInfo) -> Tuple[bool, str]:
        """Test SMB connection with authentication"""
        try:
            # First test TCP port
            tcp_ok, tcp_err = ConnectionTester._test_tcp(conn_info)
            if not tcp_ok:
                return False, tcp_err
            
            # Then test SMB connection
            conn = SMBConnection(
                conn_info.target,
                conn_info.target,
                sess_port=conn_info.port,
                timeout=conn_info.timeout
            )
            
            # Test authentication
            username = conn_info.username or ''
            password = conn_info.password or ''
            domain = conn_info.domain or ''
            lmhash = conn_info.lmhash or ''
            nthash = conn_info.nthash or ''
            
            # Use hash authentication if provided
            if lmhash or nthash:
                if conn.login(username, '', domain, lmhash, nthash):
                    conn.logoff()
                    return True, ""
                else:
                    return False, "SMB hash authentication failed"
            else:
                if conn.login(username, password, domain):
                    conn.logoff()
                    return True, ""
                else:
                    return False, "SMB authentication failed"
                
        except Exception as e:
            return False, f"SMB error: {str(e)}"
    
    @staticmethod
    def _test_ftp(conn_info: ConnectionInfo) -> Tuple[bool, str]:
        """Test FTP connection with authentication"""
        try:
            # First test TCP port
            tcp_ok, tcp_err = ConnectionTester._test_tcp(conn_info)
            if not tcp_ok:
                return False, tcp_err
            
            # Then test FTP connection
            ftp = FTP()
            ftp.timeout = conn_info.timeout
            ftp.connect(conn_info.target, conn_info.port)
            
            # Test authentication
            username = conn_info.username or 'anonymous'
            password = conn_info.password or 'anonymous@'
            
            ftp.login(username, password)
            ftp.quit()
            return True, ""
            
        except Exception as e:
            return False, f"FTP error: {str(e)}"