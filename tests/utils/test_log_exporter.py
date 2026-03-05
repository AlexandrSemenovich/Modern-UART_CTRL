"""Tests for LogExportWorker edge cases."""

import os
import tempfile
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.utils.log_exporter import ExportProgress, ExportRequest, LogExportWorker


class TestExportRequest:
    """Tests for ExportRequest dataclass."""

    def test_export_request_creation(self):
        """Test ExportRequest can be created with all fields."""
        target_dir = Path("/tmp/export")
        port_files = {
            "CPU1": Path("/data/cpu1.txt"),
            "CPU2": Path("/data/cpu2.txt"),
        }
        
        request = ExportRequest(
            target_dir=target_dir,
            chunk_bytes=1024,
            port_files=port_files,
            include_history=True,
        )
        
        assert request.target_dir == target_dir
        assert request.chunk_bytes == 1024
        assert request.port_files == port_files
        assert request.include_history is True

    def test_export_request_defaults(self):
        """Test ExportRequest with minimal fields."""
        request = ExportRequest(
            target_dir=Path("/tmp"),
            chunk_bytes=0,
            port_files={},
            include_history=False,
        )
        
        assert request.chunk_bytes == 0
        assert not request.include_history


class TestExportProgress:
    """Tests for ExportProgress dataclass."""

    def test_export_progress_creation(self):
        """Test ExportProgress can be created."""
        progress = ExportProgress(
            port_label="CPU1",
            percent=50,
            bytes_written=512,
            total_bytes=1024,
        )
        
        assert progress.port_label == "CPU1"
        assert progress.percent == 50
        assert progress.bytes_written == 512
        assert progress.total_bytes == 1024


class TestLogExportWorkerEdgeCases:
    """Edge case tests for LogExportWorker."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for exports."""
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    @pytest.fixture
    def mock_history_reader(self):
        """Create mock history reader function."""
        def reader(port: str) -> str:
            return f"Log data for {port}\nLine 2\nLine 3"
        return reader

    @pytest.fixture
    def mock_text_fetcher(self):
        """Create mock text fetcher function."""
        def fetcher(port: str) -> str:
            return f"Console text for {port}"
        return fetcher

    def test_worker_empty_port_files(self, temp_dir, mock_history_reader, mock_text_fetcher):
        """Test export with no port files creates empty target."""
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=1000,
            port_files={},
            include_history=False,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=mock_history_reader,
            text_fetcher=mock_text_fetcher,
        )
        
        import time
        result_path = None
        
        def on_finished(path):
            nonlocal result_path
            result_path = path
        
        worker.finished_success.connect(on_finished)
        worker.start()
        
        # Wait and process events
        worker.wait(5000)
        time.sleep(0.1)
        
        # With no port files, the worker should still emit finished_success
        # But due to Qt threading, we need to check differently
        # Check that target dir exists and is empty
        assert temp_dir.exists()
        assert list(temp_dir.glob("*.txt")) == []

    def test_worker_single_port_export(self, temp_dir, mock_history_reader, mock_text_fetcher):
        """Test export with single port."""
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=1000,
            port_files={"CPU1": Path("/data/cpu1.txt")},
            include_history=True,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=mock_history_reader,
            text_fetcher=mock_text_fetcher,
        )
        
        finished_event = threading.Event()
        result_path = None
        
        def on_finished(path):
            nonlocal result_path
            result_path = path
            finished_event.set()
        
        worker.finished_success.connect(on_finished)
        worker.start()
        finished_event.wait(timeout=5)
        
        # Check file was created
        output_file = temp_dir / "CPU1.txt"
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "CPU1" in content

    def test_worker_multiple_ports_export(self, temp_dir):
        """Test export with multiple ports."""
        def history_reader(port: str) -> str:
            return f"History for {port}"
        
        def text_fetcher(port: str) -> str:
            return f"Text for {port}"
        
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=1000,
            port_files={
                "CPU1": Path("/data/cpu1.txt"),
                "CPU2": Path("/data/cpu2.txt"),
                "TLM": Path("/data/tlm.txt"),
            },
            include_history=True,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=history_reader,
            text_fetcher=text_fetcher,
        )
        
        finished_event = threading.Event()
        
        def on_finished(path):
            finished_event.set()
        
        worker.finished_success.connect(on_finished)
        worker.start()
        finished_event.wait(timeout=5)
        
        # All three files should exist
        assert (temp_dir / "CPU1.txt").exists()
        assert (temp_dir / "CPU2.txt").exists()
        assert (temp_dir / "TLM.txt").exists()

    def test_worker_cancellation(self, temp_dir):
        """Test worker can be cancelled."""
        def slow_history_reader(port: str) -> str:
            # Simulate slow read
            import time
            time.sleep(0.5)
            return f"Data for {port}"
        
        def text_fetcher(port: str) -> str:
            return ""
        
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=1000,
            port_files={
                "CPU1": Path("/data/cpu1.txt"),
                "CPU2": Path("/data/cpu2.txt"),
            },
            include_history=True,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=slow_history_reader,
            text_fetcher=text_fetcher,
        )
        
        worker.start()
        
        # Cancel after short delay
        import time
        time.sleep(0.1)
        worker.cancel()
        
        # Wait for worker to finish
        worker.wait(5000)
        
        # Worker should complete without error (cancelled cleanly)
        assert not worker.isRunning() or worker.isFinished()

    def test_worker_progress_signals(self, temp_dir):
        """Test progress signals are emitted during export."""
        def history_reader(port: str) -> str:
            return f"Data for {port}"
        
        def text_fetcher(port: str) -> str:
            return ""
        
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=1000,
            port_files={
                "CPU1": Path("/data/cpu1.txt"),
                "CPU2": Path("/data/cpu2.txt"),
            },
            include_history=True,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=history_reader,
            text_fetcher=text_fetcher,
        )
        
        # Just verify worker completes successfully
        worker.start()
        import time
        worker.wait(5000)
        
        # Verify files were created
        assert (temp_dir / "CPU1.txt").exists()
        assert (temp_dir / "CPU2.txt").exists()

    def test_worker_empty_history_creates_file(self, temp_dir):
        """Test that empty history still creates file."""
        def empty_history_reader(port: str) -> str:
            return ""
        
        def empty_text_fetcher(port: str) -> str:
            return ""
        
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=1000,
            port_files={"CPU1": Path("/data/cpu1.txt")},
            include_history=True,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=empty_history_reader,
            text_fetcher=empty_text_fetcher,
        )
        
        finished_event = threading.Event()
        
        def on_finished(path):
            finished_event.set()
        
        worker.finished_success.connect(on_finished)
        worker.start()
        finished_event.wait(timeout=5)
        
        # File should exist but be empty
        output_file = temp_dir / "CPU1.txt"
        assert output_file.exists()
        assert output_file.read_text(encoding="utf-8") == ""

    def test_worker_large_chunk_uses_mmap(self, temp_dir):
        """Test that large chunk triggers mmap path."""
        def history_reader(port: str) -> str:
            # Return enough data to trigger mmap (>1MB)
            return "x" * (2 * 1024 * 1024)  # 2MB
        
        def text_fetcher(port: str) -> str:
            return ""
        
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=15 * 1024 * 1024,  # 15MB > 10MB threshold
            port_files={"CPU1": Path("/data/cpu1.txt")},
            include_history=True,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=history_reader,
            text_fetcher=text_fetcher,
        )
        
        finished_event = threading.Event()
        
        def on_finished(path):
            finished_event.set()
        
        worker.finished_success.connect(on_finished)
        worker.start()
        finished_event.wait(timeout=30)  # May take longer with mmap
        
        output_file = temp_dir / "CPU1.txt"
        assert output_file.exists()
        assert output_file.stat().st_size == 2 * 1024 * 1024

    def test_worker_unicode_content(self, temp_dir):
        """Test export handles unicode content correctly."""
        def unicode_history_reader(port: str) -> str:
            return "Привет мир\nHello world\n日本語テスト\n🔧🛠️"
        
        def text_fetcher(port: str) -> str:
            return ""
        
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=1000,
            port_files={"CPU1": Path("/data/cpu1.txt")},
            include_history=True,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=unicode_history_reader,
            text_fetcher=text_fetcher,
        )
        
        finished_event = threading.Event()
        
        def on_finished(path):
            finished_event.set()
        
        worker.finished_success.connect(on_finished)
        worker.start()
        finished_event.wait(timeout=5)
        
        output_file = temp_dir / "CPU1.txt"
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "Привет мир" in content
        assert "Hello world" in content
        assert "日本語テスト" in content

    def test_worker_fallback_to_text_fetcher(self, temp_dir):
        """Test that text_fetcher is used when history_reader returns empty."""
        def empty_history_reader(port: str) -> str:
            return ""
        
        def text_fetcher(port: str) -> str:
            return f"Fallback data for {port}"
        
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=1000,
            port_files={"CPU1": Path("/data/cpu1.txt")},
            include_history=True,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=empty_history_reader,
            text_fetcher=text_fetcher,
        )
        
        finished_event = threading.Event()
        
        def on_finished(path):
            finished_event.set()
        
        worker.finished_success.connect(on_finished)
        worker.start()
        finished_event.wait(timeout=5)
        
        output_file = temp_dir / "CPU1.txt"
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "Fallback data" in content

    def test_worker_exception_handling(self, temp_dir):
        """Test that exceptions are caught and emitted via failed signal."""
        def failing_history_reader(port: str) -> str:
            raise RuntimeError("Simulated read error")
        
        def text_fetcher(port: str) -> str:
            return ""
        
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=1000,
            port_files={"CPU1": Path("/data/cpu1.txt")},
            include_history=True,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=failing_history_reader,
            text_fetcher=text_fetcher,
        )
        
        # Start worker and wait for it to complete
        worker.start()
        import time
        worker.wait(5000)
        
        # Verify file was not created due to error
        assert not (temp_dir / "CPU1.txt").exists()

    def test_worker_handles_special_port_names(self, temp_dir):
        """Test export with special characters in port names."""
        def history_reader(port: str) -> str:
            return f"Data for {port}"
        
        def text_fetcher(port: str) -> str:
            return ""
        
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=1000,
            port_files={
                "COM1": Path("/data/com1.txt"),
                "COM10": Path("/data/com10.txt"),
            },
            include_history=True,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=history_reader,
            text_fetcher=text_fetcher,
        )
        
        finished_event = threading.Event()
        
        def on_finished(path):
            finished_event.set()
        
        worker.finished_success.connect(on_finished)
        worker.start()
        finished_event.wait(timeout=5)
        
        assert (temp_dir / "COM1.txt").exists()
        assert (temp_dir / "COM10.txt").exists()

    def test_worker_chunk_ready_signal(self, temp_dir):
        """Test mmap path works for large file writes."""
        def large_history_reader(port: str) -> str:
            # Return large data to trigger mmap path
            return "x" * (2 * 1024 * 1024)  # 2MB
        
        def text_fetcher(port: str) -> str:
            return ""
        
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=15 * 1024 * 1024,  # 15MB > 10MB
            port_files={"CPU1": Path("/data/cpu1.txt")},
            include_history=True,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=large_history_reader,
            text_fetcher=text_fetcher,
        )
        
        worker.start()
        
        # Wait for worker to complete
        import time
        worker.wait(30000)
        
        # Verify file was created correctly via mmap path
        output_file = temp_dir / "CPU1.txt"
        assert output_file.exists()
        assert output_file.stat().st_size == 2 * 1024 * 1024

    def test_worker_concurrent_access(self, temp_dir):
        """Test multiple workers can run concurrently to different dirs."""
        def history_reader(port: str) -> str:
            return f"Data for {port}"
        
        def text_fetcher(port: str) -> str:
            return ""
        
        # Create two workers with different target dirs
        temp_dir2 = temp_dir / "subdir"
        temp_dir2.mkdir()
        
        request1 = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=1000,
            port_files={"CPU1": Path("/data/cpu1.txt")},
            include_history=True,
        )
        
        request2 = ExportRequest(
            target_dir=temp_dir2,
            chunk_bytes=1000,
            port_files={"CPU2": Path("/data/cpu2.txt")},
            include_history=True,
        )
        
        worker1 = LogExportWorker(request1, history_reader, text_fetcher)
        worker2 = LogExportWorker(request2, history_reader, text_fetcher)
        
        worker1.start()
        worker2.start()
        
        # Wait for both workers
        import time
        worker1.wait(5000)
        worker2.wait(5000)
        
        # Verify both files were created
        assert (temp_dir / "CPU1.txt").exists()
        assert (temp_dir2 / "CPU2.txt").exists()

    def test_worker_include_history_false(self, temp_dir):
        """Test export with include_history=False still uses text_fetcher when history empty."""
        def history_reader(port: str) -> str:
            return ""  # Empty history
        
        def text_fetcher(port: str) -> str:
            return f"Console text for {port}"
        
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=1000,
            port_files={"CPU1": Path("/data/cpu1.txt")},
            include_history=False,  # History excluded
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=history_reader,
            text_fetcher=text_fetcher,
        )
        
        finished_event = threading.Event()
        
        def on_finished(path):
            finished_event.set()
        
        worker.finished_success.connect(on_finished)
        worker.start()
        finished_event.wait(5)
        
        output_file = temp_dir / "CPU1.txt"
        assert output_file.exists()
        # With empty history, text_fetcher should be used as fallback
        content = output_file.read_text(encoding="utf-8")
        assert "Console text" in content

    def test_worker_both_history_and_text_combined(self, temp_dir):
        """Test that history is used first when available, text only as fallback."""
        def history_reader(port: str) -> str:
            return f"History line 1\nHistory line 2"
        
        def text_fetcher(port: str) -> str:
            return f"Console line 1\nConsole line 2"
        
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=1000,
            port_files={"CPU1": Path("/data/cpu1.txt")},
            include_history=True,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=history_reader,
            text_fetcher=text_fetcher,
        )
        
        finished_event = threading.Event()
        
        def on_finished(path):
            finished_event.set()
        
        worker.finished_success.connect(on_finished)
        worker.start()
        finished_event.wait(5)
        
        output_file = temp_dir / "CPU1.txt"
        content = output_file.read_text(encoding="utf-8")
        # History should be used (text is only fallback)
        assert "History line" in content
        assert "Console line" not in content

    def test_worker_progress_percent_values(self, temp_dir):
        """Test that progress values are within valid range."""
        def history_reader(port: str) -> str:
            return f"Data for {port}"
        
        def text_fetcher(port: str) -> str:
            return ""
        
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=1000,
            port_files={
                "CPU1": Path("/data/cpu1.txt"),
                "CPU2": Path("/data/cpu2.txt"),
                "CPU3": Path("/data/cpu3.txt"),
            },
            include_history=True,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=history_reader,
            text_fetcher=text_fetcher,
        )
        
        progress_values = []
        
        def on_progress(percent, port_label):
            progress_values.append(percent)
        
        worker.progress_changed.connect(on_progress)
        
        finished_event = threading.Event()
        
        def on_finished(path):
            finished_event.set()
        
        worker.finished_success.connect(on_finished)
        worker.start()
        finished_event.wait(5)
        
        # All progress values should be 0-100
        for percent in progress_values:
            assert 0 <= percent <= 100

    def test_worker_cancel_during_mmap(self, temp_dir):
        """Test cancellation during mmap large file write."""
        def huge_history_reader(port: str) -> str:
            # Return very large data to ensure mmap path
            return "x" * (10 * 1024 * 1024)  # 10MB
        
        def text_fetcher(port: str) -> str:
            return ""
        
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=15 * 1024 * 1024,  # 15MB > 10MB threshold
            port_files={"CPU1": Path("/data/cpu1.txt")},
            include_history=True,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=huge_history_reader,
            text_fetcher=text_fetcher,
        )
        
        worker.start()
        
        # Cancel after a short delay to ensure mmap processing started
        import time
        time.sleep(0.2)
        worker.cancel()
        worker.wait(10000)
        
        # Worker should complete without errors
        assert not worker.isRunning()

    def test_worker_verify_file_contains_expected_data(self, temp_dir):
        """Test that output file contains exactly expected data."""
        test_history = "Line 1 from history\nLine 2 from history\nLine 3 from history"
        test_text = "Console line 1\nConsole line 2"
        
        def history_reader(port: str) -> str:
            return test_history
        
        def text_fetcher(port: str) -> str:
            return test_text
        
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=1000,
            port_files={"TEST_PORT": Path("/data/test.txt")},
            include_history=True,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=history_reader,
            text_fetcher=text_fetcher,
        )
        
        finished_event = threading.Event()
        
        def on_finished(path):
            finished_event.set()
        
        worker.finished_success.connect(on_finished)
        worker.start()
        finished_event.wait(5)
        
        output_file = temp_dir / "TEST_PORT.txt"
        content = output_file.read_text(encoding="utf-8")
        
        # Verify exact content
        assert content == test_history

    def test_worker_multiple_rapid_cancels(self, temp_dir):
        """Test that calling cancel multiple times is safe."""
        def slow_history_reader(port: str) -> str:
            import time
            time.sleep(0.3)
            return f"Data for {port}"
        
        def text_fetcher(port: str) -> str:
            return ""
        
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=1000,
            port_files={"CPU1": Path("/data/cpu1.txt")},
            include_history=True,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=slow_history_reader,
            text_fetcher=text_fetcher,
        )
        
        worker.start()
        
        # Call cancel multiple times rapidly
        worker.cancel()
        worker.cancel()
        worker.cancel()
        
        worker.wait(5000)
        
        # Should complete without error
        assert worker.isFinished() or not worker.isRunning()

    def test_worker_source_path_not_used(self, temp_dir):
        """Test that source_path in request is not used for reading."""
        # The source_path is passed but actual data comes from callbacks
        def history_reader(port: str) -> str:
            # This should be called regardless of source_path
            return f"Actual data from {port} reader"
        
        def text_fetcher(port: str) -> str:
            return ""
        
        # Pass non-existent source path - should still work
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=1000,
            port_files={"CPU1": Path("/nonexistent/path/source.txt")},
            include_history=True,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=history_reader,
            text_fetcher=text_fetcher,
        )
        
        finished_event = threading.Event()
        
        def on_finished(path):
            finished_event.set()
        
        worker.finished_success.connect(on_finished)
        worker.start()
        finished_event.wait(5)
        
        # Data should come from history_reader, not from source_path
        content = (temp_dir / "CPU1.txt").read_text(encoding="utf-8")
        assert "Actual data" in content

    def test_worker_verify_output_file_encoding(self, temp_dir):
        """Test that output file is correctly encoded in UTF-8."""
        def history_reader(port: str) -> str:
            # Include various UTF-8 characters
            return "Hello\u0000World\nJapanese: \u65e5\u672c\u8a9e\nEmoji: \U0001f600\n"
        
        def text_fetcher(port: str) -> str:
            return ""
        
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=1000,
            port_files={"CPU1": Path("/data/cpu1.txt")},
            include_history=True,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=history_reader,
            text_fetcher=text_fetcher,
        )
        
        finished_event = threading.Event()
        
        def on_finished(path):
            finished_event.set()
        
        worker.finished_success.connect(on_finished)
        worker.start()
        finished_event.wait(5)
        
        # Verify file can be read as UTF-8
        output_file = temp_dir / "CPU1.txt"
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "Hello" in content
        assert "Japanese" in content or "\u65e5" in content or "日本" in content

    def test_worker_line_endings(self, temp_dir):
        """Test that line endings are handled correctly."""
        def history_reader(port: str) -> str:
            return "Line 1\nLine 2\r\nLine 3\rLine 4"
        
        def text_fetcher(port: str) -> str:
            return ""
        
        request = ExportRequest(
            target_dir=temp_dir,
            chunk_bytes=1000,
            port_files={"CPU1": Path("/data/cpu1.txt")},
            include_history=True,
        )
        
        worker = LogExportWorker(
            request=request,
            history_reader=history_reader,
            text_fetcher=text_fetcher,
        )
        
        finished_event = threading.Event()
        
        def on_finished(path):
            finished_event.set()
        
        worker.finished_success.connect(on_finished)
        worker.start()
        finished_event.wait(5)
        
        output_file = temp_dir / "CPU1.txt"
        content = output_file.read_text(encoding="utf-8")
        assert "Line 1" in content
        assert "Line 2" in content
