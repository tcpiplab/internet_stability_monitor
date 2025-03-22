"""Presentation layer for internet stability monitor.

This package provides functionality for displaying monitoring data in various formats:
- Text output with color coding and symbols
- JSON output for programmatic consumption
- Tabular output for structured viewing
"""

from .presenter import MonitorPresenter, DisplayOptions

__all__ = [
    'MonitorPresenter',
    'DisplayOptions'
] 