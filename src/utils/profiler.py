"""
Performance profiling utilities for Modern UART Control.

This module provides profiling capabilities:
- Context manager for profiling code sections
- Decorator for profiling functions
- Profile output to files and logs
"""

import cProfile
import pstats
import io
import logging
import functools
import os
from typing import Callable, Optional
from pathlib import Path

from src.styles.constants import LoggingConfig

logger = logging.getLogger(__name__)


class Profiler:
    """Context manager for profiling code sections."""
    
    def __init__(self, name: str, output_dir: Optional[Path] = None):
        self.name = name
        self.output_dir = output_dir or (LoggingConfig.LOG_DIR / 'profiles')
        self.profiler = cProfile.Profile()
        
    def __enter__(self):
        self.profiler.enable()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.profiler.disable()
        self._save_stats()
        
    def _save_stats(self):
        """Save profiling stats to file."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        stats_file = self.output_dir / f'{self.name}.prof'
        
        # Save as pickle
        self.profiler.dump_stats(str(stats_file))
        
        # Also print summary
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s)
        ps.sort_stats('cumulative')
        ps.print_stats(20)
        logger.info(f"Profile for {self.name}:\n{s.getvalue()}")
        
    def get_stats(self) -> str:
        """Get profiling stats as string."""
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s)
        ps.sort_stats('cumulative')
        ps.print_stats(30)
        return s.getvalue()


def profile_function(func: Callable) -> Callable:
    """Decorator to profile a function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        try:
            return func(*args, **kwargs)
        finally:
            profiler.disable()
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s)
            ps.sort_stats('cumulative')
            ps.print_stats(10)
            logger.debug(f"Profile for {func.__name__}:\n{s.getvalue()}")
    return wrapper


def profile_method(method: Callable) -> Callable:
    """Decorator to profile a method (preserves self reference)."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        try:
            return method(self, *args, **kwargs)
        finally:
            profiler.disable()
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s)
            ps.sort_stats('cumulative')
            ps.print_stats(10)
            logger.debug(f"Profile for {method.__name__}:\n{s.getvalue()}")
    return wrapper


class PerformanceTimer:
    """Simple context manager for timing code sections."""
    
    def __init__(self, name: str, log_level: int = logging.DEBUG):
        self.name = name
        self.log_level = log_level
        self.start_time = None
        self.end_time = None
        
    def __enter__(self):
        import time
        self.start_time = time.perf_counter()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        self.end_time = time.perf_counter()
        duration = self.end_time - self.start_time
        logger.log(self.log_level, f"Timer '{self.name}': {duration*1000:.2f} ms")
        
    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0


def get_profile_files() -> list[Path]:
    """Get list of all profile files."""
    profile_dir = LoggingConfig.LOG_DIR / 'profiles'
    if not profile_dir.exists():
        return []
    return sorted(profile_dir.glob('*.prof'), key=lambda p: p.stat().st_mtime, reverse=True)


def cleanup_old_profiles(days: int = 7) -> int:
    """Remove profile files older than specified days."""
    import time
    profile_dir = LoggingConfig.LOG_DIR / 'profiles'
    if not profile_dir.exists():
        return 0
    
    cutoff = time.time() - (days * 24 * 60 * 60)
    removed = 0
    
    for profile_file in profile_dir.glob('*.prof'):
        if profile_file.stat().st_mtime < cutoff:
            try:
                profile_file.unlink()
                removed += 1
            except OSError:
                pass
    
    return removed
