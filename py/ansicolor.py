##
# https://github.com/philipbergen/zero
# Licensed under terms of MIT license (see LICENSE-MIT)
# Copyright (c) 2013 Philip Bergen, philip.bergen@me.com

''' Exports ansicolor functions.
    You want to probably use this as:
        from ansicolor import blk, red, grn, yel, blu, mag, cya, wht, off, bld, dim, FG, BG
    print BLD(red('Hello')), yel('world!', BG)
'''

_colors = 'blk red grn yel blu mag cya wht'.split()
__all__ = _colors + 'off bld dim FG BG'.split()

_CSI = '\033[%dm'
_OFF = _CSI % 0
FG = 30  # Add to a color for foreground
BG = 40  # Add to a color for background


def bld(s):
    'Wraps s in ANSI codes for bold'
    return _CSI % 1 + s + _OFF


def dim(s):
    'Wraps s in ANSI codes for dim'
    return _CSI % 2 + s + _OFF


def off(fg=FG):
    'Returns ANSI codes for turning off all color and style'
    return _CSI % (fg + 9)


for col_n, col in enumerate(_colors):
    def colorwrap(s='', fg=FG, col_n=col_n):
        'Returns s wrapped in ANSI color codes for each available color'
        if not s:
            return _CSI % (fg + col_n)
        return _CSI % (fg + col_n) + s + _OFF
    locals()[col] = colorwrap
