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
from itertools import chain

try:
    from collections import ChainMap
except ImportError:
    class ChainMap(dict):
        """Poor man's Python2 chainmap with getitem only.
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
STAR = object()
DSTAR = object()
DOIT = object()


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
        """Other is assumed a callable through which the chain should traverse."""
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


class Pipe(object):
    def __init__(self, *args, **kw):
        self._stack = []
        self._args = args
        self._kw = kw
        self._frame = None

    def _include_op(self, op):
        if op is DOIT:
            return self.__call__()
        self._stack.append({'op': op})
        if len(self._stack) == 1:
            self._stack[0]['args'] = self._args
            self._stack[0]['kw'] = self._kw
        return self

    def _merge(self, other):
        self._stack.extend(other._stack)
        return self

    def __getattr__(self, attr):
        if not self._frame:
            frame = sys._getframe().f_back
            self._frame = frame
        else:
            frame = self._frame
        try:
            op = ChainMap(frame.f_locals, frame.f_globals, frame.f_builtins)[attr]
        except KeyError:
            op = attr
        return self._include_op(op)

    def __or__(self, other):
        if isinstance(other, Pipe):
            return self._merge(other)
        op = other
        return self._include_op(op)

    def _is_lazy_call(*args, **kw):
        return any(arg in (DELAY, STAR, DSTAR) for arg in chain(args, kw.values()))

    def __call__(self, *args, **kw):
        if not self._is_lazy_call(args, kw):
            next_args = []
            for op_struct in self._stack:
                op = op_struct['op']
                if isinstance(op, str):
                    op = getattr(args, op)
                    next_args = ''
                args = op(
                    *chain(next_args, op_struct.get('args', [])),
                    **op_struct.get('kw', {})
                )
                if (hasattr(args, '__len__') or hasattr(args, '__iter__')) and not isinstance(args, str):
                    next_args = args
                else:
                    next_args = [args]
            return args

