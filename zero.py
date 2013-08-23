#!/usr/bin/env python
##
# https://github.com/philipbergen/zero
# Licensed under terms of MIT license (see LICENSE-MIT)
# Copyright (c) 2013 Philip Bergen, philip.bergen@me.com

''' Zero MQ command line interface.

Usage:
    0q [--dbg] (push|req|rep|pub) <socket> [-b] [--raw] (-|<message> [<message>...])
    0q [--dbg] pull <socket> [-b] [-n MESSAGES]
    0q [--dbg] sub <socket> [-b] [<subscription>...] [-n MESSAGES]

Options:
    -b, --bind      Use bind instead of connect
    -n MESSAGES     Number of messages before exiting [default: 1]
    --raw           Sends messages exactly like they are, prevents JSON validation
    --dbg           Enables debug output

<socket> is a zmq socket or just a port, in which case the host is assumed to be
localhost. Zmq sockets are things like zmq://*:<port> or zmq://<hostname>:<port>.

<message> is assumed to be a json formatted message. If multiple <message>
is given each are sent individually. If <message> is -, messages are read
from stdin, the assumption is that each message is contained in a single line.

<subscription> is any string, only messages that start with any of the subscriptions
will be retrieved. Omit this value to subscribe to all messages.

'''
import sys



def zero_args(argv=None):
    ''' Interprets argv (sys.argv[1:]) in accordance with the doc for this file.
        Returns an args dict for zero.
    '''
    from docopt import docopt
    args = docopt(__doc__, argv)
    res =
    if args['-n'] != 'inf':
        args['-n'] = int(args['-n'])
    try:
        int(args['<socket>'])
        if args['--bind']:
            args['<socket>'] = 'tcp://*:' + args['<socket>']
        else:
            args['<socket>'] = 'tcp://localhost:' + args['<socket>']
        if args['--dbg']:
            print '--> Set the socket to', args['<socket>']
    except ValueError:
        pass
    methods = ['push', 'req', 'rep', 'pub', 'pull', 'sub']
    args['<method>'] = [meth for meth in methods if args[meth]][0]
    if args['<message>'] and not args['--raw']:
        import json
        for n, msg in enumerate(args['<message>']):
            try:
                ob = json.loads(msg)
            except ValueError, e:
                if args['--dbg']:
                    print '--> Parsing message %d failed (%s): %s' % (n, e, msg)
                raise                    
            if args['--dbg']:
                print '--> Message %d: %r' % (n, ob)
    if args['--dbg']:
        print '--> Arguments:', args['<socket>'], '-b' if args['--bind'] else '', \
            args['<method>'], args['<subscription>'], '-n', args['-n'], \
            '--raw' if args['--raw'] else '', args['<message>'] if not args['-'] else '-'
    return args

def zero(args):
    ''' Yields received messages while performing the method in args. 
        args -- as returned from zero_args
    '''
    def sock(ctx, args):
        zmq_const = getattr(zmq, args['<method>'].upper())
        if args['--dbg']:
            print '--> ZMQ Method %s (%s)' % (args['<method>'], zmq_const)
        res = ctx.socket(zmq_const)
        res.setsockopt(zmq.LINGER, 1000)
        if args['<method>'] == 'sub':
            if not args['<subscription>']:
                if args['--dbg']:
                    print '--> Subscribing to all messages'
                res.setsockopt(zmq.SUBSCRIBE, '')
            else:
                for subsc in args['<subscription>']:
                    if args['--dbg']:
                        print '--> Subscribing to', subsc
                    res.setsockopt(zmq.SUBSCRIBE, subsc)
        if args['--bind']:
            res.bind(args['<socket>'])
        else:
            res.connect(args['<socket>'])
        return res
        
    def send(s, args, n, msg):
        if not args['--raw']:
            msg = msg.strip()
        if args['--dbg']:
            print '--> Sending (%d)' % n, msg
        tracker = s.send(msg, copy=False, track=True)
        tracker.wait()

    from itertools import count
    method = args['<method>']
    loop = args['<message>']
    if method in ['pull', 'sub']:
        if args['-n'] == 'inf':
            loop = count()
        else:
            loop = xrange(args['-n'])
    elif args['-']:
        loop = iter(sys.stdin.readline, b'')
    try:
        import zmq
        from time import sleep
        ctx = zmq.Context()
        s = sock(ctx, args)
        for n, msg in enumerate(loop):
            if method in ['push', 'pub', 'req']:
                if not n:
                    sleep(0.1) # TODO: Find out how to tell when it is connected
                send(s, args, n, msg)
            if method in ['req', 'rep', 'pull', 'sub']:
                yield s.recv()
                if method == 'rep':
                    send(s, args, n, msg)
    except KeyboardInterrupt:
        if args['--dbg']:
            print '--> Quit by user'

def main():
    for msg in zero(zero_args()):
        sys.stdout.write(msg + '\n')
        sys.stdout.flush()

if __name__ == '__main__':
    main()
