import threading
import time
import signal
import sys

class Controller(object):
    def __init__(self, name="controller", interval=1):
        self.name = name
        self.interval = interval

    def job(self):
        print("My name is {}.".format(self.name))


class ThreadController(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(ThreadController, self).__init__()
        self.controller = Controller(*args, **kwargs)
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.is_set()

    def run(self):
        while not self.stopped():
            self.controller.job()
            self._stop.wait(1)


def signal_handler(signum, frame):
    controller_threads = [thread for thread in threading.enumerate() if isinstance(thread, ThreadController)]
    for controller_thread in controller_threads:
        print("Stopping {}.".format(controller_thread))
        controller_thread.stop()
    sys.exit(1)

if __name__ == "__main__":
    controller1 = ThreadController(name="foo")
    controller2 = ThreadController(name="bar")

    signal.signal(signal.SIGINT, signal_handler)

    controller1.start()
    controller2.start()

    while True: 
        pass