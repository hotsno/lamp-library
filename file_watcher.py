import os
import logging
from datetime import datetime
import time
from dotenv import load_dotenv
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from manga_library import get_manga_library

class MangaFileWatcher(FileSystemEventHandler):
    def __init__(self):
        load_dotenv()
        self.manga_path = os.environ.get('MANGA_PATH')
        self.library_data = get_manga_library()
        self.observer = PollingObserver(timeout=5)
        self.logger = logging.getLogger(__name__)
    
    def _update_manga_directory(self, manga_dir: str):
        try:
            manga_path = os.path.join(self.manga_path, manga_dir)

            if not os.path.exists(manga_path):
                if manga_dir in self.library_data:
                    del self.library_data[manga_dir]
                return
            
            cbz_files = [name for name in os.listdir(manga_path) if name.endswith('.cbz')]
            
            # Update or create manga directory info
            manga_info = self.library_data.get(manga_dir, {})
            manga_info.update({
                'path': manga_path,
                'last_updated': datetime.utcnow().isoformat(),
                'cbz_files': cbz_files,
                'total_chapters': len(cbz_files)
            })
            
            # Set created_at if this is a new directory
            if 'created_at' not in manga_info:
                manga_info['created_at'] = datetime.utcnow().isoformat()
            
            self.library_data[manga_dir] = manga_info
            
        except Exception as e:
            self.logger.error(f"Error updating manga directory {manga_dir}: {e}")
    
    def is_first_level_directory(self, event) -> bool:
        if not event.is_directory:
            return
        
        if hasattr(event, 'dest_path'):
            dest_parent_dir_path = os.path.dirname(event.dest_path)
            if dest_parent_dir_path == self.manga_path:
                return True
        else:
            src_parent_dir_path = os.path.dirname(event.src_path)
            if src_parent_dir_path == self.manga_path:
                return True

        return False

    def is_second_level_file(self, event) -> bool:
        if event.is_directory:
            return
        
        if hasattr(event, 'dest_path'):
            dest_grandparent_dir_path = os.path.dirname(os.path.dirname(event.dest_path))
            if dest_grandparent_dir_path == self.manga_path:
                return True
        else:
            src_grandparent_dir_path = os.path.dirname(os.path.dirname(event.src_path))
            if src_grandparent_dir_path == self.manga_path:
                return True

        return False
    
    def on_created(self, event):
        if self.is_first_level_directory(event):
            manga_dir = os.path.basename(event.src_path)

            self._update_manga_directory(manga_dir)
            self.logger.info(f"New directory created: {event.src_path}")

        elif self.is_second_level_file(event):
            manga_dir = os.path.basename(os.path.dirname(event.src_path))
            file_name = os.path.basename(event.src_path)
            
            if file_name.endswith('.cbz'):
                self._update_manga_directory(manga_dir)

            self.logger.info(f"File added to subdirectory: {event.src_path}")
    
    def on_moved(self, event):
        if self.is_first_level_directory(event):
            old_name = os.path.basename(event.src_path)
            new_name = os.path.basename(event.dest_path)
            
            if old_name in self.library_data:
                manga_info = self.library_data.pop(old_name)
                manga_info['path'] = event.dest_path
                manga_info['last_updated'] = datetime.utcnow().isoformat()
                self.library_data[new_name] = manga_info
            else:
                self._update_manga_directory(new_name)
            
            self.logger.info(f"Directory renamed: {old_name} -> {new_name}")
        elif self.is_second_level_file(event):
            manga_dir = os.path.basename(os.path.dirname(event.src_path))
            old_file_name = os.path.basename(event.src_path)
            new_file_name = os.path.basename(event.dest_path)
            
            if new_file_name.endswith('.cbz'):
                self._update_manga_directory(manga_dir)

            
            self.logger.info(f"File renamed: {old_file_name} -> {new_file_name}")
    
    def on_deleted(self, event):
        if self.is_first_level_directory(event):
            manga_dir = os.path.basename(event.src_path)

            if manga_dir in self.library_data:
                del self.library_data[manga_dir]

            self.logger.info(f"Directory deleted: {event.src_path}")

        elif self.is_second_level_file(event):
            manga_dir = os.path.basename(os.path.dirname(event.src_path))
            file_name = os.path.basename(event.src_path)
            
            if file_name.endswith('.cbz'):
                self._update_manga_directory(manga_dir)
            
            self.logger.info(f"File deleted from subdirectory: {event.src_path}")
    
    def start_watching(self):
        try:
            self.observer.schedule(self, self.manga_path, recursive=True)
            self.observer.start()
            self.logger.info(f"Started watching: {self.manga_path}")
        except Exception as e:
            self.logger.error(f"Error starting watcher: {e}")
            raise

    def stop_watching(self):
        try:
            self.observer.stop()
            self.observer.join()
            self.logger.info("Stopped watching")
        except Exception as e:
            self.logger.error(f"Error stopping watcher: {e}")
            raise

# Global watcher instance
_watcher_instance = None

def initialize_and_start_watcher() -> MangaFileWatcher:
    global _watcher_instance
    if _watcher_instance is not None:
        _watcher_instance.stop_watching()
    
    _watcher_instance = MangaFileWatcher()
    _watcher_instance.start_watching()
    _watcher_instance

if __name__ == '__main__':
    initialize_and_start_watcher()
    while True:
        time.sleep(5)