import time

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers.polling import PollingObserver
import threading

class MyEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        print('meow')

    def on_any_event(self, event: FileSystemEvent) -> None:
        print(event)
        print(observer._event_queue.qsize())


event_handler = MyEventHandler()
observer = PollingObserver(timeout=5)
observer.schedule(event_handler, ".", recursive=True)
observer.start()
try:
    while True:
        time.sleep(1)
finally:
    observer.stop()
    observer.join()
