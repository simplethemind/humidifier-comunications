from Pyro5.api import locate_ns, Proxy

if __name__ == "__main__":
    input_string = ''
    print('Type "q" to exit')

    serial_server = None
    with locate_ns() as ns:
        uri = ns.lookup('serial_server.serial_connection')
        serial_server = Proxy(uri)
    
    while True:
        input_string = input('Type your command: ')
        if input_string == 'q':
            break
        response = serial_server.post_message(input_string)
        print('Server response is: "' + response + '"')
