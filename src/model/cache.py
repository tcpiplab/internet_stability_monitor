import os
import json
from typing import Any, Dict, Optional
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

class CacheModel:
    """Model for managing persistent cache data."""
    
    def __init__(self, cache_file: Optional[str] = None):
        """Initialize the cache model.
        
        Args:
            cache_file: Optional path to the cache file. If not provided,
                       defaults to ~/.instability_cache.json
        """
        self.cache_file = cache_file or os.path.join(
            os.path.expanduser("~"), 
            ".instability_cache.json"
        )
        self._cache: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load the cache from the JSON file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as file:
                    self._cache = json.load(file)
                    print(f"{Fore.GREEN}Cache loaded from {self.cache_file}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Cache not found at {self.cache_file}{Style.RESET_ALL}")
                self._cache = {}
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error loading cache: {e}{Style.RESET_ALL}")
            self._cache = {}
        except Exception as e:
            print(f"{Fore.RED}Unexpected error loading cache: {e}{Style.RESET_ALL}")
            self._cache = {}

    def save(self) -> None:
        """Save the cache to the JSON file."""
        try:
            # Ensure the directory exists
            Path(self.cache_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.cache_file, 'w') as file:
                json.dump(self._cache, file, indent=4)
                print(f"{Fore.GREEN}Cache saved to {self.cache_file}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error saving cache: {e}{Style.RESET_ALL}")

    def update(self, key: str, value: Any) -> None:
        """Update the cache with a new key-value pair.
        
        Args:
            key: The key to update
            value: The value to store
        """
        try:
            self._cache[key] = value
            print(f"{Fore.GREEN}Cache updated with {key}: {value}{Style.RESET_ALL}")
            self.save()  # Auto-save on update
        except Exception as e:
            print(f"{Fore.RED}Error updating cache: {e}{Style.RESET_ALL}")

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the cache.
        
        Args:
            key: The key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            The cached value or the default value
        """
        try:
            return self._cache.get(key, default)
        except Exception as e:
            print(f"{Fore.RED}Error getting cached value: {e}{Style.RESET_ALL}")
            return default

    def delete(self, key: str) -> None:
        """Delete a key from the cache.
        
        Args:
            key: The key to delete
        """
        try:
            if key in self._cache:
                del self._cache[key]
                print(f"{Fore.GREEN}Cache deleted key: {key}{Style.RESET_ALL}")
                self.save()  # Auto-save on delete
        except Exception as e:
            print(f"{Fore.RED}Error deleting from cache: {e}{Style.RESET_ALL}")

    def clear(self) -> None:
        """Clear all data from the cache."""
        try:
            self._cache.clear()
            print(f"{Fore.GREEN}Cache cleared{Style.RESET_ALL}")
            self.save()  # Auto-save on clear
        except Exception as e:
            print(f"{Fore.RED}Error clearing cache: {e}{Style.RESET_ALL}")

    @property
    def data(self) -> Dict[str, Any]:
        """Get the entire cache data.
        
        Returns:
            The complete cache dictionary
        """
        return self._cache.copy()  # Return a copy to prevent external modification 