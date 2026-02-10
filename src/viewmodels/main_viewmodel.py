"""
MainViewModel: Business logic for the main window.
Handles logging, filtering, formatting of console output from multiple serial ports.
"""

from PySide6 import QtCore
from PySide6.QtCore import Signal, Qt
from html import escape
import re


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
    log_aux_changed = Signal(str)       # HTML for AUX log
    
    counters_changed = Signal(int, int, int)  # cpu1_rx, cpu1_tx, etc
    
    # Maximum number of log lines to keep in cache per widget
    MAX_CACHE_LINES = 10000
    
    def __init__(self):
        super().__init__()
        
        # Display options
        self.show_time = True
        self.show_source = True
        
        # Counters for each port
        self.rx_counts = [0, 0, 0]  # CPU1, CPU2, AUX
        self.tx_counts = [0, 0, 0]
        
        # Cache for filtering
        self.log_cache = {}
    
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
        time_part = f"<span style='color:gray'>[{ts}]</span> " if self.show_time else ""
        source_part = f"<b style='{text_color}'>{source_label}({source}):</b> " if self.show_source else ""
        
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
        return self._format_message(source, text, "RX", "color:green")
    
    def format_tx(self, source: str, text: str) -> str:
        """
        Format TX (transmitted) message.
        
        Args:
            source (str): Port label (e.g., 'CPU1', 'CPU2')
            text (str): Data text
            
        Returns:
            str: HTML formatted text
        """
        return self._format_message(source, text, "TX", "color:#ffdd57")
    
    def format_system(self, source: str, text: str) -> str:
        """
        Format system message.
        
        Args:
            source (str): Port label (e.g., 'CPU1', 'CPU2')
            text (str): Message text
            
        Returns:
            str: HTML formatted text
        """
        return self._format_message(source, text, "SYS", "color:lightgray")
    
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
        
        Args:
            cache_key (str): Widget identifier (e.g., 'cpu1', 'cpu2', 'all')
            html (str): HTML formatted version
            plain (str): Plain text version (for filtering)
        """
        if cache_key not in self.log_cache:
            self.log_cache[cache_key] = {'html': [], 'plain': []}
        
        self.log_cache[cache_key]['html'].append(html)
        self.log_cache[cache_key]['plain'].append(plain)
        
        # Limit cache size to prevent memory issues
        max_lines = self.MAX_CACHE_LINES
        html_list = self.log_cache[cache_key]['html']
        plain_list = self.log_cache[cache_key]['plain']
        
        if len(html_list) > max_lines:
            # Keep only the most recent lines
            self.log_cache[cache_key]['html'] = html_list[-max_lines:]
            self.log_cache[cache_key]['plain'] = plain_list[-max_lines:]
    
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
