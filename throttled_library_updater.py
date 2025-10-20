import threading
import time
from typing import Optional, Dict, Set, Any

from json_dict import get_manga_library

class ThrottledLibraryUpdater:
    def __init__(self, throttle_ms: int = 500):
        self.throttle_ms = throttle_ms
        self._lock = threading.RLock()
        self._last_update_time = 0.0
        self._previous_update = None
        self._pending_update = False
        self._previous_library_data = get_manga_library().to_dict()
        
    def _update_library(self):
        try:
            self._last_update_time = time.time()
            self._pending_update = False

            new_library_data = get_manga_library().to_dict()

            import json

            with open('new_library_data.json', 'w', encoding='utf-8') as f_new:
                json.dump(new_library_data, f_new, ensure_ascii=False, indent=2)

            with open('previous_library_data.json', 'w', encoding='utf-8') as f_prev:
                json.dump(self._previous_library_data, f_prev, ensure_ascii=False, indent=2)

            # Compare old and new library data
            differences = self._compare_library_data(self._previous_library_data, new_library_data)
            
            # Process the differences
            self._process_differences(differences)
            
            # Update previous data for next comparison
            self._previous_library_data = new_library_data
            
        except Exception as e:
            print(f"[ThrottledLibraryUpdater] Error updating library: {e}")
    
    def _compare_library_data(self, old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare old and new library data and return differences.
        
        Returns:
            {
                'removed_manga': set of removed manga names,
                'removed_cbz_files': dict of removed CBZ files by manga,
                'new_manga': set of new manga names,
                'new_cbz_files': dict of new CBZ files by manga
            }
        """
        old_manga_names = set(old_data.keys())
        new_manga_names = set(new_data.keys())
        
        # 1. Set of all removed manga names
        removed_manga = old_manga_names - new_manga_names
        
        # 2. Dict of all removed CBZ files
        removed_cbz_files = {}
        for manga_name in removed_manga:
            if manga_name in old_data and 'cbz_files' in old_data[manga_name]:
                removed_cbz_files[manga_name] = {
                    'cbz_files': old_data[manga_name]['cbz_files']
                }
        
        # 3. Set of all new manga names
        new_manga = new_manga_names - old_manga_names
        
        # 4. Dict of all new CBZ files
        new_cbz_files = {}
        for manga_name in new_manga:
            if manga_name in new_data and 'cbz_files' in new_data[manga_name]:
                new_cbz_files[manga_name] = {
                    'cbz_files': new_data[manga_name]['cbz_files']
                }
        
        # Also check for CBZ file changes in existing manga
        existing_manga = old_manga_names & new_manga_names
        for manga_name in existing_manga:
            old_cbz_files = set(old_data.get(manga_name, {}).get('cbz_files', []))
            new_cbz_files_set = set(new_data.get(manga_name, {}).get('cbz_files', []))
            
            # Find removed CBZ files in existing manga
            removed_files = old_cbz_files - new_cbz_files_set
            if removed_files:
                if manga_name not in removed_cbz_files:
                    removed_cbz_files[manga_name] = {'cbz_files': []}
                removed_cbz_files[manga_name]['cbz_files'].extend(list(removed_files))
            
            # Find new CBZ files in existing manga
            added_files = new_cbz_files_set - old_cbz_files
            if added_files:
                if manga_name not in new_cbz_files:
                    new_cbz_files[manga_name] = {'cbz_files': []}
                new_cbz_files[manga_name]['cbz_files'].extend(list(added_files))
        
        return {
            'removed_manga': removed_manga,
            'removed_cbz_files': removed_cbz_files,
            'new_manga': new_manga,
            'new_cbz_files': new_cbz_files
        }
    
    def _process_differences(self, differences: Dict[str, Any]):
        """Process the differences found between old and new library data"""
        removed_manga = differences['removed_manga']
        removed_cbz_files = differences['removed_cbz_files']
        new_manga = differences['new_manga']
        new_cbz_files = differences['new_cbz_files']
        
        # Log the differences
        if removed_manga:
            print(f"[ThrottledLibraryUpdater] Removed manga: {removed_manga}")
        
        if removed_cbz_files:
            print(f"[ThrottledLibraryUpdater] Removed CBZ files: {removed_cbz_files}")
        
        if new_manga:
            print(f"[ThrottledLibraryUpdater] New manga: {new_manga}")
        
        if new_cbz_files:
            print(f"[ThrottledLibraryUpdater] New CBZ files: {new_cbz_files}")
        
        # Here you can add your custom logic to handle these differences
        # For example: update database, send notifications, etc.
    
    def schedule_update(self):
        """Schedule a update operation with throttling"""
        current_time = time.time()
        
        # If enough time has passed since last update, update immediately
        if current_time - self._last_update_time >= (self.throttle_ms / 1000.0):
            self._update_library()
        else:
            # Schedule a delayed update
            if not self._pending_update:
                self._pending_update = True
                delay = (self.throttle_ms / 1000.0) - (current_time - self._last_update_time)
                
                def delayed_update():
                    time.sleep(delay)
                    with self._lock:
                        if self._pending_update:
                            self._update_library()
                
                # Run in background thread
                threading.Thread(target=delayed_update, daemon=True).start()

# Global instance for throttled library updater
_throttled_library_updater: Optional[ThrottledLibraryUpdater] = None

def get_throttled_library_updater() -> ThrottledLibraryUpdater:
    """Get the global manga library JSONDict instance"""
    global _throttled_library_updater
    if _throttled_library_updater is None:
        initialize_throttled_library_updater()
    return _throttled_library_updater


def initialize_throttled_library_updater() -> ThrottledLibraryUpdater:
    """Initialize the global manga library with optional custom file path"""
    global _throttled_library_updater
    _throttled_library_updater = ThrottledLibraryUpdater()
    return _throttled_library_updater
