import threading
import time

class Throttler:
    def __init__(self, timeout=5):
        self.timeout = timeout
        self.last_call = 0
        self.timer = threading.Timer(0, None)

    def throttled_call(self, func):
        next_call = self.last_call + self.timeout
        time_until_next_call = next_call - time.time()

        def delayed_call():
            func()
            self.last_call = time.time()

        if time_until_next_call <= 0:
            delayed_call()
        else:
            self.timer.cancel()
            self.timer = threading.Timer(time_until_next_call, delayed_call)
            self.timer.start()