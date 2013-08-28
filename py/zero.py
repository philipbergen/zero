#!/usr/bin/env python
##
# https://github.com/philipbergen/zero
# Licensed under terms of MIT license (see LICENSE-MIT)
# Copyright (c) 2013 Philip Bergen, philip.bergen@me.com

''' Zero MQ command line interface.

Usage:
    zero [--dbg] (push|req|rep|pub) <socket> [-b] (-|<message> [<message>...])
    zero [--dbg] pull <socket> [-b] [-n MESSAGES]
    zero [--dbg] sub <socket> [-b] [<subscription>...] [-n MESSAGES]

Options:
    -b, --bind      Use bind instead of connect
    -n MESSAGES     Number of messages before exiting [default: inf]
    --dbg           Enables debug output

<socket> is a zmq socket or just a port, in which case the host is assumed to
be localhost. Zmq sockets are things like zmq://*:<port> or
zmq://<hostname>:<port>.

<message> is assumed to be a json formatted message. If multiple <message>
is given each are sent individually. If <message> is -, messages are read
from stdin, the assumption is that each message is contained in a single line.

<subscription> is any string, only messages that start with any of the
subscriptions will be retrieved. Omit this value to subscribe to all messages.
'''
import sys
import zmq

__all__ = ('ZeroSetup', 'Zero', 'zauto')


class ZeroSetup(object):
    ''' Config and input to a zmq socket setup.

        Examples:
         * Setup for pull on port 8000 that gets response messages from stdin
           and prints some debugging info:
            for msg in zero(ZeroSetup('pull', '8000').binding().debugging()):
                print "Got mail:", msg

         * Always reply 'ok' to all req on port 8000:
            for never in zero(ZeroSetup('rep', '8000', itertools.repeat('ok'))\
                              .binding().debugging()):
                pass

         * Always reply 'ok' + msg to all req on port 8000:
            z = Zero(ZeroSetup('rep', '8000').binding().debugging())
            for msg, callback in z:
                print "Got Mail:", msg
                callback("ok " + msg)

          * Sub pub forwarder (Fan in sub@tcp://localhost:8000 to fan out
            pub@tcp://*:8001):
             subscriber = zero(ZeroSetup('sub', '8000').binding())
             publisher = zero(ZeroSetup('pub', '8001', subscriber).binding())
             for n in publisher:
                 print 'This will never print'
    '''

    @classmethod
    def iter_stdin(self):
        from itertools import imap
        return imap(lambda x: x.strip(), iter(sys.stdin.readline, b''))

    @classmethod
    def argv(cls, argv=sys.argv[1:]):
        ''' Interprets argv (sys.argv[1:]) in accordance with the doc for this
            file. Returns a ZeroSetup.

            Methods pub, req, rep and, push require messages input.
        '''
        from docopt import docopt
        args = docopt(__doc__, argv)
        method = [meth for meth in ['push', 'req', 'rep', 'pub', 'pull', 'sub']
                  if args[meth]][0]

        msgloop = None
        if ZeroSetup.method_transmits(method):
            if not args['-']:
                msgloop = args['<message>']
        elif args['-n'] != 'inf':
            msgloop = range(int(args['-n']))
        setup = ZeroSetup(method, args['<socket>'], msgloop)
        setup.binding(args['--bind']).debugging(args['--dbg'])
        if args['<subscription>']:
            setup.subscribing(args['<subscription>'])
        setup.debug(repr(setup))
        return setup

    def __init__(self, method, socket, messageloop=None):
        ''' Creates a setup for zmq, not the actual socket.
            method -- Any ZMQ method (PAIR PUB SUB REQ REP DEALER ROUTER PULL
                                      PUSH XPUB XSUB)
            socket -- A zmq socket or simply a port number
            messageloop -- Determines how long the zmq will run, anything that
                           can be wrapped in iter is fine.
                           Default messageloop is to run forever or, if method
                           is pub, req, rep or push until stdin is empty.
                           For methods that send the message is created from
                           the output of each iteration on messageloop.
        '''
        from itertools import count
        self.zmq_method = getattr(zmq, method.upper())
        self.method = method.lower()
        self._socket = socket
        self._options = []
        if messageloop is None:
            if self.transmits:
                self._options.append('messageloop=stdin.readline')
                self.loop = self.iter_stdin()
            else:
                self._options.append('messageloop=count')
                self.loop = count()
        else:
            self.loop = iter(messageloop)
        self.binding(False).debugging(False)
        self.linger = 1000
        self.blocking = True

    def _debug_off(self, s, *args, **kwarg):
        pass

    def _debug_on(self, s, *args, **kwarg):
        from ansicolor import blu
        if args:
            s = s % args
        if kwarg:
            s = s % kwarg
        for i in range(0, len(s), 95):
            print '>', blu(s[i:i + 95])

    def binding(self, val=True):
        if val:
            self._options.append('(bind)')
        self.bind = val
        return self

    def subscribing(self, heads):
        self._filters = list(iter(heads))
        return self

    def debugging(self, val=True):
        self.debug = self._debug_on if val else self._debug_off
        return self

    def nonblocking(self, val=False):
        self.blocking = not val
        return self

    @classmethod
    def method_transmits(cls, method, tx='push pub req rep'.split()):
        return method in tx

    @property
    def transmits(self):
        return self.method_transmits(self.method)

    @property
    def replies(self):
        return self.method == 'rep'

    @property
    def yields(self, tx='pull sub req rep'.split()):
        return self.method in tx

    @property
    def subscriptions(self):
        if self.method == 'sub':
            for res in getattr(self, '_filters', ['']):
                self.debug('Subscription %r', res)
                yield res

    @property
    def socket(self):
        if self._socket[:1] == ':':
            self._socket = self._socket[1:]
        try:
            int(self._socket)
            if self.bind:
                return 'tcp://*:' + self._socket
            return 'tcp://localhost:' + self._socket
        except ValueError:
            return self._socket

    def __repr__(self):
        return '<ZeroSetup %s %s %s%s%s%s %s>' % (
            self.method, self.socket, list(self.subscriptions),
            ' TX' if self.transmits else '', ' RX' if self.replies else '',
            ' YLD' if self.yields else '', ' '.join(self._options))
    __str__ = __repr__

    def __iter__(self):
        return self

    def next(self):
        return self.loop.next()


class Zero(object):
    'Yields received messages based on supplied ZeroSetup'
    def __init__(self, setup):
        self.setup = setup
        self.sock = zmq.Context().socket(setup.zmq_method)
        if setup.linger:
            self.sock.setsockopt(zmq.LINGER, setup.linger)
        for subsc in setup.subscriptions:
            self.sock.setsockopt(zmq.SUBSCRIBE, subsc)
        if setup.bind:
            self.sock.bind(setup.socket)
        else:
            self.sock.connect(setup.socket)
        setup.debug('Created ZMQ socket %r', setup)
        self.naptime = 0.5
        if self.setup.yields:
            self.recv = self.sock.recv
        
    def send(self, msg=None):
        from time import sleep
        if msg is None and self.setup.loop is not None:
            msg = self.setup.loop.next()
        elif not isinstance(msg, str):
            from json import dumps
            msg = dumps(msg)
        self.setup.debug('Sending %s', msg[:100])
        sleep(self.naptime)  # TODO: Find out how to tell when it is connected
        self.naptime = 0
        tracker = self.sock.send(msg, copy=False, track=True)
        if self.setup.blocking:
            tracker.wait()

    def __repr__(self):
        return 'Zero(%r)' % self.setup

    def __iter__(self):
        return self

    def next(self):
        if self.setup.transmits and not self.setup.replies:
            self.send()
        if self.setup.yields:
            res = self.sock.recv()
            if self.setup.replies:
                return (res, self.send)
            return res
        return None


def zauto(setup):
    'Keep listening and sending til the loop ends.'
    z = Zero(setup)
    try:
        for msg in z:
            if setup.yields:
                if setup.replies:
                    yield msg[0]
                    msg[1]()
                else:
                    yield msg
    except KeyboardInterrupt:
        setup.debug('Quit by user')


def main():
    for msg in zauto(ZeroSetup.argv()):
        sys.stdout.write(msg + '\n')
        sys.stdout.flush()

if __name__ == '__main__':
    main()
