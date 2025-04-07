import time
from typing import Optional
import logging


class RequestTimer:
    """
    Class to measure the time needed to process a request with improved readability.
    """

    def __init__(self) -> None:
        self._start_time: float = time.time()
        self._last_time_checked: float = self._start_time
        self._last_checkpoint: str = "Start"
        self._end_time: Optional[float] = None
        self._process_name: str = ""
        self.logger = logging.getLogger(__name__)

    def start(self, process_name: str):
        """Starts the timer for a specific process."""
        self._process_name = process_name
        self._start_time = time.time()
        self._last_time_checked = self._start_time
        self._last_checkpoint = "Start"
        self.logger.info(
            f"\n[Request Timer] Process '{self._process_name}' started at {self._format_time(self._start_time)}"
        )

    def checkpoint(self, checkpoint: str):
        """Logs a checkpoint with the elapsed time since the last checkpoint."""
        new_time = time.time()
        elapsed_since_last = new_time - self._last_time_checked
        self.logger.info(f"\n[Request Timer] Checkpoint: '{checkpoint}'")
        self.logger.info(
            f"   ├─ Time since last checkpoint ('{self._last_checkpoint}'): {elapsed_since_last:.4f} sec"
        )
        self._last_time_checked = new_time
        self._last_checkpoint = checkpoint

    def end(self):
        """Ends the timer and logs the total elapsed time."""
        self._end_time = time.time()
        total_elapsed = self._end_time - self._start_time
        elapsed_since_last = self._end_time - self._last_time_checked

        self.logger.info("\n[Request Timer] Process completed")
        self.logger.info(
            f"   ├─ Last checkpoint ('{self._last_checkpoint}') duration: {elapsed_since_last:.4f} sec"
        )
        self.logger.info(
            f"   └─ Total execution time for '{self._process_name}': {total_elapsed:.4f} sec"
        )

    @staticmethod
    def _format_time(timestamp: float) -> str:
        """Formats the given timestamp into a human-readable string."""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
