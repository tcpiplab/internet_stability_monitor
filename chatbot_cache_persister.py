import os
import json

# Define the path to the cache file
home_dir = os.path.expanduser("~")
cache_file_path = os.path.join(home_dir, ".instability_cache.json")

def load_cache():
    """Load the cache from the JSON file."""
    if os.path.exists(cache_file_path):
        with open(cache_file_path, 'r') as file:
            return json.load(file)
    return {}

def save_cache(cache):
    """Save the cache to the JSON file."""
    with open(cache_file_path, 'w') as file:
        json.dump(cache, file, indent=4)

def update_cache(cache, key, value):
    """Update the cache with a new key-value pair."""
    cache[key] = value

def get_cached_value(cache, key):
    """Retrieve a value from the cache."""
    return cache.get(key)
