#!/usr/bin/env python

''' USAGE:
      zlog-sink [<config>]

    <config> default is log.json
'''

import json
from clint.textui import puts, colored

class Logout(object):
    def __init__(self, ts_format):
        self.colwidth = [0] * 5
        self.lvls = {'lol': colored.white, 'fyi': colored.green, 'wtf': colored.yellow, 'omg': colored.red, '?': colored.magenta}
        self.ts_format = ts_format

    def tty(self, logline):
        def wide(n, s):
            self.colwidth[n] = max(self.colwidth[n], len(s))
            return ('%-' + str(self.colwidth[n]) + 's') % s

        from time import strftime
        try:
            sender, host, lvl, ts, msg = json.loads(logline)
        except (ValueError, TypeError) as e:
            lvl = host = sender = '?'
            ts = strftime(self.ts_format)
            msg = logline
        if lvl not in self.lvls:
            lvl = '?'
        try:
            msg = iter(msg.split('\n'))
        except AttributeError:
            tmp = repr(msg)
            msg = []
            msg.append(tmp[:40])
            i = 40
            while i < len(tmp):
                msg.append(tmp[i:i+80])
                t += 80
            msg = iter(msg)
        col = self.lvls[lvl]
        print col(wide(0, lvl)), wide(1, ts), col(wide(2, host)), colored.cyan(wide(3, sender)), msg.next()
        for m in msg:
            print self.lvls[lvl](' ------>'), m

def main():
    from sys import argv
    from json import load
    from zlog import log_format
    from zero import zero, ZeroSetup
    from os.path import dirname, exists
    conf = dirname(__file__) + '/../log.json'
    if len(argv) > 1:
        conf = argv[1]
    with open(conf) as fin:
        conf = load(fin)['log']
    setup = ZeroSetup('pull', str(conf['port'])).binding()
    print 'Logger started for', setup
    with open(conf['file'], 'a', 1) as fout:
        logout = Logout(conf.get('ts-format', '%Y-%m-%dT%H:%M:%S%Z'))
        try:
            for line in zero(setup):
                fout.write(line)
                fout.write('\n')
                logout.tty(line)
        except KeyboardInterrupt:
            print 'Logger quitting.'
            sock.close()
    print 'Logger stopped on', setup

if __name__ == '__main__':
    main()
