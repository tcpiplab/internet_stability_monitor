"""Context package for internet stability monitor.

This package provides a high-level interface that coordinates between different models
to manage the overall application state and provide unified access to system, network,
and location information.
"""

from .context import MonitorContext, SystemContext

__all__ = [
    'MonitorContext',
    'SystemContext'
] 