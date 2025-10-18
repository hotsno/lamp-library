import os
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, DirCreatedEvent, DirMovedEvent, FileCreatedEvent, DirDeletedEvent, FileDeletedEvent


class MangaFileWatcher(FileSystemEventHandler):
    """
    File watcher for MANGA_PATH directory that monitors:
    - New directory creation
    - Directory renaming
    - Files added to subdirectories
    - Directory deletion
    - File deletion
    """
    
    def __init__(self, manga_path: str):
        self.manga_path = manga_path
        self.observer = Observer()
        self.events_log: List[Dict[str, Any]] = []
        self.is_watching = False
        self._lock = threading.Lock()
        
        # Validate manga path
        if not os.path.exists(manga_path):
            raise ValueError(f"MANGA_PATH directory does not exist: {manga_path}")
        if not os.path.isdir(manga_path):
            raise ValueError(f"MANGA_PATH is not a directory: {manga_path}")
    
    def _log_event(self, event_type: str, path: str, details: Optional[Dict[str, Any]] = None):
        """Log an event with timestamp and details"""
        with self._lock:
            event = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': event_type,
                'path': path,
                'relative_path': os.path.relpath(path, self.manga_path),
                'details': details or {}
            }
            self.events_log.append(event)
            
            # Keep only last 100 events to prevent memory issues
            if len(self.events_log) > 100:
                self.events_log = self.events_log[-100:]
    
    def on_created(self, event):
        """Handle file/directory creation events"""
        if event.is_directory:
            # New directory created
            parent_dir = os.path.dirname(event.src_path)
            if parent_dir == self.manga_path: # Only log directories in the manga path
                self._log_event('directory_created', event.src_path, {
                    'directory_name': os.path.basename(event.src_path)
                })
                print(f"[WATCHER] New directory created: {event.src_path}")
        else:
            # File created in a subdirectory
            parent_dir = os.path.dirname(event.src_path)
            if os.path.dirname(parent_dir) == self.manga_path:  # Only log files in subdirectories of the manga path
                self._log_event('file_added', event.src_path, {
                    'file_name': os.path.basename(event.src_path),
                    'parent_directory': os.path.basename(parent_dir)
                })
                print(f"[WATCHER] File added to subdirectory: {event.src_path}")
    
    def on_moved(self, event):
        """Handle file/directory move/rename events"""
        if event.is_directory:
            # Directory renamed/moved
            old_name = os.path.basename(event.src_path)
            new_name = os.path.basename(event.dest_path)
            
            self._log_event('directory_renamed', event.dest_path, {
                'old_name': old_name,
                'new_name': new_name,
                'old_path': event.src_path
            })
            print(f"[WATCHER] Directory renamed: {old_name} -> {new_name}")
    
    def on_deleted(self, event):
        """Handle file/directory deletion events"""
        if event.is_directory:
            # Directory deleted
            parent_dir = os.path.dirname(event.src_path)
            if parent_dir == self.manga_path:  # Only log directories in the manga path
                self._log_event('directory_deleted', event.src_path, {
                    'directory_name': os.path.basename(event.src_path)
                })
                print(f"[WATCHER] Directory deleted: {event.src_path}")
        else:
            # File deleted in a subdirectory
            parent_dir = os.path.dirname(event.src_path)
            if os.path.dirname(parent_dir) == self.manga_path:  # Only log files in subdirectories of the manga path
                self._log_event('file_deleted', event.src_path, {
                    'file_name': os.path.basename(event.src_path),
                    'parent_directory': os.path.basename(parent_dir)
                })
                print(f"[WATCHER] File deleted from subdirectory: {event.src_path}")
    
    def start_watching(self):
        """Start watching the manga directory"""
        if self.is_watching:
            print("[WATCHER] Already watching")
            return
        
        try:
            self.observer.schedule(self, self.manga_path, recursive=True)
            self.observer.start()
            self.is_watching = True
            self._log_event('watcher_started', self.manga_path, {
                'watch_path': self.manga_path
            })
            print(f"[WATCHER] Started watching: {self.manga_path}")
        except Exception as e:
            print(f"[WATCHER] Error starting watcher: {e}")
            raise
    
    def stop_watching(self):
        """Stop watching the manga directory"""
        if not self.is_watching:
            print("[WATCHER] Not currently watching")
            return
        
        try:
            self.observer.stop()
            self.observer.join()
            self.is_watching = False
            self._log_event('watcher_stopped', self.manga_path)
            print("[WATCHER] Stopped watching")
        except Exception as e:
            print(f"[WATCHER] Error stopping watcher: {e}")
            raise
    
    def get_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent events from the log"""
        with self._lock:
            return self.events_log[-limit:] if limit else self.events_log.copy()
    
    def clear_events(self):
        """Clear the events log"""
        with self._lock:
            self.events_log.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current watcher status"""
        return {
            'is_watching': self.is_watching,
            'watch_path': self.manga_path,
            'total_events': len(self.events_log),
            'last_event': self.events_log[-1] if self.events_log else None
        }


# Global watcher instance
_watcher_instance: Optional[MangaFileWatcher] = None


def get_watcher() -> Optional[MangaFileWatcher]:
    """Get the global watcher instance"""
    return _watcher_instance


def initialize_watcher(manga_path: str) -> MangaFileWatcher:
    """Initialize the global watcher instance"""
    global _watcher_instance
    if _watcher_instance is not None:
        _watcher_instance.stop_watching()
    
    _watcher_instance = MangaFileWatcher(manga_path)
    return _watcher_instance


def start_watcher(manga_path: str):
    """Start the global watcher"""
    global _watcher_instance
    if _watcher_instance is None:
        _watcher_instance = MangaFileWatcher(manga_path)
    
    _watcher_instance.start_watching()


def stop_watcher():
    """Stop the global watcher"""
    global _watcher_instance
    if _watcher_instance is not None:
        _watcher_instance.stop_watching()
