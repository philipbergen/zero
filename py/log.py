#!/usr/bin/env python

''' USAGE:
      log.py <config> (debug|info|warning|error) <sender> (-|<message> <message>...)

    <sender> is a logical name of emitting party.

    If <message> is -,message lines are read from stdin.
'''

_log_socket = [0, None, None]
def _get_log_socket(config):
    if _log_socket[0] != config['port'] or _log_socket[1] != config['host']:
        from zmq import PUB, LINGER, Context
        ctx = Context()
        sock = ctx.socket(PUB)
        sock.setsockopt(LINGER, 1000)
        #sock.setsockopt(SNDHWM, 1000)
        sock.connect('tcp://%s:%s' % (config['host'], config['port']))
        _log_socket[0] = config['port']
        _log_socket[1] = config['host']
        _log_socket[2] = sock
    from time import sleep
    sleep(0.2) # Allow time for connect
    return _log_socket[2]

def clear_socket_cache():
    _log_socket[0] = 0
    _log_socket[1] = None
    _log_socket[2] = None

def send_log(config, level, sender, message):
    from socket import gethostname
    from time import strftime
    from json import dumps
    wire = dumps([level, strftime(config['ts-format']), gethostname(), sender, message])
    _get_log_socket(config).send(wire)

def main():
    from sys import argv, stdin
    from json import load
    config = load(open(argv[1]))['log']
    msg = ' '.join(argv[4:])
    if msg == '-':
        msg = stdin.read()
    send_log(config, argv[2], argv[3], msg)
    from time import sleep
    sleep(0.5) # Allow time for egress

if __name__ == '__main__':
    main()
