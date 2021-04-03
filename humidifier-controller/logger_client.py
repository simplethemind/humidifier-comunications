import sys
from Pyro5.api import Proxy
import os
import datetime
from threading import Thread, Event, enumerate

class Logger():
    def __init__(self, log_to_file = True):
        self._exit = Event()
        self.do_job(log_to_file)

    def stop(self):
        self._exit.set()

    def do_job(self, log_to_file = True):
        with Proxy('PYRONAME:serial_server.serial_connection') as serial_connection:
            
            filename = os.path.basename(serial_connection.connection_name) + '_' + datetime.datetime.now().strftime('%Y.%m.%d_%H.%M.%S') + '.csv'

            logs_folder = os.path.join(serial_connection.working_directory,'logs')
            
            try:
                os.makedirs(logs_folder)
            except OSError:
                pass
            full_filepath = os.path.join(logs_folder, filename)


            while not self._exit.is_set():
                serial_line = serial_connection.post_message('sr')
                serial_line = serial_line[:-2]
                timestamp_line = datetime.datetime.now().strftime('%x %X')
                print('Returned data: "' + timestamp_line + ',' + serial_line + '"')
                if log_to_file:
                    if not os.path.exists(full_filepath):
                        with open(full_filepath, 'x') as f:
                            f.write('t,0,1,2\r\n')
                    with open(full_filepath, 'a') as f:
                        f.write(timestamp_line + "," + serial_line + '\r\n')

                delay = serial_connection.delay
                print('Sleeping for ' + str(delay))
                self._exit.wait(delay)


def signal_handler(signo, frame):
    logger_threads = [thread for thread in enumerate() if isinstance(thread, Logger)]
    for logger_thread in logger_threads:
        print("Stopping {}.".format(logger_thread))
        logger_thread.stop()
    sys.exit(1)
        
if __name__ == "__main__":
    t = Thread(target=Logger)

    import signal
    for sig in ('TERM', 'HUP', 'INT'):
        signal.signal(getattr(signal, 'SIG'+sig), signal_handler)

    t.start()