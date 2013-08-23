#!/usr/bin/env python

''' USAGE:
      log.py <config>
'''

import json
from clint.textui import puts, colored

class Logout(object):
    def __init__(self, ts_format):
        self.colwidth = [0] * 5
        self.lvls = {'debug': colored.white, 'info': colored.green, 'warning': colored.yellow, 'error': colored.red, '?': colored.magenta}
        self.ts_format = ts_format

    def tty(self, logline):
        def wide(n, s):
            self.colwidth[n] = max(self.colwidth[n], len(s))
            return ('%-' + str(self.colwidth[n]) + 's') % s

        from time import strftime
        try:
            lvl, ts, host, sender, msg = json.loads(logline)
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
    import sys
    import json
    config = json.load(open(sys.argv[1]))['log']
    port, logfile = config['port'], config['file']
    from zero import zero, zero_args
    args = zero_args(('%s -b sub -n inf' % port).split(' '))

    print 'Logger started on', port
    with open(logfile, 'a') as fout:
        logout = Logout(config.get('ts-format', '%Y-%m-%dT%H:%M:%S%Z'))
        try:
            for logline in zero(args):
                fout.write(logline)
                fout.write('\n')
                logout.tty(logline)
        except KeyboardInterrupt:
            print 'Logger quitting.'
            sock.close()
    print 'Logger stopped on', port
    sys.exit(0)

if __name__ == '__main__':
    main()
