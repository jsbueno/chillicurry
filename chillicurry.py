# coding: utf-8

# Author: João S. O. Bueno
# License: LGPL v3.0

"""
>>> from chillicurry import curry, DELAY
>>> # test fails in Python3 - due to "open" reading the text as unicode already
>>> curry.encode(DELAY, "ASCII", "ignore").upper.decode(DELAY, "utf-8").sorted(DELAY, key=len).strip.readlines.open("cities.txt")
['LIMEIRA', 'IBITINGA', 'CAMPINAS', 'AMERICANA', 'SO PAULO', 'PIRACICABA', 'PIRATININGA', 'RIBEIRO PRETO', 'SO BERNARDO DO CAMPO', 'SO JOS DO RIO PRETO']

>>> import math
>>> (curry|(math.log)).len.range(10)
2.302585092994046

"""

# TODO: A way to transform a chillicurried chain into a giant robot with lasers

import sys

try:
    from collections import ChainMap
except ImportError:
    class ChainMap(dict):
        """
        Poorman's Python2 chainmap with getitem only
        """
        def __init__(self, *mappings):
            self.mappings = mappings
        def __getitem__(self, key):
            for dct in self.mappings:
                try:
                    return dct[key]
                except KeyError:
                    pass
            raise KeyError

DELAY = object()

class ChilliCurry(object):
    def __init__(self, previous=None):
        self._stack = []
        self._previous = previous
        self._frame = None
        self._args = ()
        self._kw = {}

    def __getattr__(self, attr):
        if self._previous and self._previous._frame:
            frame = self._previous._frame
        else:
            frame = sys._getframe().f_back
            self._frame = frame
        try:
            op = ChainMap(frame.f_locals, frame.f_globals, frame.f_builtins)[attr]
        except KeyError:
            op = (attr,)
        self._current_op = op
        return ChilliCurry(self)

    def __or__(self, other):
        # other is assumed a callable through which the chain should traverse
        self._current_op = other
        return ChilliCurry(self)

    def __call__(self, value, *args, **kw):
        if value is DELAY:
            self._args = args
            self._kw = kw
            return self
        if self._previous:
            op = self._previous._current_op
            if isinstance(op, tuple):
                try:
                    op = getattr(value, op[0])
                    result = op(*self._args, **self._kw)
                except AttributeError:
                    try:
                        result = []
                        for item in value:
                            result.append(getattr(item, op[0])(*self._args, **self._kw))  
                    except TypeError:
                        raise AttributeError(op[0])
            else:
                result = op(value, *self._args, **self._kw)
            return self._previous(result)
        return value

curry = ChilliCurry()

