zero
====

Zero MQ utilities

Installation
------------
This only works on the mac. What if you don't have a mac? ...get one?

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

Useful for workers feeding status messages to a central publisher that
has many subscribers listening in.

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

### Pub-sub

Fan-out pub-sub. The most common for feeding a large number of
listeners a stream of messages.

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

**Note: ** It is quite useful and possible to activate a `pull`
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
