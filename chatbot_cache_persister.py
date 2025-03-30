import datetime
import os
import json
from typing import cast, IO
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
                print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot (thinking):{Style.RESET_ALL} {Fore.GREEN}Cache loaded from {cache_file_path}{Style.RESET_ALL}")
                return json.load(file)
        except json.JSONDecodeError as e:
            print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot (thinking):{Style.RESET_ALL} {Fore.RED}Error loading cache: {e}{Style.RESET_ALL}")
            return {}
    else:
        print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot (thinking):{Style.RESET_ALL} {Fore.YELLOW}Cache not found at {cache_file_path}{Style.RESET_ALL}")
        return {}


def save_cache(cache):
    """Save the cache to the JSON file."""

    # Get a machine-readable string for the current date and time
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Add the current time to the cache
    cache["cache_last_updated"] = current_time

    try:

        # Ensure cache is a dictionary
        if cache is None:
            cache = {}

        with open(cache_file_path, 'w') as file_handle:
            json.dump(cache, cast(IO[str], file_handle), indent=4)
            file_handle.write('\n')

    except Exception as e:
        print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot (thinking):{Style.RESET_ALL} {Fore.RED}Error saving cache: {e}{Style.RESET_ALL}")
        pass


def update_cache(cache, key, value):
    """Update the cache with a new key-value pair."""
    try:

        if cache is None:
            cache = {}

        cache[key] = value
        print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot (thinking):{Style.RESET_ALL} {Fore.GREEN}Cache updated with output from: {key}(){Style.RESET_ALL}")
        return cache # Return the updated cache

    except Exception as e:
        print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot (thinking):{Style.RESET_ALL} {Fore.RED}Error updating cache: {e}{Style.RESET_ALL}")
        return {}


def get_cached_value(cache, key):
    """Retrieve a value from the cache."""
    try:

        if cache is None:
            return None

        return cache.get(key)
    except Exception as e:
        print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot (thinking):{Style.RESET_ALL} {Fore.RED}Error getting cached value: {e}{Style.RESET_ALL}")
        return None
