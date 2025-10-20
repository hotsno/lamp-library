import json
import os

from throttler import Throttler

class AutoSaveDict(dict):
    def __init__(self, save_callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.save_callback = save_callback
    
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.save_callback()
    
    def __delitem__(self, key):
        super().__delitem__(key)
        self.save_callback()
    
    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        self.save_callback()
    
    def clear(self):
        super().clear()
        self.save_callback()
    
    def pop(self, *args, **kwargs):
        result = super().pop(*args, **kwargs)
        self.save_callback()
        return result
    
    def popitem(self):
        result = super().popitem()
        self.save_callback()
        return result

class MangaLibraryManager:
    def __init__(self):
        self.file_path = os.path.join(os.path.dirname(__file__), 'manga_library.json')
        self.manga_library = AutoSaveDict(self.save_manga_library, self.load_manga_library())
        self.save_throttler = Throttler(timeout=0.5)
    
    def get_manga_library(self):
        return self.manga_library

    def load_manga_library(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                return json.load(f)
        return {}
    
    def save_manga_library(self):
        def to_throttle():
            with open(self.file_path, 'w') as f:
                json.dump(self.manga_library, f, indent=2)

        self.save_throttler.throttled_call(to_throttle)

manga_library_manager = None

def get_manga_library_manager():
    global manga_library_manager
    if manga_library_manager is None:
        manga_library_manager = MangaLibraryManager()
    return manga_library_manager

def get_manga_library():
    return get_manga_library_manager().get_manga_library()

# manga_library = get_manga_library()
# manga_library['meow'] = 'hi'
# manga_library['meow2'] = 'hi'