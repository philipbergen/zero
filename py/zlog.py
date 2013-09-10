#!/usr/bin/env python
##
# https://github.com/philipbergen/zero
# Licensed under terms of MIT license (see LICENSE-MIT)
# Copyright (c) 2013 Philip Bergen, philip.bergen@me.com

''' USAGE:
      zlog [<config>] (lol|fyi|wtf|omg) <sender> (-|<message> <message>...)

    <sender> is a logical name of emitting party.

    If <message> is -, message lines are read from stdin.
'''

__all__ = ('ZLogger', 'zlogger')
from socket import gethostname
from zero import ZeroSetup, Zero


class ZLogger(object):
    'ZMQ logging object. Caches host and sender. Transmits via a queue to the push Zero.'
    def __init__(self, config, logq, sender, host):
        self.logq = logq
        self.sender = sender
        self.host = host
        for lvl, _ in config['levels']:
            def logout(msg, lvl=lvl):
                'Local function object for dynamic log level functions such as fyi or wtf.'
                self.log(msg, lvl)
            setattr(self, lvl, logout)

    def log(self, msg, level):
        'Formats a message and puts it on the logging queue.'
        self.logq.put(self.format(self.sender, level, msg, self.host))

    @classmethod
    def format(cls, sender, level, msg, host=gethostname(), ts_format='%Y-%m-%dT%H:%M:%S%Z'):
        'Returns a correctly formatted zlog json message.'
        from json import dumps
        from time import strftime
        return dumps([sender, host, level, strftime(ts_format), msg])


def zlogger(config, sender):
    ''' Convenience function for setting up a ZLogger and queue. Returns a ZLogger
        object with .fyi, .wtf, .omg functions as specified in config['log']['levels'].
    '''
    from Queue import Queue
    from threading import Thread
    logq = Queue()
    slog = Zero(ZeroSetup('push', 'tcp://%(host)s:%(port)s' % config).nonblocking())

    def thread(slog=slog):
        for t in iter(logq.get, ''):
            slog(t)
    t = Thread(target=thread)
    t.daemon = True
    t.start()
    return ZLogger(config, logq, sender, gethostname())


def main():
    'For CLI use, see usage in __doc__.'
    import os.path
    from sys import argv, exit
    from json import load
    from os.path import exists
    from itertools import imap
    from collections import deque
    HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    args = deque(argv[1:])
    if len(args) < 3:
        exit(__doc__)
    conf = HERE + '/log.json'
    level = args.popleft()
    if exists(level):
        conf = level
        level = args.popleft()
    with open(conf) as fin:
        conf = load(fin)['log']
    sender = args.popleft()
    if args[0] == '-':
        messages = ZeroSetup.iter_stdin()
    else:
        messages = iter(args)
    messages = imap(lambda x: ZLogger.format(sender, level, x), messages)
    z = Zero(ZeroSetup('push', conf['port']))
    for msg in messages:
        z(msg)


if __name__ == '__main__':
    main()
