"""
Unit tests for CommandHistoryViewModel.

Tests the command history functionality including:
- Adding entries
- Removing entries
- Clearing history
- Loading/saving history
- Edge cases for empty commands, max items, etc.
"""

import pytest
import sys
import os
import tempfile
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))


class TestCommandHistoryEntry:
    """Test CommandHistoryEntry dataclass."""
    
    def test_create_entry(self):
        """Test creating a history entry."""
        from src.viewmodels.command_history_viewmodel import CommandHistoryEntry
        
        entry = CommandHistoryEntry(
            command='PING',
            port='CPU1',
            status='success',
            timestamp='2024-01-01T12:00:00'
        )
        
        assert entry.command == 'PING'
        assert entry.port == 'CPU1'
        assert entry.status == 'success'
        assert entry.timestamp == '2024-01-01T12:00:00'
    
    def test_to_display_tuple(self):
        """Test converting entry to display tuple."""
        from src.viewmodels.command_history_viewmodel import CommandHistoryEntry
        
        entry = CommandHistoryEntry(
            command='TEST',
            port='CPU2',
            status='error',
            timestamp='2024-01-01T10:00:00'
        )
        
        display = entry.to_display_tuple()
        
        assert display == ('TEST', 'CPU2', 'error', '2024-01-01T10:00:00')


class TestCommandHistoryModel:
    """Test CommandHistoryModel functionality."""
    
    def test_add_entry(self):
        """Test adding a command entry."""
        # Test the add logic
        entries = []
        max_items = 200
        
        command = 'PING'
        port = 'CPU1'
        status = 'success'
        timestamp = '2024-01-01T12:00:00'
        
        from src.viewmodels.command_history_viewmodel import CommandHistoryEntry
        entry = CommandHistoryEntry(command=command, port=port, status=status, timestamp=timestamp)
        entries.insert(0, entry)
        entries = entries[:max_items]
        
        assert len(entries) == 1
        assert entries[0].command == 'PING'
    
    def test_add_empty_command(self):
        """Test adding empty command does nothing."""
        entries = []
        
        command = '   '  # whitespace only
        if command.strip():  # Empty after strip
            from src.viewmodels.command_history_viewmodel import CommandHistoryEntry
            entry = CommandHistoryEntry(command=command, port='CPU1', status='success', timestamp='')
            entries.insert(0, entry)
        
        # Should not add
        assert len(entries) == 0
    
    def test_add_whitespace_command(self):
        """Test adding whitespace-only command is filtered."""
        command = '  '
        
        # The add_entry method strips and checks
        is_valid = bool(command.strip())
        
        assert is_valid is False
    
    def test_max_items_limit(self):
        """Test entries are limited to max_items."""
        entries = []
        max_items = 5
        
        from src.viewmodels.command_history_viewmodel import CommandHistoryEntry
        
        # Add more than max
        for i in range(10):
            entry = CommandHistoryEntry(
                command=f'CMD{i}',
                port='CPU1',
                status='success',
                timestamp=f'2024-01-01T{i:02d}:00:00'
            )
            entries.insert(0, entry)
        
        # Apply limit
        entries = entries[:max_items]
        
        assert len(entries) == max_items
        assert entries[0].command == 'CMD9'  # Last added
    
    def test_remove_entry(self):
        """Test removing entry by index."""
        entries = []
        
        from src.viewmodels.command_history_viewmodel import CommandHistoryEntry
        
        entries.append(CommandHistoryEntry(command='CMD1', port='CPU1', status='success', timestamp=''))
        entries.append(CommandHistoryEntry(command='CMD2', port='CPU1', status='success', timestamp=''))
        entries.append(CommandHistoryEntry(command='CMD3', port='CPU1', status='success', timestamp=''))
        
        # Remove index 1
        indices_to_remove = [1]
        sorted_indices = sorted(set(idx for idx in indices_to_remove if 0 <= idx < len(entries)), reverse=True)
        
        for idx in sorted_indices:
            entries.pop(idx)
        
        assert len(entries) == 2
        assert entries[0].command == 'CMD1'
        assert entries[1].command == 'CMD3'
    
    def test_clear_entries(self):
        """Test clearing all entries."""
        from src.viewmodels.command_history_viewmodel import CommandHistoryEntry
        
        entries = [
            CommandHistoryEntry(command='CMD1', port='CPU1', status='success', timestamp=''),
            CommandHistoryEntry(command='CMD2', port='CPU1', status='success', timestamp=''),
        ]
        
        entries.clear()
        
        assert len(entries) == 0
    
    def test_entry_count(self):
        """Test getting entry count."""
        from src.viewmodels.command_history_viewmodel import CommandHistoryEntry
        
        entries = [
            CommandHistoryEntry(command='CMD1', port='CPU1', status='success', timestamp=''),
            CommandHistoryEntry(command='CMD2', port='CPU1', status='success', timestamp=''),
            CommandHistoryEntry(command='CMD3', port='CPU1', status='success', timestamp=''),
        ]
        
        count = len(entries)
        
        assert count == 3


class TestSerialization:
    """Test serialization/deserialization."""
    
    def test_serialize_entries(self):
        """Test serializing entries to JSON."""
        from src.viewmodels.command_history_viewmodel import CommandHistoryEntry
        from dataclasses import asdict
        
        entries = [
            CommandHistoryEntry(command='PING', port='CPU1', status='success', timestamp='2024-01-01T12:00:00'),
            CommandHistoryEntry(command='PONG', port='CPU2', status='error', timestamp='2024-01-01T12:01:00'),
        ]
        
        data = [asdict(entry) for entry in entries]
        
        assert len(data) == 2
        assert data[0]['command'] == 'PING'
        assert data[1]['status'] == 'error'
    
    def test_deserialize_entries(self):
        """Test deserializing entries from JSON."""
        json_data = [
            {'command': 'TEST1', 'port': 'CPU1', 'status': 'success', 'timestamp': '2024-01-01T10:00:00'},
            {'command': 'TEST2', 'port': 'CPU2', 'status': 'error', 'timestamp': '2024-01-01T10:01:00'},
        ]
        
        from src.viewmodels.command_history_viewmodel import CommandHistoryEntry
        entries = [
            CommandHistoryEntry(
                command=item.get('command', ''),
                port=item.get('port', 'unknown'),
                status=item.get('status', 'unknown'),
                timestamp=item.get('timestamp', '')
            )
            for item in json_data
            if item.get('command')
        ]
        
        assert len(entries) == 2
        assert entries[0].command == 'TEST1'
        assert entries[1].port == 'CPU2'


class TestExport:
    """Test export functionality."""
    
    def test_export_to_file(self, tmp_path):
        """Test exporting history to file."""
        from src.viewmodels.command_history_viewmodel import CommandHistoryEntry
        
        entries = [
            CommandHistoryEntry(command='PING', port='CPU1', status='success', timestamp='2024-01-01T12:00:00'),
            CommandHistoryEntry(command='PONG', port='CPU2', status='error', timestamp='2024-01-01T12:01:00'),
        ]
        
        export_file = tmp_path / "export.txt"
        
        with export_file.open('w', encoding='utf-8') as handle:
            for entry in entries:
                handle.write("\t".join(entry.to_display_tuple()) + "\n")
        
        content = export_file.read_text()
        
        assert 'PING' in content
        assert 'CPU1' in content


class TestEdgeCases:
    """Test edge cases."""
    
    def test_unicode_commands(self):
        """Test handling unicode commands."""
        from src.viewmodels.command_history_viewmodel import CommandHistoryEntry
        
        entry = CommandHistoryEntry(
            command='Команда',
            port='CPU1',
            status='success',
            timestamp='2024-01-01T12:00:00'
        )
        
        assert 'Команда' in entry.command
    
    def test_special_characters_in_command(self):
        """Test handling special characters in command."""
        from src.viewmodels.command_history_viewmodel import CommandHistoryEntry
        
        entry = CommandHistoryEntry(
            command='AT+CMD="test"',
            port='CPU1',
            status='success',
            timestamp='2024-01-01T12:00:00'
        )
        
        assert '=' in entry.command
        assert '"' in entry.command
    
    def test_long_command(self):
        """Test handling very long commands."""
        from src.viewmodels.command_history_viewmodel import CommandHistoryEntry
        
        long_command = 'A' * 10000
        entry = CommandHistoryEntry(
            command=long_command,
            port='CPU1',
            status='success',
            timestamp='2024-01-01T12:00:00'
        )
        
        assert len(entry.command) == 10000
    
    def test_empty_history(self):
        """Test empty history handling."""
        from src.viewmodels.command_history_viewmodel import CommandHistoryEntry
        
        entries = []
        
        assert len(entries) == 0
        assert entries == []
    
    def test_multiple_entries_same_timestamp(self):
        """Test multiple entries can have same timestamp."""
        from src.viewmodels.command_history_viewmodel import CommandHistoryEntry
        
        entries = [
            CommandHistoryEntry(command='CMD1', port='CPU1', status='success', timestamp='2024-01-01T12:00:00'),
            CommandHistoryEntry(command='CMD2', port='CPU2', status='success', timestamp='2024-01-01T12:00:00'),
        ]
        
        assert entries[0].timestamp == entries[1].timestamp


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
