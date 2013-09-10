zero
====

Zero MQ wrapper that makes it trivial to set up [0MQ](http://zeromq.org/)
connections. A wrapper for a wrapper... Does that make any sense? Well, to me
it did, since the [pyzmq](https://github.com/zeromq/pyzmq) wrapper tries to
stay very close to the reference C implementation.

zero tries to be simpler to use. It doesn't supply all of the fine aspects and
features of 0MQ, (though they are available through member variables `ctx` and
`sock`). Instead it aims to make 0MQ messaging trivial.

You can even get access to it all through a command line interface. Very useful
for testing 0MQ even if you are not writing your program in python at all.

Example, a server that pulls messages (fan-in) and publishes a stream of them
(fan-out):

```bash
zero pull 8000 | zero pub 8001 -
```

Installation
------------
I have developed on a Mac. This should work on all unix, but the installer will
only help you install zeromq and python using homebrew, so if your platform is
not OS X, you will need to install libzmq and python manually first.

If you need to do that, the installer will instaruct you so.

    ./install.sh
    . ./env.sh

Command line interface
----------------------

Overall usage (see complete with `zero -h`):

    zero [--dbg] [--wait] (pub|rep) <socket> [-c] (-|<message> [<message>...])
    zero [--dbg] [--wait] (push|req) <socket> [-b] (-|<message> [<message>...])
    zero [--dbg] [--wait] pull <socket> [-c] [-n MESSAGES]
    zero [--dbg] [--wait] sub <socket> [-b] [<subscription>...] [-n MESSAGES]

    Options:
	-b, --bind      Use bind instead of connect
	-c, --connect   Use connect instead of bind
        --wait          Waits for user input at the end of the program, before quitting
        -n MESSAGES     Number of messages before exiting [default: inf]
        --dbg           Enables debug output

### Push-pull

The simplest is a fan-in push-pull:

    # Terminal 1, binds
    zero pull 8000

    # Terminal 2, connects
    zero push 8000 "Hello world"

To make a fan out push-pull (useful for distributing work):

    # Terminal 1, binds
    zero pull 8000 -c

    # Terminal 2, connects
    zero push 8000 -b "Hello world"

### Pub-sub

Fan-out pub-sub:

    # Terminal 1, binds
    zero pub 8000 alpha polka baton appel

    # Terminal 2, connects
    zero sub 8000

Fan-out pub-sub with subscriber filter:

    # Terminal 1, binds
    zero pub 8000 alpha polka baton appel

    # Terminal 2, connects, subscribes to strings that start with a and b.
    zero sub 8000 '"a'" '"b'

### Req-rep

    # Terminal 1, binds, replies "hola":
    zero --dbg rep 8000 hola

    # Terminal 2, connects, asks "que":
    zero --dbg req 8000 que

Python API
----------

Default marshalling is json. Marshalling is configurable. See below
for more information. All examples assume `from zero import *`.

### Push-pull fan-in

Useful for workers feeding status messages or objects to a persistence.
E.g. logfile writer.

```python
# The pull (bind) server
zero = Zero(ZeroSetup('pull', 8000))
for msg in zero:
    zero.setup.warn('Pulled %s', msg)
``` 

```python
# The push (connect) client, with debugging on, so that it is visible
# what the client is doing. Connects to localhost.
zero = Zero(ZeroSetup('push', 8000).debugging())
for msg in ['alpha', 'beta', 'gamma']:
    zero(msg)
```

### Push-pull fan-out

Useful for distributing work from a server to multiple workers. Combines
well with RPC, see below.

```python
# The push (bind) server
zero = Zero(ZeroSetup('push', 8000).binding().debugging())
for work in range(1000):
    # Insert a sleep here for testing
    zero(work)
``` 

```python
# The pull (connect) client, each client gets a message from the push 
# in round robin fashion.
zero = Zero(ZeroSetup('push', 8000).binding(False))
for msg in zero:
    print "Doing work %s" % msg
```

### Pub-sub fan-out

The most common for feeding a large number of listeners a stream of
messages.

```python
# The pub (bind) server
zero = Zero(ZeroSetup('pub', 8000))
for msg in ['alpha', 'beta', 'gamma']:
    zero(msg)
```

```python
# The sub (connect) client
zero = Zero(ZeroSetup('sub', 8000))
for msg in zero:
    zero.setup.warn('Published %s', msg)
```

If you want to filter messages you subscribe to then remember that
messages are json encoded. The example here assumes that messages of
interest are lists with a string level as the first element.

```python
# The sub (connect) client
zero = Zero(ZeroSetup('sub', 8000).subscribing(['["error"', '["warning"']))
for msg in zero:
    zero.setup.warn('Published %s', msg)
```

### Req-rep

RPC style calls. Simplest form just replies to input, such as this
doubler service:

```python
# The rep (bind) server
zero = Zero(ZeroSetup('rep', 8000))
for msg in zero:
    zero(2 * msg)
```

```python
# The req (connect) client
zero = Zero(ZeroSetup('req', 8000))
for msg in [1, 2, "hello"]:
    rep = zero(msg)
    zero.setup.warn('%r became %r', msg, rep)
```

### RPC

Remote Procedure Call. Name the procedure and supply a dictionary of
arguments. Works with `rep`, `pull` and even `sub`.

***Note:*** It is quite useful and possible to activate a `pull`
server. It can't reply, but it can act on incoming orders.

You will need to implement your RPC server. It is simple, just extend
`ZeroRPC` and add the methods you need to the class. All methods that
are not prefixed with `_` are exposed.

Then create a zero and activate it with an RPC object.
```python
class RPCDemo(ZeroRPC):
    def ping(self):
        return "pong"
    def greet(self, name):
        return "hello %s" % name

# The rep (bind) server, activated with RPCDemo
zero = Zero(ZeroSetup('rep', 8000).activated(RPCDemo())
for msg in zero:
    # msg here is the result after going through RPCDemo
    zero.setup.warn('Reply with %r', msg)
    zero(msg)
```

```python
# The req (connect) client
zero = Zero(ZeroSetup('req', 8000))
print zero(['ping'])
print zero(['greet', {'name': 'Phil'}])
```

Marshalling
-----------
If you need a different marshalling, just supply encode and decode
methods to `Zero.marshals`.

Test
----
Install and set up environment:

    . ./env.sh
    python py/zero.py test

Optionally `-v` for a more verbose test report.
