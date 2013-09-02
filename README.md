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

Assumes `from zero import *`

### Push-pull

Fan-in push-pull, using json marshalling:

```python
# The pull (bind) server
setup = ZeroSetup('pull', 8000).debugging()
zero = Zero(setup)
for msg in zero:
    zero.setup.warn('Pulled %s', msg)
```

```python
# The push (connect) client
setup = ZeroSetup('push', 8000).debugging()
zero = Zero(setup)
for msg in ['alpha', 'beta', 'gamma']:
    zero(msg)
```


Test
----
Install and set up environment:

    . ./env.sh
    python py/zero.py test

Optionally `-v` for a more verbose test report.
