#!/usr/bin/env python
##
# https://github.com/philipbergen/zero
# Licensed under terms of MIT license (see LICENSE-MIT)
# Copyright (c) 2013 Philip Bergen, philip.bergen@me.com

''' Zero MQ command line interface.
sub push req: connect
Usage:
    zero [--dbg] (pub|rep) <socket> [-c] (-|<message> [<message>...])
    zero [--dbg] (push|req) <socket> [-b] (-|<message> [<message>...])
    zero [--dbg] pull <socket> [-c] [-n MESSAGES]
    zero [--dbg] sub <socket> [-b] [<subscription>...] [-n MESSAGES]
    zero test [-v]

Options:
    -b, --bind      Use bind instead of connect
    -c, --connect   Use connect instead of bind
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
import json

__all__ = ('ZeroSetup', 'Zero', 'ZeroRPC', 'zauto')


class ZeroSetup(object):
    ''' Simplifies 0MQ use and setup. Use with Zero, see below.

        >>> ZeroSetup('pull', 8000)
        ZeroSetup('pull', 8000).binding(True)
        >>> ZeroSetup('push', 8000)
        ZeroSetup('push', 8000).binding(False)
        >>> ZeroSetup('sub', 8000)
        ZeroSetup('sub', 8000).binding(False).subscribing([''])
        >>> ZeroSetup('pub', 8000)
        ZeroSetup('pub', 8000).binding(True)
        >>> ZeroSetup('req', 8000)
        ZeroSetup('req', 8000).binding(False)
        >>> ZeroSetup('rep', 8000)
        ZeroSetup('rep', 8000).binding(True)
    '''
    def __init__(self, method, point):
        ''' Creates a setup that may be proactive (method is pub/push/req) or reactive
            (method is sub/pull/rep).
            point -- a port number or a zmq url that is valid for the method.
        '''
        self._method = method
        self.method = getattr(zmq, method.upper())
        self.bind = not self.method in (zmq.SUB, zmq.PUSH, zmq.REQ)
        self.debugging(False)
        self._point = point
        self.linger = 1000
        self.block = True

    @classmethod
    def argv(cls, argv=sys.argv[1:]):
        ''' Interprets argv (sys.argv[1:]) in accordance with the doc for this
            file. Returns a ZeroSetup and an iterator.

            setup, loops = ZeroSetup.argv()
            zauto(setup, loops)

            >>> setup, loop = ZeroSetup.argv('--dbg push 8000 -b alpha beta charlie'.split())
            > \x1b[34mZeroSetup('push', '8000').binding(True).debugging()\x1b[0m
            >>> setup
            ZeroSetup('push', '8000').binding(True).debugging()
            >>> ' '.join(loop)
            'alpha beta charlie'
            >>> setup, loop = ZeroSetup.argv('pull 8000 -c -n 3'.split())
            >>> setup
            ZeroSetup('pull', '8000').binding(False)
            >>> list(loop)
            [0, 1, 2]
        '''
        from docopt import docopt
        from itertools import count
        args = docopt(__doc__, argv)
        method = [meth for meth in ['push', 'req', 'rep', 'pub', 'pull', 'sub']
                  if args[meth]][0]

        setup = ZeroSetup(method, args['<socket>']).debugging(args['--dbg'])
        if args['--bind']:
            setup.binding(True)
        if args['--connect']:
            setup.binding(False)
        if args['<subscription>']:
            setup.subscribing(args['<subscription>'])
        setup.debug('%r', setup)

        msgloop = None
        if setup.transmits:
            if not args['-']:
                msgloop = args['<message>']
        elif args['-n'] != 'inf':
            msgloop = range(int(args['-n']))
        else:
            msgloop = count()
        return setup, msgloop

    def __repr__(self):
        res = ['ZeroSetup(%r, %r)' % (self._method, self._point)]
        res.append('.binding(%s)' % self.bind)
        if self.debug == self._debug_on:
            res.append('.debugging()')
        if not self.block:
            res.append('.nonblocking()')
        if self.subscriptions:
            res.append('.subscribing(%r)' % self.subscriptions)
        return ''.join(res)
    __str__ = __repr__

    def _debug_off(self, s, *args, **kwarg):
        'Does nothing. For debug == False.'
        pass

    def _debug_on(self, s, *args, **kwarg):
        'Interpolates s with args/kwarg and prints on stdout, when debug == True.'
        from ansicolor import blu
        if args:
            s = s % args
        if kwarg:
            s = s % kwarg
        for i in range(0, len(s), 95):
            print '>', blu(s[i:i + 95])

    def binding(self, val=True):
        ''' Switches from socket.connect to socket.bind.
            >>> setup = ZeroSetup('pull', 8000)
            >>> setup.point
            'tcp://*:8000'
            >>> setup.binding(False).point
            'tcp://localhost:8000'
        '''
        self.bind = val
        return self

    def subscribing(self, heads):
        ''' Sets the subscription strings for SUB sockets.
            >>> setup = ZeroSetup('sub', 8000)
            >>> setup
            ZeroSetup('sub', 8000).binding(False).subscribing([''])
            >>> setup.subscribing(['test:', 'error:'])
            ZeroSetup('sub', 8000).binding(False).subscribing(['test:', 'error:'])
        '''
        if self.method == zmq.SUB:
            self._filters = list(iter(heads))
        else:
            raise ValueError('Only zmq.SUB accepts subscriptions (%r)' % self)
        return self

    def debugging(self, val=True):
        ''' Turns debug output on/off.
            >>> ZeroSetup('push', 8000).debugging()
            ZeroSetup('push', 8000).binding(False).debugging()
        '''
        self.debug = self._debug_on if val else self._debug_off
        return self

    def nonblocking(self, val=False):
        'Switches blocking sends, calls.'
        self.block = not val
        return self

    @property
    def subscriptions(self):
        ''' Yields subscription topics.
            >>> ZeroSetup('pull', 8000).subscribing(['test:', 'error:']).subscriptions
            Traceback (most recent call last):
                ...
            ValueError: Only zmq.SUB accepts subscriptions (ZeroSetup('pull', 8000).binding(True))
        '''
        if self.method == zmq.SUB:
            return getattr(self, '_filters', [''])
        return []

    @property
    def point(self):
        ''' Returns the ZMQ socket string.
            >>> ZeroSetup('pull', 'tcp://other.host.net:9000')
            ZeroSetup('pull', 'tcp://other.host.net:9000').binding(True)
        '''
        if str(self._point)[:1] == ':':
            self._point = self._point[1:]
        try:
            int(self._point)
            if self.bind:
                return 'tcp://*:%s' % self._point
            return 'tcp://localhost:%s' % self._point
        except ValueError:
            return self._point

    @property
    def transmits(self):
        'True if the method member is a sending kind.'
        return self.method in (zmq.PUSH, zmq.PUB, zmq.REQ, zmq.REP)

    @property
    def replies(self):
        'True if method is zmq.REP'
        return self.method == zmq.REP

    @property
    def yields(self):
        'True if method receives objects.'
        return self.method in (zmq.PULL, zmq.SUB, zmq.REQ, zmq.REP)


class ZeroRPC(object):
    ''' Inherit and implement your own methods on from this.
        Then supply to ZeroSetup:

        ZeroSetup('pull', '8000').activated(ZeroRPC())


        >>> class Z(ZeroRPC):
        ...     def hi(self):
        ...         return "hello"
        ...     def sqr(self, x):
        ...         return x*x
        >>> def lstn():
        ...     zauto(ZeroSetup.argv('rep 8800 hi'.split())).activated(Z())
        >>> 
        
    '''
    def __call__(self, obj):
        'Calls the method from obj (always of the form [<method name>, {<kwargs>}]).'
        if obj[0][:1] == '_':
            raise Exception('Method not available')
        if len(obj) == 1:
            obj = [obj[0], []]
        if not hasattr(self, obj[0]):
            return self._unsupported(obj[0], **obj[1])
        return getattr(self, obj[0])(**obj[1])

    def _unsupported(self, func, **kwargs):
        'Catch-all method for when the object received does not fit.'
        return ['UnsupportedFunc', func, kwargs]


class Zero(object):
    ''' ZMQ wrapper object that gets its setup from ZeroSetup.

        # To PUB a number of objects (push is the same, except 'push' method):

        z = Zero(ZeroSetup('pub', 8000))
        for obj in objects:
            z(obj)

        # To make a number of REQ calls:

        z = Zero(ZeroSetup('req', 8000))
        res = map(z, objects)

        # To print objects from a PULL (or sub):

        z = Zero(ZeroSetup('pull', 8000).binding())
        for obj in z:
            print obj

        # To REP twice the sent object

        z = Zero(ZeroSetup('rep', 8000).binding())
        for obj in z:
            z(2*obj)
    '''

    def __init__(self, setup):
        self.setup = setup
        if not hasattr(setup, 'ctx'):
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
        self.marshals()
        setup.debug('Created ZMQ socket %r', self)
        self.naptime = 0.5

    def marshals(self, encode=json.dumps, decode=json.loads):
        ''' Set automatic marshalling functions. Example for raw input:
            Zero(setup).marshals(lambda x: x)
        '''
        self._encode = encode
        self._decode = decode
        return self

    def activated(self, zerorpc):
        ''' Sets an ZeroRPC object that gets called when messages are received.
            >>> Zero(ZeroSetup('push', 8000)).activated(iter([]).next) # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            ValueError: ('Only setups that yield can be activated', ...)
            >>> Zero(ZeroSetup('pull', 8000)).activated(1) # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            ValueError: ('Objects used for activation must be callable', ...)
        '''
        if not self.setup.yields:
            raise ValueError('Only setups that yield can be activated', self)
        if not callable(zerorpc):
            raise ValueError('Objects used for activation must be callable', self, zerorpc)
        self.rpc = zerorpc
        return self

    def __repr__(self):
        res = ['Zero(%r)' % self.setup]
        if self._encode != json.dumps or self._decode != json.loads:
            res.append('.marshals(%r, %r)' % (self._encode, self._decode))
        if hasattr(self, 'rpc'):
            res.append('.activated(%r)' % self.rpc)
        return ''.join(res)
    __str__ = __repr__

    def __iter__(self):
        return self

    def next(self):
        ''' Blocks regardless of self.setup.block. If method is rep,
            must send reply before going to next().
        '''
        res = self._decode(self.sock.recv())
        if self.active:
            return self.rpc(res)
        return res

    def __call__(self, obj):
        ''' Send and block while waitingfor response, unless not self.setup.block
            (the caller must call .next(), before sending the next message).
        '''
        self.send(obj)
        if self.setup.method == zmq.REQ and self.setup.block:
            return self.next()

    def send(self, obj):
        from time import sleep
        msg = self._encode(obj)
        self.setup.debug('Sending %s', msg[:100])
        sleep(self.naptime)  # TODO: Find out how to tell when it is connected
        self.naptime = 0
        tracker = self.sock.send(msg, copy=False, track=True)
        if self.setup.block:
            tracker.wait()

    @property
    def active(self):
        return hasattr(self, 'rpc')


def zauto(setup, loops):
    'Keep listening and sending until the loop ends. All received objects are yielded.'
    try:
        z = Zero(setup)
        if setup.replies:
            loops = iter(loops)
            for msg in z:
                yield msg
                z(loops.next())
        elif setup.transmits:
            for msg in loops:
                res = z(msg)
                if setup.yields:
                    yield res
        else:
            for _, msg in zip(loops, z):
                yield msg
    except KeyboardInterrupt:
        setup.debug('Quit by user')
    except StopIteration:
        setup.debug('Loop ended')


def zbg(setup, loop, callback):
    ''' Use to daemonize zauto in a background thread.
        >>> import Queue
        >>> q = Queue.Queue()
        >>> t = zbg(*ZeroSetup.argv('rep 8000 hello'), callback=q.put)
        >>> list(zauto(*ZeroSetup.argv('req 8000 hi')))
        [u'hello']
    '''
    def tloop(setup, loop, callback):
        for obj in zauto(setup, loop):
            callback(obj)
    from threading import Thread
    t = Thread(name='zbg %r' % setup, target=tloop, args=(setup, loop, callback))
    t.daemon = True
    t.start()
    return t

    
def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        import doctest
        return doctest.testmod()
        
    for msg in zauto(*ZeroSetup.argv()):
        sys.stdout.write(msg + '\n')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
