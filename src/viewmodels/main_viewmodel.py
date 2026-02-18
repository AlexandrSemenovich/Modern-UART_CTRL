"""
MainViewModel: Business logic for the main window.
Handles logging, filtering, formatting of console output from multiple serial ports.
"""

from PySide6 import QtCore
from PySide6.QtCore import Signal, Qt
from html import escape
from collections import deque
import re
import os

from src.utils.config_loader import config_loader
from src.utils.theme_manager import theme_manager
from src.utils.profiler import PerformanceTimer

# Enable/disable profiling via environment variable
_ENABLE_PROFILING = os.environ.get('APP_PROFILE', '').lower() == 'true'


class MainViewModel(QtCore.QObject):
    """
    ViewModel for console logging and display management.
    
    Signals:
        log_appended (str): HTML text to append to a specific log widget
        logs_cleared (): All logs cleared
        logs_filtered (str): Logs filtered with search results
    """
    
    # Signals for View binding
    log_cpu1_changed = Signal(str)      # HTML for CPU1 log
    log_cpu2_changed = Signal(str)      # HTML for CPU2 log
    log_all_changed = Signal(str)       # HTML for combined log
    log_tlm_changed = Signal(str)       # HTML for TLM log
    
    counters_changed = Signal(int, int, int)  # cpu1_rx, cpu1_tx, etc
    
    # Maximum number of log lines to keep in cache per widget
    # Value is taken from console configuration (ConsoleLimits)
    from src.styles.constants import ConsoleLimits as _ConsoleLimits  # local import to avoid cycles
    MAX_CACHE_LINES = _ConsoleLimits.MAX_CACHE_LINES
    
    def __init__(self):
        super().__init__()
        
        # Display options
        self.show_time = True
        self.show_source = True
        self._colors = config_loader.get_colors(self._current_theme())
        theme_manager.theme_changed.connect(self._on_theme_changed)
        
        # Counters for each port
        self.rx_counts = [0, 0, 0]  # CPU1, CPU2, TLM
        self.tx_counts = [0, 0, 0]
        
        # Cache for filtering
        self.log_cache = {}

    def _current_theme(self) -> str:
        return "light" if theme_manager.is_light_theme() else "dark"

    def _on_theme_changed(self, theme: str) -> None:
        self._colors = config_loader.get_colors(theme)
    
    def set_display_options(self, show_time: bool, show_source: bool) -> None:
        """Update display options for time and source visibility."""
        self.show_time = show_time
        self.show_source = show_source
    
    def _format_message(self, source: str, text: str, source_label: str, text_color: str) -> str:
        """
        Common formatting logic for all message types.
        
        Args:
            source (str): Port label (e.g., 'CPU1', 'CPU2')
            text (str): Message text
            source_label (str): Label prefix (e.g., 'RX', 'TX', 'SYS')
            text_color (str): CSS color for the text
            
        Returns:
            str: HTML formatted text
        """
        if not text or not text.strip():
            return ""
            
        ts = QtCore.QDateTime.currentDateTime().toString('hh:mm:ss')
        time_color = self._colors.timestamp
        time_part = f"<span style='color:{time_color}'>[{ts}]</span> " if self.show_time else ""
        source_part = f"<b style='color:{text_color}'>{source_label}({source}):</b> " if self.show_source else ""
        
        # Remove trailing line endings
        text = text.rstrip('\r\n')
        
        escaped_text = escape(text)
        return f"{time_part}{source_part}<span style='color:{text_color}; white-space:pre'>{escaped_text}</span><br>"
    
    def format_rx(self, source: str, text: str) -> str:
        """
        Format RX (received) message.
        
        Args:
            source (str): Port label (e.g., 'CPU1', 'CPU2')
            text (str): Data text
            
        Returns:
            str: HTML formatted text
        """
        if _ENABLE_PROFILING:
            with PerformanceTimer('format_rx', logging.DEBUG):
                return self._format_message(source, text, "RX", self._colors.rx_label)
        return self._format_message(source, text, "RX", self._colors.rx_label)
    
    def format_tx(self, source: str, text: str) -> str:
        """
        Format TX (transmitted) message.
        
        Args:
            source (str): Port label (e.g., 'CPU1', 'CPU2')
            text (str): Data text
            
        Returns:
            str: HTML formatted text
        """
        return self._format_message(source, text, "TX", self._colors.tx_label)
    
    def format_system(self, source: str, text: str) -> str:
        """
        Format system message.
        
        Args:
            source (str): Port label (e.g., 'CPU1', 'CPU2')
            text (str): Message text
            
        Returns:
            str: HTML formatted text
        """
        return self._format_message(source, text, "SYS", self._colors.sys_label)
    
    def increment_rx(self, port_index: int) -> int:
        """
        Increment RX counter for a port.
        
        Args:
            port_index (int): Port index (1-3)
            
        Returns:
            int: New count
        """
        idx = port_index - 1
        if 0 <= idx < len(self.rx_counts):
            self.rx_counts[idx] += 1
            return self.rx_counts[idx]
        return 0
    
    def increment_tx(self, port_index: int) -> int:
        """
        Increment TX counter for a port.
        
        Args:
            port_index (int): Port index (1-3)
            
        Returns:
            int: New count
        """
        idx = port_index - 1
        if 0 <= idx < len(self.tx_counts):
            self.tx_counts[idx] += 1
            return self.tx_counts[idx]
        return 0
    
    def get_rx_count(self, port_index: int) -> int:
        """Get RX counter for a port."""
        idx = port_index - 1
        if 0 <= idx < len(self.rx_counts):
            return self.rx_counts[idx]
        return 0
    
    def get_tx_count(self, port_index: int) -> int:
        """Get TX counter for a port."""
        idx = port_index - 1
        if 0 <= idx < len(self.tx_counts):
            return self.tx_counts[idx]
        return 0
    
    def clear_counters(self) -> None:
        """Reset all counters."""
        self.rx_counts = [0, 0, 0]
        self.tx_counts = [0, 0, 0]
    
    def cache_log_line(self, cache_key: str, html: str, plain: str) -> None:
        """
        Cache a log line for filtering support with size limit.
        Uses deque with maxlen for O(1) append operations.
        
        Args:
            cache_key (str): Widget identifier (e.g., 'cpu1', 'cpu2', 'all')
            html (str): HTML formatted version
            plain (str): Plain text version (for filtering)
        """
        if cache_key not in self.log_cache:
            # Use deque with maxlen for automatic size limiting (O(1) operation)
            self.log_cache[cache_key] = {
                'html': deque(maxlen=self.MAX_CACHE_LINES),
                'plain': deque(maxlen=self.MAX_CACHE_LINES)
            }
        
        self.log_cache[cache_key]['html'].append(html)
        self.log_cache[cache_key]['plain'].append(plain)
    
    def clear_cache(self) -> None:
        """Clear all cached logs."""
        self.log_cache.clear()
    
    @staticmethod
    def strip_html(html_text: str) -> str:
        """
        Remove HTML tags from text for plain text filtering.
        
        Args:
            html_text (str): HTML formatted text
            
        Returns:
            str: Plain text
        """
        clean = re.compile('<.*?>')
        clean_text = re.sub(clean, '', html_text)
        # Also decode HTML entities
        return (clean_text
                .replace('&lt;', '<')
                .replace('&gt;', '>')
                .replace('&amp;', '&'))
    
    def filter_cache(self, cache_key: str, search_text: str) -> str:
        """
        Filter cached logs by search text, preserving HTML formatting.
        
        Args:
            cache_key (str): Widget identifier
            search_text (str): Search query
            
        Returns:
            str: Filtered HTML content
        """
        if _ENABLE_PROFILING:
            with PerformanceTimer('filter_cache', logging.DEBUG):
                return self._filter_cache_impl(cache_key, search_text)
        return self._filter_cache_impl(cache_key, search_text)
    
    def _filter_cache_impl(self, cache_key: str, search_text: str) -> str:
        """Internal implementation of filter_cache."""
        if cache_key not in self.log_cache:
            return ""
        
        cache_data = self.log_cache[cache_key]
        if 'html' not in cache_data:
            return ""
        
        html_lines = cache_data['html']
        plain_lines = cache_data['plain']
        
        # Filter lines
        if search_text.strip():
            search_lower = search_text.lower()
            filtered_html = [
                html for html, plain in zip(html_lines, plain_lines)
                if search_lower in plain.lower()
            ]
        else:
            filtered_html = html_lines
        
        return ''.join(filtered_html)
