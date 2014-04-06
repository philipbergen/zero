#!/usr/bin/env python
##
# https://github.com/philipbergen/zero
# Licensed under terms of MIT license (see LICENSE-MIT)
# Copyright (c) 2013 Philip Bergen, philip.bergen@me.com

''' USAGE:
      zlog-sink [<config>]

    <config>  Path to configuration file [default: log.json]
'''

from ansicolor import *


class Logout(object):
    width = 100
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
        from traceback import format_exc
        try:
            sender, host, lvl, ts, msg = loads(logline)
        except (ValueError, TypeError):
            print format_exc()
            lvl = host = sender = '?'
            ts = strftime(self.ts_format)
            msg = logline
        if lvl not in self.lvls:
            lvl = '?'
        try:
            lines = iter(msg.split('\n'))
        except AttributeError:
            lines = [repr(msg)]
        msg = []
        for tmp in lines:
            for i in range(0, len(tmp), self.width):
                msg.append(tmp[i:i+self.width])
        msg = iter(msg)
        col = self.lvls[lvl]
        print wide(1, ts), col(wide(0, lvl)), col(wide(2, host))
        for m in msg:
            print self.lvls[lvl](' ------>'), cya(sender), m


def main():
    import os.path
    from sys import argv
    from json import load
    from zero import Zero, ZeroSetup
    HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    conf = HERE + '/log.json'
    if len(argv) > 1:
        conf = argv[1]
    print 'Loading config from', conf
    with open(conf) as fin:
        conf = load(fin)['log']
    setup = ZeroSetup('pull', conf['port'])
    path = conf['file']
    if path[0] != '/':
        path = HERE + '/' + path
    print 'Logger started for', setup
    print 'Logging to', path
    with open(path, 'a', 1) as fout:
        logout = Logout(conf)
        try:
            for line in Zero(setup):
                fout.write(line)
                fout.write('\n')
                logout.tty(line)
        except KeyboardInterrupt:
            print 'Logger quitting.'
    print 'Logger stopped on', setup


if __name__ == '__main__':
    main()
