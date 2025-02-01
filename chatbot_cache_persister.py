import os
import json
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Define the path to the cache file
home_dir = os.path.expanduser("~")
cache_file_path = os.path.join(home_dir, ".instability_cache.json")

def load_cache():
    """Load the cache from the JSON file."""
    if os.path.exists(cache_file_path):
        try:
            with open(cache_file_path, 'r') as file:
                print(f"{Fore.GREEN}Cache loaded from {cache_file_path}{Style.RESET_ALL}")
                return json.load(file)
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error loading cache: {e}{Style.RESET_ALL}")
            pass
    else:
        print(f"{Fore.YELLOW}Cache not found at {cache_file_path}{Style.RESET_ALL}")
        return {}


def save_cache(cache):
    """Save the cache to the JSON file."""
    try:
        with open(cache_file_path, 'w') as file:
            print(f"{Fore.GREEN}Cache saved to {cache_file_path}{Style.RESET_ALL}")
            json.dump(cache, file, indent=4)
    except Exception as e:
        print(f"{Fore.RED}Error saving cache: {e}{Style.RESET_ALL}")
        pass


def update_cache(cache, key, value):
    """Update the cache with a new key-value pair."""
    try:
        cache[key] = value
        print(f"{Fore.GREEN}Cache updated with {key}: {value}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error updating cache: {e}{Style.RESET_ALL}")
        pass


def get_cached_value(cache, key):
    """Retrieve a value from the cache."""
    try:
        return cache.get(key)
    except Exception as e:
        print(f"{Fore.RED}Error getting cached value: {e}{Style.RESET_ALL}")
        pass
