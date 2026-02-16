#!/usr/bin/env python
"""
Run application with profiling enabled.

Usage:
    python scripts/profile_app.py
    python scripts/profile_app.py --output profile_output
"""

import sys
import os
import argparse

# Add parent directory to path (for src/ imports)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from src.main import MainWindow
import cProfile
import pstats
from io import StringIO

from src.styles.constants import LoggingConfig


def main():
    parser = argparse.ArgumentParser(description='Run app with profiling')
    parser.add_argument('--output', '-o', default='profile_output', 
                        help='Output profile file name (default: profile_output)')
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    
    # Enable profiling
    profiler = cProfile.Profile()
    profiler.enable()
    
    window = MainWindow()
    window.show()
    
    result = app.exec()
    
    profiler.disable()
    
    # Print stats to console
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats('cumulative')
    ps.print_stats(30)
    
    print("=== Top 30 Functions by Cumulative Time ===")
    print(s.getvalue())
    
    # Save to file
    profile_dir = LoggingConfig.LOG_DIR / 'profiles'
    profile_dir.mkdir(parents=True, exist_ok=True)
    output_file = profile_dir / f'{args.output}.prof'
    
    profiler.dump_stats(str(output_file))
    
    print(f"\nProfile saved to {output_file}")
    print("View with: python -m pstats", str(output_file))
    
    sys.exit(result)


if __name__ == '__main__':
    main()
