import platform
import psutil
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

@dataclass
class SystemInfo:
    """Data class representing system information."""
    os_type: str
    os_version: str
    os_release: str
    os_machine: str
    os_processor: str
    python_version: str
    cpu_count: int
    memory_total: int
    memory_available: int
    disk_partitions: List[Dict[str, str]]
    last_updated: datetime

@dataclass
class ProcessInfo:
    """Data class representing process information."""
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_percent: float
    create_time: datetime
    last_updated: datetime

class SystemModel:
    """Model for managing system state information."""
    
    def __init__(self):
        """Initialize the system model."""
        self._system_info = SystemInfo(
            os_type="",
            os_version="",
            os_release="",
            os_machine="",
            os_processor="",
            python_version="",
            cpu_count=0,
            memory_total=0,
            memory_available=0,
            disk_partitions=[],
            last_updated=datetime.now()
        )
        self._processes: Dict[int, ProcessInfo] = {}
        self._update_system_info()

    def _update_system_info(self) -> None:
        """Update system information."""
        self._system_info = SystemInfo(
            os_type=self._get_os_type(),
            os_version=platform.version(),
            os_release=platform.release(),
            os_machine=platform.machine(),
            os_processor=platform.processor(),
            python_version=platform.python_version(),
            cpu_count=psutil.cpu_count(),
            memory_total=psutil.virtual_memory().total,
            memory_available=psutil.virtual_memory().available,
            disk_partitions=[{
                'device': partition.device,
                'mountpoint': partition.mountpoint,
                'fstype': partition.fstype
            } for partition in psutil.disk_partitions()],
            last_updated=datetime.now()
        )

    def _get_os_type(self) -> str:
        """Get the OS type in a standardized format.
        
        Returns:
            Standardized OS type (macOS, Windows, Linux, or Unknown)
        """
        os_type = platform.system()
        if os_type == "Darwin":
            return "macOS"
        elif os_type == "Windows":
            return "Windows"
        elif os_type == "Linux":
            return "Linux"
        else:
            return "Unknown"

    def update_process_info(self) -> None:
        """Update information about running processes."""
        self._processes.clear()
        for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 
                                       'memory_percent', 'create_time']):
            try:
                info = proc.info()
                self._processes[info['pid']] = ProcessInfo(
                    pid=info['pid'],
                    name=info['name'],
                    status=info['status'],
                    cpu_percent=info['cpu_percent'],
                    memory_percent=info['memory_percent'],
                    create_time=datetime.fromtimestamp(info['create_time']),
                    last_updated=datetime.now()
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    def get_system_info(self) -> SystemInfo:
        """Get the current system information.
        
        Returns:
            Current SystemInfo object
        """
        self._update_system_info()
        return self._system_info

    def get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """Get information about a specific process.
        
        Args:
            pid: Process ID
            
        Returns:
            ProcessInfo object if found, None otherwise
        """
        self.update_process_info()
        return self._processes.get(pid)

    def get_process_by_name(self, name: str) -> List[ProcessInfo]:
        """Get information about processes matching a name.
        
        Args:
            name: Process name to search for
            
        Returns:
            List of matching ProcessInfo objects
        """
        self.update_process_info()
        return [
            proc for proc in self._processes.values()
            if name.lower() in proc.name.lower()
        ]

    def is_process_running(self, name: str) -> bool:
        """Check if a process is running.
        
        Args:
            name: Process name to check
            
        Returns:
            True if process is running, False otherwise
        """
        return len(self.get_process_by_name(name)) > 0

    def get_system_summary(self) -> str:
        """Get a human-readable summary of the system state.
        
        Returns:
            Formatted summary string
        """
        self._update_system_info()
        summary = []
        
        # System information
        summary.append(f"Operating System: {self._system_info.os_type} {self._system_info.os_version}")
        summary.append(f"System Architecture: {self._system_info.os_machine}")
        summary.append(f"Python Version: {self._system_info.python_version}")
        
        # Hardware information
        memory_gb = self._system_info.memory_total / (1024**3)
        available_gb = self._system_info.memory_available / (1024**3)
        summary.append(f"CPU Cores: {self._system_info.cpu_count}")
        summary.append(f"Total Memory: {memory_gb:.1f} GB")
        summary.append(f"Available Memory: {available_gb:.1f} GB")
        
        # Disk information
        summary.append("\nDisk Partitions:")
        for partition in self._system_info.disk_partitions:
            summary.append(f"- {partition['device']} mounted at {partition['mountpoint']}")
        
        return "\n".join(summary)

    def get_process_summary(self, name: str) -> str:
        """Get a human-readable summary of a process.
        
        Args:
            name: Process name to summarize
            
        Returns:
            Formatted summary string
        """
        processes = self.get_process_by_name(name)
        if not processes:
            return f"No processes found matching '{name}'"
        
        summary = []
        for proc in processes:
            summary.append(f"Process: {proc.name} (PID: {proc.pid})")
            summary.append(f"Status: {proc.status}")
            summary.append(f"CPU Usage: {proc.cpu_percent:.1f}%")
            summary.append(f"Memory Usage: {proc.memory_percent:.1f}%")
            summary.append(f"Created: {proc.create_time}")
            summary.append("---")
        
        return "\n".join(summary) 