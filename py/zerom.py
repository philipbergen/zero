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
    def __init__(self, method, point):
        ''' Creates a setup that may be proactive (method is pub/push/req) or reactive 
            (method is sub/pull/rep).
            point -- a port number or a zmq url that is valid for the method.
        '''
        self._method = method
        self.method = getattr(zmq, method.upper())
        self.proactive = self.method in (zmq.PUB, zmq.PUSH, zmq.REQ)
        self.bind = not self.proactive
        self.debug = False
        self._point = point
        self.linger = 1000
        self.block = True
        self.json = True

    @classmethod
    def argv(cls, argv=sys.argv[1:]):
        ''' Interprets argv (sys.argv[1:]) in accordance with the doc for this
            file. Returns a ZeroSetup and an iterator.

            setup, loops = ZeroSetup.argv()
            z = Zero(setup)
            if setup.replies:
                for msg in z:
                    print msg
                    z(loops.next())
            elif setup.transmits:
                for msg in loops:
                    res = z(msg)
                    if setup.yields:
                        print res
            else:
                for _, msg in zip(loops, z):
                    print msg
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
        else:
            msgloop = itertools.count()
        setup = ZeroSetup(method, args['<socket>'], msgloop)
        setup.binding(args['--bind']).debugging(args['--dbg'])
        if args['<subscription>']:
            setup.subscribing(args['<subscription>'])
        setup.debug(repr(setup))
        return setup, msgloop

    def __repr__(self):
        res = ['ZeroSetup(%r, %r)' % (self._method, self._point)]
        if self.bind:
            res.append('.binding()')
        if self.debug:
            res.append('.debugging()')
        if not self.block:
            res.append('.nonblocking()')
        if not self.json:
            res.append('.raw()')
        if list(self.subscriptions):
            res.append('.subscribing(%s)' % ''.join(self.subscriptions()))
        if hasattr(self, 'rpc'):
            res.append('.activated(%r)' % self.rpc)
    __str__ = __repr__

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
        self.block = not val
        return self

    def raw(self, val=False):
        self.json = not val
        return self

    def activated(self, zerorpc):
        self.rpc = zerorpc

    @property
    def subscriptions(self):
        if self.method == 'sub':
            for res in getattr(self, '_filters', ['']):
                self.debug('Subscription %r', res)
                yield res

    @property
    def point(self):
        if self._point[:1] == ':':
            self._point = self._point[1:]
        try:
            int(self._point)
            if self.bind:
                return 'tcp://*:' + self._point
            return 'tcp://localhost:' + self._point
        except ValueError:
            return self._point

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
    def active(self):
        return hasattr(self, 'rpc')

class ZeroRPC(object):
    ''' Inherit and implement your own methods on from this.
        Then supply to ZeroSetup:

        ZeroSetup('pull', '8000').activated(ZeroRPC())
    '''
    def __call__(self, obj):
        'Calls the method from obj (always of the form [<method name>, {<kwargs>}]).'
        if not hasattr(self, obj[0]):
            return self._unsupported(obj[0], **obj[1])
        return getattr(self, obj[0])(**obj[1])

    def _unsupported(self, func, **kwargs):
        return ['UnsupportedFunc', func, kwargs] 

           
class Zero(object):
    ''' ZMQ wrapper object that gets its setup from ZeroSetup.
        
        # To PUB a number of objects (push is the same, except 'push' method):

        z = Zero(ZeroSetup('pub', '8000'))
        for obj in objects:
            z(obj)

        # To make a number of REQ calls:

        z = Zero(ZeroSetup('pub', '8000'))
        res = list(itertools.imap(z, objects))

        # To print objects from a PULL (or sub):

        z = Zero(ZeroSetup('pull', '8000').binding())
        for obj in z:
            print obj

        # To REP twice the sent object

        z = Zero(ZeroSetup('rep', '8000').binding())
        for obj in z:
            z(2*obj)
    '''

    def __init__(self, setup):
        self.setup = setup
        if not hasattr(setup, ctx):
            setup.ctx = zmq.Context()
        self.sock = setup.ctx.socket(setup.method)
        if setup.linger:
            self.sock.setsockopt(zmq.LINGER, setup.linger)
        for subsc in setup.subscriptions:
            self.sock.setsockopt(zmq.SUBSCRIBE, subsc)
        if setup.bind:
            self.sock.bind(setup.point)
        else:
            self.sock.connect(setup.point)
        setup.debug('Created ZMQ socket %r', self)
        self.naptime = 0.5
        if not setup.json:
            self._decode = lambda x:x
            self._encode = self._decode

    def __repr__(self):
        return 'Zero(%r)' % self.setup
    __str__ = __repr__

    from json import loads, dumps
    _decode = loads
    _encode = dumps

    def __iter__(self):
        return self

    def next():
        ''' Blocks regardless of self.setup.block. If method is rep,
            must send reply before going to next().
        '''
        res = self._decode(self.sock.recv())
        if self.setup.active:
            return self.setup.rpc(res)
        return res

    def __call__(self, obj):
        ''' Send and block while waitingfor response, unless not self.setup.block
            (the caller must call .next(), before sending the next message).
        '''
        self.send(obj)
        if self.method == zmq.REQ and self.setup.block:
            return self.next()

    def send(self, obj):
        from time import sleep
        msg = self._encode(obj)
        self.setup.debug('Sending %s', msg[:100])
        sleep(self.naptime)  # TODO: Find out how to tell when it is connected
        self.naptime = 0
        tracker = self.sock.send(msg, copy=False, track=True)
        if self.setup.blocking:
            tracker.wait()


def zauto(setup, loops):
    'Keep listening and sending til the loop ends.'
    try:
        z = Zero(setup)
        if setup.replies:
            for msg in z:
                print msg
                z(loops.next())
        elif setup.transmits:
            for msg in loops:
                res = z(msg)
                if setup.yields:
                    print res
        else:
            for _, msg in zip(loops, z):
                print msg
    except KeyboardInterrupt:
        setup.debug('Quit by user')


def main():
   for msg in zauto(*ZeroSetup.argv()):
        sys.stdout.write(msg + '\n')
        sys.stdout.flush()

if __name__ == '__main__':
    main()
