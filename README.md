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
The installer will install pip if it is missing and then use that to install 
the zmq module (pyzmq) and a few other requirements.

    ./install.sh

*Note:* I developed this on a Mac, should work on other unix as well.

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
        -n MESSAGES     Number of messages before exiting [default: inf]
        --wait          Waits for user input at the end of the program, before
                        quitting
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

Most important in the `zero` module is `ZeroSetup` and `Zero`. The 
`ZeroSetup` is the input to constructing `Zero`. That way the result
of docopt (`ZeroSetup.argv`) is the same as using `ZeroSetup()` and
calling a few factory-like functions on it.

The `Zero` object is both *callable* and *iterable*. Iterate over
incoming messages and call to transmit a message. Objects are
automatically marshalled before returning out of the iterator or before
transmission.

Default marshalling is JSON. Marshalling is configurable. See below
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
# what the client is doing. Connects to localhost and sends three 
# messages ("alpha", "beta", "gamma").
zero = Zero(ZeroSetup('push', 8000).debugging())
zero('alpha')
zero('beta')
zero('gamma')
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
from zero.rpc import ZeroRPC

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

### Configuration based RPC

Create a configuration object. The easiest way is a json file with
your configuration. Configuration based RPC only looks at the section
named `workers`, allowing other system specific setup to be stored
alongside the RPC configuration.

Example configuration file:

```python
config =  {'workers': {
    'common': {
        'module': 'zero.test',
        'class': 'CommonRPC',
        'zmq': {'port': 8000, 'method': 'rep'}
    }
}}
```

The `zmq` node also accepts (optional) `bind`, `debug` and `host`, see
`rpc.py` for details.

To establish an activated Zero with the RPC object  based on your
configuration:

```python
from zero.rpc import zrpc

zero = zrpc(config, 'common')
for msg in zero:
    zero(msg)
```

To call your RPC, create a client:

```python
from zero.rpc import zrpc

zserver = zrpc(config, 'common')
zero = zserver.opposite()

print 'Server returned:', zero(['echo', {'msg': 'Say hello'}])
```

Marshalling
-----------
If you need a different marshalling, just supply encode and decode
methods to `Zero.marshals`.

Test
----
Set up environment and run tests:

    bin/zero test

Optionally `-v` for a more verbose test report.

[Travis](https://travis-ci.org/philipbergen/zero) continuous integration:
<br/>
<img src="https://api.travis-ci.org/philipbergen/zero.png"/>
