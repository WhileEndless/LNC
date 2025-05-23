from typing import Generator, Type, List, Dict,Tuple
from queue import Queue, Empty
from threading import Event, Thread, Lock
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from signal import signal, SIGINT
from rich.console import Console
from os import _exit
from rich.prompt import Prompt
from rich.live import Live
from lnc.multi.base.handler import Handler
from lnc.multi.accessibility_manager import AccessibilityManager
from time import time

class MultiThreadManagerError(Exception):
    """Base class for MultiThreadManager exceptions."""
    pass

class QueueFillingError(MultiThreadManagerError):
    """Raised when there's an error filling the queues."""
    pass

class WorkerProcessingError(MultiThreadManagerError):
    """Raised when there's an error in worker processing."""
    pass

class MultiThreadManager:
    """
    A class to manage multi-threaded processing.

    This class handles the orchestration of multiple threads for data processing,
    including queue management, progress tracking, and graceful interruption handling.
    """

    def __init__(self, process_name: str, console: Console, datas: Generator, handler: Type[Handler],
                 thread_count: int, max_parallel_generators: int, total_data: int, config: dict,
                 custom_columns: List[Dict[str, str]] = None, before_force_stop:Tuple[object,Dict[str,object]]=None) -> None:
        """
        Initialize the MultiThreadManager.

        Args:
            process_name (str): Name of the process for display purposes.
            console (Console): Rich Console instance for output.
            datas (Generator): Generator providing data to be processed.
            handler (Type[Handler]): Handler class for processing data.
            thread_count (int): Number of worker threads to spawn.
            max_parallel_generators (int): Maximum number of parallel data generators.
            total_data (int): Total amount of data to be processed.
            config (dict): Configuration dictionary for the process.
            custom_columns (List[Dict[str, str]], optional): Custom columns for progress tracking. Defaults to None.
        """
        self.datas = datas
        self.datas_lock = Lock()
        self.current_progress_lock = Lock()
        self.console = console
        self.config = config
        self.handler = handler
        self.thread_count = thread_count
        self.max_parallel_generators = max_parallel_generators
        self.worker_queues = []
        self.filler_queues = {}
        self.filling_threads = []
        self.empty_quetes = []
        self.data_groups = []
        self.filler_queues_lock = Lock()
        self.threads = []
        self.stop_event = Event()
        self.total_data = total_data
        self.process_name = process_name
        self.interrupted = Event()
        self.live = None
        self.retry_thread = None
        self.retry_queue = Queue()
        
        # Initialize accessibility checker
        self.accessibility_checker = AccessibilityManager.initialize(config, console)
        
        # Set up crawl tracking if this is a crawl operation
        if self.accessibility_checker and 'crawl' in process_name.lower():
            import uuid
            operation_id = str(uuid.uuid4())
            self.accessibility_checker.set_crawl_tracking_file(operation_id)
        
        # Determine operation type from process name
        self.operation_type = self._determine_operation_type(process_name)
        
        # Initialize progress tracking variables
        self.current_progress = 0
        self.total_handled = 0
        self.custom_columns = custom_columns or []
        self.task = None
        self.total_stop_event = 0
        self.before_force_stop=before_force_stop
        
        # Initialize progress columns
        columns = [
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TextColumn("[{task.completed}/{task.total}]")
        ]
        
        for column in self.custom_columns:
            columns.append(TextColumn(f"[bold {column['color']}]{column['name']} " + "{task.fields[" + column['name'] + "]}"))

        columns.append(TextColumn("[red]{task.fields[stop_message]}"))

        self.progress = Progress(*columns)

        signal(SIGINT, self.signal_handler)
    
    def _determine_operation_type(self, process_name: str) -> str:
        """Determine the operation type from process name"""
        process_lower = process_name.lower()
        if 'share' in process_lower:
            return 'share_list'
        elif 'crawl' in process_lower:
            return 'file_crawl'
        elif 'download' in process_lower:
            return 'download'
        elif 'analyz' in process_lower:
            return 'analyze'
        else:
            return 'unknown'

    def signal_handler(self, signum, frame):
        """
        Handle SIGINT signal for graceful interruption.

        Args:
            signum: Signal number.
            frame: Current stack frame.
        """
        self.total_stop_event += 1
        if self.total_stop_event > 2:
            self.console.print("[red]Force stop request received. Cleaning up...[/red]")
            self.live.stop()
            
            # Clean up worker threads
            self.stop_event.set()
            for thread in self.threads:
                thread.join(timeout=1)
            
            # Clean up handlers
            try:
                for queue in self.worker_queues:
                    queue.put(None)
            except:
                pass
                
            if self.before_force_stop:
                self.before_force_stop[0](**self.before_force_stop[1])
            _exit(0)
        self.console.print("\n[red]Stop request received. Waiting for the current process to complete...[/red]")
        self.interrupted.set()
        self.stop_event.set()
        self.progress.update(self.task, stop_message="Stopping...")
        for thread in self.threads:
            thread.join()
        if self.live:
            self.live.stop()
        self.confirm_exit()

    def confirm_exit(self):
        """
        Asks the user for confirmation to exit if the process is not yet complete.
        """
        if not self.current_progress >= self.total_data:
            self.total_stop_event += 1
            if self.total_stop_event > 2:
                self.console.print("[red]Force stop request received. Exiting...[/red]")
                self.live.stop()
                if self.before_force_stop:
                    self.before_force_stop[0](**self.before_force_stop[1])
                _exit(0)
            response = Prompt.ask("Are you sure you want to exit?", choices=["y", "n"], default="n")
            if response == "y":
                self.console.print("[red]Program is exiting...[/red]")
                self.live.stop()
                if self.before_force_stop:
                    self.before_force_stop[0](**self.before_force_stop[1])
                _exit(0)
            else:
                self.console.print("[green]Processes are continuing...[/green]")
                self.interrupted.clear()
                self.stop_event.clear()
                self.total_stop_event = 0
                self.restart()

    def start_threads(self, restart: bool = False):
        """
        Starts the worker threads.
        """
        for i in range(self.thread_count):
            if restart:
                thread = Thread(target=self.worker, args=(self.worker_queues[i],))
            else:
                queue = Queue(maxsize=self.thread_count * self.max_parallel_generators)
                thread = Thread(target=self.worker, args=(queue,))
                self.worker_queues.append(queue)
            thread.start()
            self.threads.append(thread)

    def allocate_filler_queues(self, filler_id):
        """
        Allocates queues to fillers ensuring each has enough queues to fill.

        Args:
            filler_id (int): ID of the filler.
        """
        with self.filler_queues_lock:
            if filler_id not in self.filler_queues:
                self.filler_queues[filler_id] = []
            while len(self.filler_queues[filler_id]) < self.max_parallel_generators and self.empty_quetes:
                self.filler_queues[filler_id].append(self.empty_quetes.pop(0))

    def fill_queues(self, filler_id: int):
        """
        Fills the queues with data from the generator.

        Args:
            filler_id (int): ID of the filler.
        """
        try:
            while not self.stop_event.is_set():
                if self.data_groups[filler_id] is None:
                    with self.datas_lock:
                        try:
                            self.data_groups[filler_id] = next(self.datas)
                        except StopIteration:
                            break
                for data in self.data_groups[filler_id]:
                    self.allocate_filler_queues(filler_id)
                    min_index = min(range(len(self.filler_queues[filler_id])), key=lambda i: self.filler_queues[filler_id][i].qsize())
                    self.filler_queues[filler_id][min_index].put(data)
                with self.filler_queues_lock:
                    self.empty_quetes.extend(self.filler_queues[filler_id])
                    del self.filler_queues[filler_id]
                self.data_groups[filler_id] = None
        except Exception as e:
            self.console.print(f"[red]Error in fill_queues: {e}[/red]")
            # Clean up filler resources on error
            with self.filler_queues_lock:
                if filler_id in self.filler_queues:
                    self.empty_quetes.extend(self.filler_queues[filler_id])
                    del self.filler_queues[filler_id]

    def start_filler_threads(self):
        """
        Starts the filler threads to fill the worker queues.
        """
        filler_count = int(self.thread_count / self.max_parallel_generators)
        if self.filling_threads == []:
            for i in range(filler_count):
                self.filler_queues[i] = []
            for i in range(self.thread_count):
                self.empty_quetes.append(self.worker_queues[i])
        self.filling_threads = []
        if self.thread_count % self.max_parallel_generators != 0:
            filler_count += 1
        for i in range(filler_count):
            if len(self.data_groups) < filler_count:
                self.data_groups.append(None)
            thread = Thread(target=self.fill_queues, args=(i,))
            thread.start()
            self.filling_threads.append(thread)

    def start(self):
        """
        Starts the entire multi-threaded processing workflow.
        """
        self.live = Live(self.progress, console=self.console, refresh_per_second=10)
        with self.live:
            self.initialize_task()
            self.start_threads()
            self.start_retry_thread()
            self.start_filler_threads()
            self.wait_for_filler_completion()
            self.wait_for_queue_completion()
            self.stop_event.set()
            for thread in self.threads:
                thread.join()
            if self.retry_thread:
                self.retry_thread.join()
        
        # Cleanup accessibility checker
        AccessibilityManager.cleanup()
        
        if self.before_force_stop:
            self.before_force_stop[0](**self.before_force_stop[1])
    def initialize_task(self):
        """
        Initializes the progress task for tracking.
        """
        task_fields = {
            "completed": self.current_progress,
            "total_handled": self.total_handled,
            "stop_message": ""
        }
        for column in self.custom_columns:
            task_fields[column["name"]] = 0
        
        self.task = self.progress.add_task(
            f"[green]{self.process_name}",
            total=self.total_data,
            **task_fields
        )

    def wait_for_filler_completion(self):
        """
        Waits for all filler threads to complete.
        """
        for thread in self.filling_threads:
            thread.join()

    def wait_for_queue_completion(self):
        """
        Waits for all worker queues to be empty.
        """
        for queue in self.worker_queues:
            queue.join()

    def worker(self, queue: Queue):
        """
        Worker method for processing data from the queue.

        Args:
            queue (Queue): Queue from which data is processed.
        """
        handler = None
        try:
            handler = self.handler(self.console, self.progress, self.task)
            while not self.stop_event.is_set() or not queue.empty():
                try:
                    # Check if we should pause due to network issues
                    if self.accessibility_checker:
                        self.accessibility_checker.wait_if_paused()
                    
                    data = queue.get(timeout=1)
                    
                    # For crawl operations, check if item was already processed
                    if self.accessibility_checker and 'crawl' in self.process_name.lower() and hasattr(data, 'id'):
                        if self.accessibility_checker.is_item_processed(str(data.id)):
                            queue.task_done()
                            continue
                    
                    handler_result = handler.run(data, self.config)
                    
                    # Update the total_handled value
                    with self.current_progress_lock:
                        # Only update if the result is valid (not None)
                        if handler_result is not None:
                            self.total_handled = handler_result
                        self.current_progress += 1  
                        
                        # Use only one method to update progress to avoid conflicts
                        # Don't use advance() and update() together
                        self.progress.update(
                            self.task, 
                            completed=self.current_progress,
                            refresh=True
                        )
                    
                    queue.task_done()
                    if self.interrupted.is_set():
                        break
                except Empty:
                    continue
                except Exception as e:
                    self.console.print(f"[red]Error processing data: {e}[/red]")
                    # Record network errors with failed item
                    if self.accessibility_checker and any(err in str(e).lower() for err in ['connection', 'timeout', 'network', 'refused']):
                        # Extract target info from data if available
                        target = None
                        port = None
                        if hasattr(data, 'target'):
                            target = data.target
                        elif isinstance(data, dict) and 'target' in data:
                            target = data['target']
                        
                        self.accessibility_checker.record_error(
                            failed_item=data,
                            operation_type=self.operation_type,
                            error_msg=str(e),
                            target=target,
                            port=port
                        )
                    queue.task_done()
                    # Don't re-raise the exception, continue processing
                    continue
        finally:
            if handler:
                try:
                    # Ensure handler is properly cleaned up
                    handler.clean_up() if hasattr(handler, 'clean_up') else None
                    del handler
                except Exception as cleanup_error:
                    self.console.print(f"[red]Error cleaning up handler: {cleanup_error}[/red]")
                    pass
    
    def start_retry_thread(self):
        """Start the retry thread that monitors for failed items to retry"""
        if self.accessibility_checker:
            self.retry_thread = Thread(target=self.retry_worker, daemon=True)
            self.retry_thread.start()
    
    def retry_worker(self):
        """Worker thread that handles retrying failed items"""
        while not self.stop_event.is_set():
            try:
                # Check if we're resumed from a pause
                if self.accessibility_checker and not self.accessibility_checker.is_paused:
                    failed_items = self.accessibility_checker.get_failed_items()
                    if failed_items:
                        self.console.print(f"[yellow][*] Processing {len(failed_items)} failed items for retry[/yellow]")
                        for item in failed_items:
                            # Distribute to appropriate worker queue
                            if self.worker_queues:
                                # Round-robin distribution
                                queue_idx = item.retry_count % len(self.worker_queues)
                                self.worker_queues[queue_idx].put(item.data)
                
                # Check every 5 seconds
                self.stop_event.wait(5)
            except Exception as e:
                self.console.print(f"[red]Error in retry worker: {e}[/red]")
    
    def restart(self):
        """
        Restarts the processing workflow after an interruption.
        """
        self.live = Live(self.progress, console=self.console, refresh_per_second=10)
        with self.live:
            # Preserve current progress state when restarting
            update_fields = {
                "completed": self.current_progress,
                "stop_message": ""
            }
            
            # Don't reset the custom column values - keep their current values
            # This way we preserve the progress between restarts
            # Only update if explicitly needed
            
            # Apply the updates
            self.progress.update(self.task, **update_fields, refresh=True)
            
            # Start/restart threads
            self.start_threads(restart=True)
            self.start_filler_threads()
            self.wait_for_queue_completion()
            self.stop_event.set()
            
            # Wait for all threads to complete
            for thread in self.threads:
                thread.join(timeout=5)  # Add timeout to prevent hanging