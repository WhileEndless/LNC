"""
Network Accessibility Checker Module

This module provides functionality to monitor network accessibility and automatically
pause/resume operations when network issues are detected.
"""

from threading import Lock, Event, Thread
from time import time, sleep
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass
from rich.console import Console
from rich.prompt import Confirm
import socket
from queue import Queue
import json
from datetime import datetime
from lnc.multi.connection_tester import ConnectionTester, ConnectionInfo


@dataclass
class FailedItem:
    """Information about a failed processing item"""
    data: Any              # The data to be processed
    operation_type: str    # 'share_list', 'file_crawl', 'download', 'analyze'
    retry_count: int = 0   # Number of retry attempts
    last_error: str = ""   # Last error message
    timestamp: float = 0   # Time of failure
    target: str = ""       # Target host for connection verification
    port: int = 0          # Port for connection verification


@dataclass
class SuccessfulConnection:
    """Stores information about a successful connection for later verification"""
    target: str
    port: int
    timestamp: float
    operation_type: str  # 'smb', 'ftp', etc.
    username: Optional[str] = None
    password: Optional[str] = None
    domain: Optional[str] = None


class AccessibilityChecker:
    """
    Monitors network accessibility and manages automatic pause/resume of operations
    """
    
    def __init__(self, config: Dict[str, Any], console: Console):
        self.config = config
        self.console = console
        
        # Configuration
        self.enabled = config.get('network_accessibility_check', True)
        self.auto_resume = config.get('auto_resume_on_recovery', True)
        self.error_threshold = config.get('error_threshold_for_check', 10)
        self.check_interval = config.get('accessibility_check_interval', 30)
        self.check_timeout = config.get('accessibility_check_timeout', 5)
        
        # State management
        self.error_count = 0
        self.error_count_lock = Lock()
        self.last_successful_connection: Optional[SuccessfulConnection] = None
        self.is_paused = False
        self.pause_event = Event()
        self.pause_event.set()  # Initially not paused
        self.stop_event = Event()
        
        # For crawl operations - track processed items to prevent duplicates
        self.processed_items_file = None
        self.processed_items = set()
        self.processed_items_lock = Lock()
        
        # Statistics
        self.total_errors = 0
        self.total_checks = 0
        self.total_pauses = 0
        
        # Failed items queue for retry
        self.failed_items = Queue()
        self.failed_items_lock = Lock()
    
    def set_crawl_tracking_file(self, operation_id: str):
        """Set up tracking file for crawl operations to prevent duplicates"""
        self.processed_items_file = f".lnc_crawl_tracking_{operation_id}.json"
        self._load_processed_items()
    
    def _load_processed_items(self):
        """Load previously processed items from tracking file"""
        try:
            with open(self.processed_items_file, 'r') as f:
                data = json.load(f)
                self.processed_items = set(data.get('processed_items', []))
        except (FileNotFoundError, json.JSONDecodeError):
            self.processed_items = set()
    
    def _save_processed_items(self):
        """Save processed items to tracking file"""
        if self.processed_items_file:
            with self.processed_items_lock:
                data = {
                    'processed_items': list(self.processed_items),
                    'last_updated': datetime.now().isoformat()
                }
                with open(self.processed_items_file, 'w') as f:
                    json.dump(data, f)
    
    def mark_item_processed(self, item_id: str):
        """Mark an item as processed (for crawl operations)"""
        with self.processed_items_lock:
            self.processed_items.add(item_id)
            if len(self.processed_items) % 10 == 0:  # Save every 10 items
                self._save_processed_items()
    
    def is_item_processed(self, item_id: str) -> bool:
        """Check if an item has already been processed"""
        with self.processed_items_lock:
            return item_id in self.processed_items
    
    def record_success(self, target: str, port: int, operation_type: str, 
                      username: str = None, password: str = None, domain: str = None):
        """Record a successful connection for later verification"""
        if not self.enabled:
            return
            
        self.last_successful_connection = SuccessfulConnection(
            target=target,
            port=port,
            timestamp=time(),
            operation_type=operation_type,
            username=username,
            password=password,
            domain=domain
        )
        
        # Reset error count on success
        with self.error_count_lock:
            if self.error_count > 0:
                self.console.print(f"[green][+] Network recovered, resetting error count[/green]")
            self.error_count = 0
    
    def record_error(self, failed_item=None, operation_type=None, error_msg="", target=None, port=None):
        """Record a network error and check if we should pause operations"""
        if not self.enabled:
            return
        
        # Store failed item for retry
        if failed_item is not None and operation_type:
            conn = self.last_successful_connection
            failed = FailedItem(
                data=failed_item,
                operation_type=operation_type,
                retry_count=0,
                last_error=str(error_msg),
                timestamp=time(),
                target=target or (conn.target if conn else ""),
                port=port or (conn.port if conn else 0)
            )
            with self.failed_items_lock:
                self.failed_items.put(failed)
            
        with self.error_count_lock:
            self.error_count += 1
            self.total_errors += 1
            
            if self.error_count >= self.error_threshold:
                self.console.print(f"[yellow][!] Error threshold reached ({self.error_count} errors)[/yellow]")
                # Start accessibility check in a separate thread
                Thread(target=self._check_accessibility, daemon=True).start()
    
    def _check_accessibility(self):
        """Check if the last successful connection is still accessible"""
        if not self.last_successful_connection:
            self.console.print("[red][!] No previous successful connection to verify[/red]")
            return
            
        self.total_checks += 1
        conn = self.last_successful_connection
        
        self.console.print(f"[yellow][*] Checking network accessibility to {conn.target}:{conn.port}...[/yellow]")
        
        if self._test_connection(conn.target, conn.port):
            self.console.print("[green][+] Network is accessible, continuing operations[/green]")
            with self.error_count_lock:
                self.error_count = 0
        else:
            self.console.print("[red][-] Network is not accessible[/red]")
            self._handle_network_failure()
    
    def _test_connection(self, target: str, port: int) -> bool:
        """Test if a connection can be established"""
        conn = self.last_successful_connection
        if not conn:
            # Fallback to basic TCP test
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.check_timeout)
            try:
                sock.connect((target, port))
                return True
            except (socket.timeout, socket.error):
                return False
            finally:
                sock.close()
        
        # Use protocol-specific test
        conn_info = ConnectionInfo(
            target=target,
            port=port,
            protocol=conn.operation_type,
            username=conn.username,
            password=conn.password,
            domain=conn.domain,
            timeout=self.check_timeout
        )
        
        success, error_msg = ConnectionTester.test_connection(conn_info)
        if not success:
            self.console.print(f"[red][-] Connection test failed: {error_msg}[/red]")
        return success
    
    def _handle_network_failure(self):
        """Handle network failure - pause operations and wait for recovery"""
        self.is_paused = True
        self.pause_event.clear()
        self.total_pauses += 1
        
        self.console.print("[red][!] Pausing all operations due to network failure[/red]")
        
        if self.auto_resume:
            self._auto_recovery_loop()
        else:
            self._manual_recovery_loop()
    
    def _auto_recovery_loop(self):
        """Automatically check for network recovery and resume"""
        conn = self.last_successful_connection
        
        while not self.stop_event.is_set():
            self.console.print(f"[yellow][*] Waiting {self.check_interval} seconds before next check...[/yellow]")
            
            if self.stop_event.wait(self.check_interval):
                break
                
            if self._test_connection(conn.target, conn.port):
                self.console.print("[green][+] Network recovered! Resuming operations...[/green]")
                self._resume_operations()
                break
            else:
                self.console.print(f"[red][-] Network still unavailable[/red]")
    
    def _manual_recovery_loop(self):
        """Manual recovery with user interaction"""
        conn = self.last_successful_connection
        
        while not self.stop_event.is_set():
            if Confirm.ask("[yellow]Network is down. Do you want to continue checking?[/yellow]"):
                if self._test_connection(conn.target, conn.port):
                    self.console.print("[green][+] Network recovered! Resuming operations...[/green]")
                    self._resume_operations()
                    break
                else:
                    self.console.print("[red][-] Network still unavailable[/red]")
            else:
                self.console.print("[red][!] Stopping all operations[/red]")
                self.stop_event.set()
                break
    
    def _resume_operations(self):
        """Resume paused operations"""
        self.is_paused = False
        self.pause_event.set()
        
        with self.error_count_lock:
            self.error_count = 0
        
        # Save any pending processed items
        if self.processed_items_file:
            self._save_processed_items()
    
    def get_failed_items(self) -> List[FailedItem]:
        """Get all failed items for retry"""
        items = []
        with self.failed_items_lock:
            while not self.failed_items.empty():
                items.append(self.failed_items.get())
        return items
    
    def requeue_failed_items(self, items: List[FailedItem]):
        """Put failed items back in the queue for retry"""
        with self.failed_items_lock:
            for item in items:
                item.retry_count += 1
                if item.retry_count <= 3:  # Max 3 retries
                    self.failed_items.put(item)
                else:
                    self.console.print(f"[red][-] Max retries exceeded for item: {item.operation_type}[/red]")
    
    def wait_if_paused(self):
        """Called by worker threads to wait if operations are paused"""
        self.pause_event.wait()
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_event.set()
        
        # Save final state
        if self.processed_items_file:
            self._save_processed_items()
        
        # Print statistics
        if self.enabled:
            self.console.print(f"\n[cyan]Accessibility Check Statistics:[/cyan]")
            self.console.print(f"  Total errors: {self.total_errors}")
            self.console.print(f"  Total checks: {self.total_checks}")
            self.console.print(f"  Total pauses: {self.total_pauses}")