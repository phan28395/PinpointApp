# In pinpoint/storage.py

import json
from pathlib import Path
class StorageManager:
    """Manages persistence of all application data to a JSON file."""

    def __init__(self, file_name: str = "pinpoint_data.json"):
        app_dir = Path.home() / ".pinpoint"
        app_dir.mkdir(parents=True, exist_ok=True)
        self.data_path = app_dir / file_name

    def load_data(self) -> dict:
        """
        Loads the main data object from the JSON file.
        Includes logic to automatically migrate old list-based data.
        """
        if not self.data_path.exists():
            return {"tiles": [], "layouts": []}
        
        try:
            with open(self.data_path, 'r') as f:
                data = json.load(f)
            
            # --- NEW: Migration Logic ---
            # Check if the loaded data is a list (the old format)
            if isinstance(data, list):
                print("Old data format detected. Migrating to new format...")
                # Create the new dictionary structure, placing the old list into the "tiles" key
                migrated_data = {"tiles": data, "layouts": []}
                # Immediately save the data back in the new format for next time
                self.save_data(migrated_data)
                return migrated_data

            # --- Standard Logic for New Format ---
            # If it's already a dict, just ensure the keys exist
            if "tiles" not in data:
                data["tiles"] = []
            if "layouts" not in data:
                data["layouts"] = []
            
            return data

        except (json.JSONDecodeError, IOError):
            # If file is corrupt or unreadable, return a clean default structure
            return {"tiles": [], "layouts": []}
    
    def save_data(self, app_data: dict):
        """Saves the given main data object to the JSON file."""
        try:
            with open(self.data_path, 'w') as f:
                json.dump(app_data, f, indent=2)
        except IOError as e:
            print(f"Error saving data: {e}")