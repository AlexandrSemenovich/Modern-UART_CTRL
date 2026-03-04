"""Background log export worker using QThread with mmap-based transfer."""

from __future__ import annotations

import dataclasses
import os
import tempfile
import traceback
from pathlib import Path
from typing import Callable

from PySide6 import QtCore


@dataclasses.dataclass(slots=True)
class ExportRequest:
    target_dir: Path
    chunk_bytes: int
    port_files: dict[str, Path]
    include_history: bool


@dataclasses.dataclass(slots=True)
class ExportProgress:
    """Progress information for export operation."""
    port_label: str
    percent: int
    bytes_written: int
    total_bytes: int


class LogExportWorker(QtCore.QThread):
    """
    Worker thread that exports log history without blocking UI.
    
    Uses temporary mmap file for large exports to minimize memory usage.
    Supports progress reporting and cancellation.
    """

    progress_changed = QtCore.Signal(int, str)  # percent, port_label
    chunk_ready = QtCore.Signal(str, int, int)  # port_label, offset, length (for mmap transfer)
    finished_success = QtCore.Signal(Path)
    failed = QtCore.Signal(str)

    def __init__(
        self, 
        request: ExportRequest, 
        history_reader: Callable[[str], str],
        text_fetcher: Callable[[str], str],
        parent=None
    ) -> None:
        super().__init__(parent)
        self._request = request
        self._history_reader = history_reader
        self._text_fetcher = text_fetcher
        self._cancelled = False
        self._temp_mmap_file: str | None = None

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:  # noqa: D401
        try:
            total_ports = len(self._request.port_files)
            
            # For large exports, create temporary mmap file
            use_mmap = self._request.chunk_bytes > 10 * 1024 * 1024  # > 10MB
            
            for index, (port_label, source_path) in enumerate(self._request.port_files.items(), start=1):
                if self._cancelled:
                    return
                    
                percent = int((index - 1) / max(1, total_ports) * 100)
                self.progress_changed.emit(percent, port_label)
                
                target_file = self._request.target_dir / f"{port_label}.txt"
                data = self._history_reader(port_label)
                if not data:
                    data = self._text_fetcher(port_label)
                
                if not data:
                    # Create empty file for ports with no data
                    data = ""
                
                data_bytes = data.encode('utf-8')
                total_bytes = len(data_bytes)
                
                if use_mmap and total_bytes > 1024 * 1024:  # > 1MB
                    # Write through mmap for large data
                    self._write_via_mmap(target_file, data_bytes, port_label, percent, index, total_ports)
                else:
                    # Direct write for small data
                    with open(target_file, "w", encoding="utf-8") as handle:
                        handle.write(data)
                
                # Emit progress for completed port
                port_percent = int(index / max(1, total_ports) * 100)
                self.progress_changed.emit(port_percent, port_label)
            
            # Cleanup temp file
            self._cleanup_temp_file()
            
            self.finished_success.emit(self._request.target_dir)
            
        except Exception as exc:  # pragma: no cover - observed via signal
            self._cleanup_temp_file()
            traceback_str = "".join(traceback.format_exception(exc))
            self.failed.emit(traceback_str)

    def _write_via_mmap(
        self, 
        target_file: Path, 
        data_bytes: bytes,
        port_label: str,
        start_percent: int,
        port_index: int,
        total_ports: int
    ) -> None:
        """
        Write data using temporary mmap file for large exports.
        
        This approach:
        1. Creates a temp file mapped to memory
        2. Writes data in chunks
        3. Emits progress via chunk_ready signal
        4. Copies to final destination
        """
        # Create temp file for mmap
        fd, self._temp_mmap_file = tempfile.mkstemp(suffix='.log_export')
        try:
            os.close(fd)
            
            # Resize temp file to fit data
            with open(self._temp_mmap_file, 'ba') as f:
                f.truncate(len(data_bytes))
            
            # Memory-map the file and write
            import mmap
            with open(self._temp_mmap_file, 'r+b') as f:
                mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)
                try:
                    chunk_size = 256 * 1024  # 256KB chunks
                    offset = 0
                    
                    while offset < len(data_bytes):
                        if self._cancelled:
                            return
                            
                        chunk = data_bytes[offset:offset + chunk_size]
                        mm[offset:offset + len(chunk)] = chunk
                        offset += len(chunk)
                        
                        # Emit chunk ready (for potential UI progress)
                        self.chunk_ready.emit(port_label, offset, len(data_bytes))
                        
                        # Update progress
                        chunk_percent = start_percent + int(
                            (offset / len(data_bytes)) * (100 // total_ports)
                        )
                        self.progress_changed.emit(chunk_percent, port_label)
                        
                finally:
                    mm.close()
            
            # Copy from temp file to final destination
            with open(self._temp_mmap_file, 'rb') as src:
                with open(target_file, 'wb') as dst:
                    dst.write(src.read())
                    
        finally:
            self._cleanup_temp_file()

    def _cleanup_temp_file(self) -> None:
        """Remove temporary mmap file if it exists."""
        if self._temp_mmap_file and os.path.exists(self._temp_mmap_file):
            try:
                os.unlink(self._temp_mmap_file)
            except OSError:
                pass
            self._temp_mmap_file = None
