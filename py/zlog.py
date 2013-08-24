#!/usr/bin/env python

''' USAGE:
      zlog [<config>] (lol|fyi|wtf|omg) <sender> (-|<message> <message>...)

    <sender> is a logical name of emitting party.

    If <message> is -, message lines are read from stdin.
'''


def log_format(config, sender, level, msg):
    from json import dumps
    from time import strftime
    from socket import gethostname
    return dumps([sender, gethostname(), level, strftime(config['ts-format']), msg])
                 
def main():
    from sys import argv, exit
    from json import load
    from itertools import imap
    from collections import deque
    from zero import zero, ZeroSetup
    from os.path import dirname, exists
    args = deque(argv[1:])
    if len(args) < 4:
        exit(__doc__)
    conf = dirname(__file__) + '/../log.json'
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
    messages = imap(lambda x:log_format(conf, sender, level, x), messages)
    z = zero(ZeroSetup('push', str(conf['port']), messages))
    for msg in z:
        pass

if __name__ == '__main__':
    main()
