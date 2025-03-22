"""Model package for internet stability monitor.

This package contains the core data models used throughout the application:
- CacheModel: Manages persistent cache data
- NetworkModel: Handles network state information
- LocationModel: Manages location and IP information
"""

from .cache import CacheModel
from .network import NetworkModel, NetworkInterface, NetworkState
from .location import LocationModel, LocationInfo, IPReputation

__all__ = [
    'CacheModel',
    'NetworkModel',
    'NetworkInterface',
    'NetworkState',
    'LocationModel',
    'LocationInfo',
    'IPReputation'
] 