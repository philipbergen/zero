##
# https://github.com/philipbergen/zero
# Licensed under terms of MIT license (see LICENSE-MIT)
# Copyright (c) 2013 Philip Bergen, philip.bergen@me.com

''' Exports ansicolor functions.
    You want to probably use this as:
        from ansicolor import *
    print BLD(red('Hello')), yel('world!')
'''

_colors = 'blk red grn yel blu mag cya wht'.split()
__all__ = _colors + 'off bld dim FG BG'.split()

_CSI = '\033[%dm'
_OFF = _CSI % 0
FG = 30  # Add to a color for foreground
BG = 40  # Add to a color for background


def bld(s):
    return _CSI % 1 + s + _OFF


def dim(s):
    return _CSI % 2 + s + _OFF


def off(fg=FG):
    return _CSI % (fg + 9)


for col_n, col in enumerate(_colors):

    def colorwrap(s='', fg=FG, col_n=col_n):
        if not s:
            return _CSI % (fg + col_n)
        return _CSI % (fg + col_n) + s + _OFF
    locals()[col] = colorwrap
