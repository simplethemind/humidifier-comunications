import serial
import os
import sys
from Pyro5.api import expose, Daemon, behavior, locate_ns, start_ns, config
from .logger_client import Logger
import json

@behavior(instance_mode='single')
class SerialConnection:
    def __init__(self, port='', baudrate='9600', reboot=True):
        self._delay = 60.0
        self._serial = SerialConnection.open_serial_port(port, baudrate, reboot)
        print('Opened serial connection to ' + self._serial.name)
        serial_line = ''
        while serial_line == '':
            serial_line = self._serial.readline().decode('utf-8')
        print('<<< ' + serial_line)

    @expose
    def post_message(self, message):
        if message.startswith('log'):
            self._delay = int(message[3:])/1000
            return 'Set logging timer to ' + str(self._delay) + ' seconds.'
        else:
            return self.post_serial_message(message)

    def post_serial_message(self, message):
        serial_line = ''
        while self._serial.in_waiting != 0:
            serial_line = self._serial.readline().decode('utf-8')
            print('<<< (old) ' + serial_line)

        print('>>> ' + message)
        self._serial.write(bytes(message + '\r\n', 'ascii'))
        self._serial.flush()

        # Waiting for response. Timeout after value set in open_serial_port
        serial_line = self._serial.readline().decode('utf-8') 
        print('<<< ' + serial_line[:-1])
        return serial_line

    @expose
    @property
    def delay(self):
        return self._delay

    @expose
    @property
    def connection_name(self):
        return self._serial.name

    @expose
    @property
    def working_directory(self):
        return os.getcwd()

    @expose
    def get_settings(self):
        # get the values reported by the arduino program
        json_response = self.post_serial_message('stat')
        response = json.loads(json_response)
        # report the delay currenty used on the server
        response['log_delay'] = self.delay
        # add followning values from saved json
        read_values = self.read_settings()
        for num in range(3):
            try:
                num = str(num)
                response['sensor' + num]['plant_label'] = read_values['sensor' + num]['plant_label']
            except:
                pass
    
        return response

    @expose
    def set_settings(self, values):
        try:
            self._delay = float(values['log_delay'])
            self.post_serial_message('rel' + values['relay_cooldown'])
            for i in range(3):
                num = str(i)
                self.post_serial_message('v' + num + 'M' + str(values['sensor'+num]['zero_humidity']))
                self.post_serial_message('v' + num + 'm' + str(values['sensor'+num]['full_humidity']))
                self.post_serial_message('v' + num + 's' + str(values['sensor'+num]['relay_start']))
                self.post_serial_message('v' + num + 'r' + str(values['sensor'+num]['relay_duration']))
            with open(os.path.join(self.working_directory, 'settings.json'), 'w') as f:
                f.write(json.dumps(values, indent=4))
        except:
            pass

    def read_settings(self):
        values = {}
        settings_path = os.path.join(self.working_directory, 'settings.json')
        try:
            with open(settings_path, 'r') as f:
                values = json.loads(f.read())
        except:
            pass
        return values

    def __del__(self):
        self._serial.close()
        print("serial port closed")

    def open_serial_port(port='', baudrate='9600', reboot=True):
        if port  == '':
            dir = os.listdir('/dev')

            ### Use this on raspberry pi systems if using arduino nano ###
            for path in dir:
                if 'USB' in path:
                    port = os.path.join('/dev', path)

        serialComm = serial.Serial(port=port, baudrate=baudrate, timeout=2)
        if reboot:
            serialComm.dtr = False
            serialComm.rts = False
            from time import sleep
            sleep(0.2)
            serialComm.dtr = True
            serialComm.rts = True
        serialComm.flush()
        return serialComm


def main(log_to_file = True):

    import pkg_resources
    version = pkg_resources.require('humidifier-controller')[0].version
    print('Starting Humidifier Controller Server, version: ' + version)

    config.SERVERTYPE = 'multiplex'
    daemon = Daemon()

    def start_client_logger():
        from threading import Thread
        t = Thread(target=Logger, kwargs={'log_to_file': log_to_file}, daemon=True)
        t.start()
        return t

    def signal_handler(signo, frame):
        if daemon != None:
            daemon.transportServer.shutting_down = True
            print(f'Shutting down gracefully exit code: {signo}')
            daemon.shutdown()

        from threading import enumerate
        logger_threads = [thread for thread in enumerate() if isinstance(thread, Logger)]
        for logger_thread in logger_threads:
            print("Stopping {}.".format(logger_thread))
            logger_thread.stop()
        sys.exit(1)

    import signal
    for sig in ('TERM', 'HUP', 'INT'):
        signal.signal(getattr(signal, 'SIG'+sig), signal_handler)

    nameserverDaemon = None
    try:
        nameserverUri, nameserverDaemon, broadcastServer = start_ns()
        assert broadcastServer is not None, "expect a broadcast server to be created"
        print("got a Nameserver, uri=%s" % nameserverUri)
    except OSError:
        print('Pyro nameserver already running. No idea who started it.')
    
    if (nameserverDaemon == None):
        with locate_ns() as ns:
            try:
                ns.lookup('serial_server.serial_connection')
                print("Serial server is already registered. Aborting.")
                return 0
            except:
                pass
    
    serial_connection = SerialConnection(baudrate='9600')
    serial_connection.set_settings(serial_connection.read_settings())
    serial_connection.post_message('\0')

    serial_uri = daemon.register(serial_connection)
    if (nameserverDaemon == None):
        with locate_ns() as ns:
            ns.register('serial_server.serial_connection', serial_uri)
    else:
        nameserverDaemon.nameserver.register('serial_server.serial_connection', serial_uri)
        daemon.combine(nameserverDaemon)
        daemon.combine(broadcastServer)
    print('Serial connection registered.')
    start_client_logger()
    daemon.requestLoop()


if __name__ == "__main__":
    main()