#!/usr/bin/env python

''' USAGE:
      zlog-sink [<config>]

    <config> default is log.json
'''

from ansicolor import *

class Logout(object):
    def __init__(self, conf):
        self.colwidth = [0] * 5
        self.lvls = {}
        for lvl, col in conf['levels']:
            self.lvls[lvl] = eval(col)
        self.ts_format = conf['ts-format']

    def tty(self, logline):
        def wide(n, s):
            self.colwidth[n] = max(self.colwidth[n], len(s))
            return ('%-' + str(self.colwidth[n]) + 's') % s

        from json import loads
        from time import strftime
        try:
            sender, host, lvl, ts, msg = loads(logline)
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
        print col(wide(0, lvl)), wide(1, ts), col(wide(2, host)), cya(wide(3, sender)), msg.next()
        for m in msg:
            print self.lvls[lvl](' ------>'), m

def main():
    from env import HERE
    from sys import argv
    from json import load
    from os import environ
    from zlog import log_format
    from zero import zero, ZeroSetup
    from os.path import exists
    conf = HERE + '/log.json'
    if len(argv) > 1:
        conf = argv[1]
    print 'Loading config from', conf
    with open(conf) as fin:
        conf = load(fin)['log']
    setup = ZeroSetup('pull', conf['port']).binding()
    path = conf['file']
    if path[0] != '/':
        path = HERE + '/' + path
    print 'Logger started for', setup
    print 'Logging to', path
    with open(path, 'a', 1) as fout:
        logout = Logout(conf)
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
