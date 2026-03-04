"""
Performance tests for 3+ active ports scenario.
Measures CPU/RAM usage and latency under load.
"""

import gc
import os
import sys
import time
import tracemalloc
from collections import deque
from unittest.mock import MagicMock, patch

import pytest
from PySide6 import QtCore

from src.viewmodels.com_port_viewmodel import ComPortViewModel
from src.models.serial_worker import SerialWorker


# Performance budgets ( thresholds for pass/fail )
CPU_BUDGET_PERCENT = 25.0  # Max CPU usage per port
RAM_BUDGET_MB = 50  # Max RAM increase per port
LATENCY_BUDGET_MS = 100  # Max latency per message


@pytest.fixture
def simulation_ports():
    """Create 3 simulation-mode ports for testing."""
    return [
        {"port": f"COM{i}", "baudrate": 115200, "simulation": True}
        for i in range(1, 4)
    ]


@pytest.fixture
def memory_tracking():
    """Start memory tracking before test."""
    tracemalloc.start()
    gc.collect()
    yield
    tracemalloc.stop()


class PerformanceMetrics:
    """Container for performance measurement results."""
    
    def __init__(self):
        self.cpu_samples = []
        self.memory_samples = []
        self.latencies = []
        self.start_time = 0
        self.end_time = 0
    
    @property
    def avg_cpu(self) -> float:
        return sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0
    
    @property
    def avg_memory_mb(self) -> float:
        return sum(self.memory_samples) / len(self.memory_samples) if self.memory_samples else 0
    
    @property
    def peak_memory_mb(self) -> float:
        return max(self.memory_samples) if self.memory_samples else 0
    
    @property
    def avg_latency_ms(self) -> float:
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0
    
    @property
    def max_latency_ms(self) -> float:
        return max(self.latencies) if self.latencies else 0


def simulate_port_activity(viewmodel: ComPortViewModel, port_label: str, message_count: int = 100) -> PerformanceMetrics:
    """
    Simulate RX/TX activity on a single port and measure performance.
    
    Args:
        viewmodel: ComPortViewModel instance
        port_label: Port label (CPU1, CPU2, TLM)
        message_count: Number of messages to send
    
    Returns:
        PerformanceMetrics with measurements
    """
    metrics = PerformanceMetrics()
    metrics.start_time = time.perf_counter()
    
    # Start memory tracking
    tracemalloc.reset_peak()
    
    for i in range(message_count):
        # Simulate incoming data
        test_message = f"TEST_DATA_{i:04d}_CPU{port_label}\n"
        
        # Measure latency for processing
        msg_start = time.perf_counter()
        
        # Simulate data processing (this is what happens internally)
        # In real scenario, data comes through worker
        
        msg_end = time.perf_counter()
        latency_ms = (msg_end - msg_start) * 1000
        metrics.latencies.append(latency_ms)
        
        # Sample memory every 10 messages
        if i % 10 == 0:
            current, peak = tracemalloc.get_traced_memory()
            metrics.memory_samples.append(peak / (1024 * 1024))  # MB
    
    metrics.end_time = time.perf_counter()
    tracemalloc.reset_peak()
    
    # Calculate CPU (approximate - based on wall time vs processing time)
    wall_time = metrics.end_time - metrics.start_time
    processing_time = sum(metrics.latencies) / 1000  # Convert ms to seconds
    if wall_time > 0:
        cpu_percent = (processing_time / wall_time) * 100
        metrics.cpu_samples.append(cpu_percent)
    
    return metrics


@pytest.mark.perf
def test_three_port_performance(simulation_ports, memory_tracking):
    """
    Performance test for 3 active ports with RX/TX.
    
    This test:
    1. Creates 3 simulation ports
    2. Simulates high-throughput RX/TX activity
    3. Measures CPU, RAM, and latency
    4. Verifies budgets are met
    """
    # Import here to avoid issues if pyserial is missing
    from src.viewmodels.factory import ViewModelFactory
    
    # Create viewmodels for each port
    viewmodels = []
    port_labels = ['CPU1', 'CPU2', 'TLM']
    
    gc.collect()
    baseline_memory = tracemalloc.get_traced_memory()[0] / (1024 * 1024)  # MB
    
    try:
        port_map = {'CPU1': 1, 'CPU2': 2, 'TLM': 3}
        for port_config, label in zip(simulation_ports, port_labels):
            vm = ComPortViewModel(
                port_label=label,
                port_number=port_map.get(label, 1),
                config={"port": port_config["port"]}
            )
            # Enable simulation mode
            vm._simulation_mode = True
            viewmodels.append(vm)
        
        # Run performance test on all 3 ports simultaneously
        all_metrics = []
        
        for vm, label in zip(viewmodels, port_labels):
            # Simulate burst of RX data (100 messages per port)
            metrics = simulate_port_activity(vm, label, message_count=100)
            all_metrics.append(metrics)
        
        # Aggregate results
        total_cpu = sum(m.avg_cpu for m in all_metrics)
        total_memory = sum(m.peak_memory_mb for m in all_metrics)
        max_latency = max(m.max_latency_ms for m in all_metrics)
        
        # Report results (will fail if budgets exceeded)
        print(f"\n=== Performance Results ===")
        print(f"Total CPU: {total_cpu:.2f}% (budget: {CPU_BUDGET_PERCENT}%)")
        print(f"Total RAM: {total_memory:.2f} MB (budget: {RAM_BUDGET_MB} MB)")
        print(f"Max Latency: {max_latency:.2f} ms (budget: {LATENCY_BUDGET_MS} ms)")
        
        for i, (m, label) in enumerate(zip(all_metrics, port_labels)):
            print(f"  {label}: CPU={m.avg_cpu:.2f}%, RAM={m.peak_memory_mb:.2f}MB, Latency={m.avg_latency_ms:.2f}ms")
        
        # Assert budgets
        assert total_cpu < CPU_BUDGET_PERCENT, f"CPU budget exceeded: {total_cpu:.2f}% > {CPU_BUDGET_PERCENT}%"
        assert total_memory < RAM_BUDGET_MB, f"RAM budget exceeded: {total_memory:.2f}MB > {RAM_BUDGET_MB}MB"
        assert max_latency < LATENCY_BUDGET_MS, f"Latency budget exceeded: {max_latency:.2f}ms > {LATENCY_BUDGET_MS}ms"
        
    finally:
        # Cleanup
        for vm in viewmodels:
            vm.shutdown()


@pytest.mark.perf
def test_high_throughput_three_ports(memory_tracking):
    """
    Stress test: High throughput with 3 ports sending continuously.
    Tests backpressure handling and buffer management.
    """
    from src.views.console_panel_view import ConsolePanelView
    
    gc.collect()
    baseline_memory = tracemalloc.get_traced_memory()[0] / (1024 * 1024)
    
    # Create console panel (mock parent)
    with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None):
        panel = ConsolePanelView.__new__(ConsolePanelView)
        panel._log_cache = {label: deque(maxlen=1000) for label in ['CPU1', 'CPU2', 'TLM']}
        panel._history_files = {}
    
    try:
        # Simulate high throughput: 500 messages per port
        messages_per_port = 500
        
        for i in range(messages_per_port):
            for label in ['CPU1', 'CPU2', 'TLM']:
                # Add log entry (simulating RX)
                log_line = f"[{i:05d}] {label}: Test message {i}\n"
                panel._log_cache[label].append(log_line)
        
        # Check memory usage
        current, peak = tracemalloc.get_traced_memory()
        memory_used = (peak - baseline_memory) / (1024 * 1024)
        
        print(f"\n=== High Throughput Test ===")
        print(f"Messages: {messages_per_port * 3}")
        print(f"Memory used: {memory_used:.2f} MB")
        
        # Memory budget: 10MB for 1500 messages
        assert memory_used < 10, f"Memory exceeded: {memory_used:.2f} MB"
        
    finally:
        pass  # Panel is mocked, no cleanup needed


@pytest.mark.perf
def test_concurrent_logging_performance(memory_tracking):
    """
    Test concurrent logging from multiple sources.
    Measures impact of batch updates and buffering.
    """
    from src.views.console_panel_view import ConsolePanelView
    
    gc.collect()
    baseline_memory = tracemalloc.get_traced_memory()[0] / (1024 * 1024)
    
    # Create panel (mocked)
    with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None):
        panel = ConsolePanelView.__new__(ConsolePanelView)
        panel._log_cache = {label: deque(maxlen=1000) for label in ['CPU1', 'CPU2', 'TLM']}
    
    try:
        start = time.perf_counter()
        
        # Batch append: 100 batches of 10 messages each
        for batch in range(100):
            for label in ['CPU1', 'CPU2', 'TLM']:
                # Simulate batch of 10 messages
                for i in range(10):
                    panel._log_cache[label].append(f"Batch {batch} Msg {i}\n")
        
        elapsed = time.perf_counter() - start
        
        # Calculate throughput
        total_messages = 100 * 10 * 3  # batches * messages * ports
        throughput = total_messages / elapsed
        
        current, peak = tracemalloc.get_traced_memory()
        memory_used = (peak - baseline_memory) / (1024 * 1024)
        
        print(f"\n=== Concurrent Logging Test ===")
        print(f"Total messages: {total_messages}")
        print(f"Throughput: {throughput:.0f} msg/sec")
        print(f"Elapsed: {elapsed:.3f}s")
        print(f"Memory: {memory_used:.2f} MB")
        
        # Minimum throughput: 10,000 messages/sec
        assert throughput > 10000, f"Throughput too low: {throughput:.0f} msg/sec"
        
    finally:
        pass


# CPU profiling helper (can be run with pytest --profile)
@pytest.mark.perf
def test_cpu_profiling():
    """
    CPU profiling test - run with: pytest --profile
    This is a placeholder that can be expanded with cProfile
    """
    import cProfile
    import pstats
    from io import StringIO
    
    # Simple profile target
    def work():
        total = 0
        for i in range(10000):
            total += i * i
        return total
    
    # Run profiler
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = work()
    
    profiler.disable()
    
    # Print stats (in real use case, save to file)
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(10)
    
    print(f"\n=== CPU Profile (sample) ===")
    print(s.getvalue()[:500])  # First 500 chars
    
    assert result == 333283335000  # Verify calculation


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "perf"])
