import json
import os
import threading
import time
from typing import Any, Dict, Optional, Union
from datetime import datetime

class JSONDict:
    def __init__(self, file_path: str, save_throttle_ms: int = 5000):
        self.file_path = file_path
        self.save_throttle_ms = save_throttle_ms
        self._data = {}
        self._lock = threading.Lock()
        self._last_save_time = 0.0
        self._pending_save = False
        
        self._load_from_file()
    
    def _load_from_file(self):
        """Load data from JSON file if it exists"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
                print(f"[JSONDict] Loaded data from {self.file_path}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"[JSONDict] Error loading {self.file_path}: {e}")
                self._data = {}
        else:
            print(f"[JSONDict] No existing file found at {self.file_path}, starting with empty dict")
            self._data = {}
    
    def _save_to_file(self):
        """Save data to JSON file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            # Write to temporary file first, then rename for atomic operation
            temp_path = f"{self.file_path}.tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            os.rename(temp_path, self.file_path)
            self._last_save_time = time.time()
            self._pending_save = False
            print(f"[JSONDict] Saved data to {self.file_path}")
            
        except Exception as e:
            print(f"[JSONDict] Error saving to {self.file_path}: {e}")
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def _schedule_save(self):
        """Schedule a save operation with throttling"""
        current_time = time.time()
        
        # If enough time has passed since last save, save immediately
        if current_time - self._last_save_time >= (self.save_throttle_ms / 1000.0):
            print('breh0129312931238')
            self._save_to_file()
        else:
            # Schedule a delayed save
            if not self._pending_save:
                self._pending_save = True
                delay = (self.save_throttle_ms / 1000.0) - (current_time - self._last_save_time)
                print('alsdkjalskdjalksjdlaksjd')
                
                def delayed_save():
                    print('WHYYYYYY')
                    time.sleep(delay)
                    with self._lock:
                        if self._pending_save:
                            print('????')
                            self._save_to_file()
                
                # Run in background thread
                threading.Thread(target=delayed_save).start()
    
    def __getitem__(self, key: str) -> Any:
        """Get item by key"""
        with self._lock:
            return self._data[key]
    
    def __setitem__(self, key: str, value: Any):
        """Set item by key and schedule save"""
        with self._lock:
            self._data[key] = value
            self._schedule_save()
    
    def __delitem__(self, key: str):
        """Delete item by key and schedule save"""
        with self._lock:
            del self._data[key]
            self._schedule_save()
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists"""
        with self._lock:
            return key in self._data
    
    def __len__(self) -> int:
        """Get number of items"""
        with self._lock:
            return len(self._data)
    
    def __iter__(self):
        """Iterate over keys"""
        with self._lock:
            return iter(self._data)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get item with default value"""
        with self._lock:
            return self._data.get(key, default)
    
    def keys(self):
        """Get all keys"""
        with self._lock:
            return self._data.keys()
    
    def values(self):
        """Get all values"""
        with self._lock:
            return self._data.values()
    
    def items(self):
        """Get all key-value pairs"""
        with self._lock:
            return self._data.items()
    
    def update(self, other: Union[Dict[str, Any], 'JSONDict']):
        """Update with another dictionary"""
        with self._lock:
            if isinstance(other, JSONDict):
                self._data.update(other._data)
            else:
                self._data.update(other)
            self._schedule_save()
    
    def clear(self):
        """Clear all items and schedule save"""
        with self._lock:
            self._data.clear()
            self._schedule_save()
    
    def pop(self, key: str, default: Any = None) -> Any:
        """Pop item and schedule save"""
        with self._lock:
            result = self._data.pop(key, default)
            self._schedule_save()
            return result
    
    def force_save(self):
        """Force immediate save, bypassing throttle"""
        with self._lock:
            self._save_to_file()
    
    def to_dict(self) -> Dict[str, Any]:
        """Get a copy of the current data"""
        with self._lock:
            return self._data.copy()
    
    def __repr__(self) -> str:
        """String representation"""
        with self._lock:
            return f"JSONDict(file_path='{self.file_path}', items={len(self._data)})"


# Global instance for manga library data
_manga_library: Optional[JSONDict] = None

def get_manga_library() -> JSONDict:
    """Get the global manga library JSONDict instance"""
    global _manga_library
    if _manga_library is None:
        initialize_manga_library()
    return _manga_library

def initialize_manga_library() -> JSONDict:
    """Initialize the global manga library with optional custom file path"""
    global _manga_library
    file_path = os.path.join(os.path.dirname(__file__), 'manga_library.json')
    _manga_library = JSONDict(file_path)
    return _manga_library
