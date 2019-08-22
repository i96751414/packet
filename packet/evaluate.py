#!/usr/bin/python
# -*- coding: UTF-8 -*-

from ast import Str, Num, Tuple, List, Set, Dict, Name, UnaryOp, UAdd, \
    USub, BinOp, Add, Sub, Call
# AST necessary imports
from ast import parse, Expression

from packet._compat import string_types

try:
    from ast import Constant
except ImportError:
    class Constant(object):
        value = None

try:
    from ast import NameConstant
except ImportError:
    class NameConstant(object):
        value = None

try:
    from ast import Bytes
except ImportError:
    class Bytes(object):
        s = None

_NUM_TYPES = (int, float, complex)

# None, True and False are treated as Names in Python 2+
_SAFE_NAMES = {
    "None": None, "True": True, "False": False,
    "inf": float("inf"), "nan": float("nan"),
    "infj": complex("infj"), "nanj": complex("nanj"),
}

_SAFE_CALLS = {
    "set": set,
}


def safe_eval(node_or_string):
    """
    Safely evaluate an expression node or a string containing a Python
    expression. The string or node provided may only consist of the following
    Python literal structures: strings, bytes, numbers, tuples, lists, dicts,
    sets, booleans, and None.

    Note: This is a modified version of the ast.literal_eval function from
    Python 3.6

    :type node_or_string: str, node
    :param node_or_string: expression string or node
    :return: evaluated
    """
    if isinstance(node_or_string, string_types):
        node_or_string = parse(node_or_string, mode="eval")
    if isinstance(node_or_string, Expression):
        node_or_string = node_or_string.body

    def _convert(node):
        if isinstance(node, Constant):
            return node.value
        elif isinstance(node, (Str, Bytes)):
            return node.s
        elif isinstance(node, Num):
            return node.n
        elif isinstance(node, Tuple):
            return tuple(map(_convert, node.elts))
        elif isinstance(node, List):
            return list(map(_convert, node.elts))
        elif isinstance(node, Set):
            return set(map(_convert, node.elts))
        elif isinstance(node, Dict):
            return dict((_convert(k), _convert(v)) for k, v
                        in zip(node.keys, node.values))
        elif isinstance(node, Name):
            if node.id in _SAFE_NAMES:
                return _SAFE_NAMES[node.id]
        elif isinstance(node, NameConstant):
            return node.value
        elif isinstance(node, Call):
            if node.func.id in _SAFE_CALLS:
                args = [_convert(arg) for arg in node.args]
                return _SAFE_CALLS[node.func.id](*args)
        elif isinstance(node, UnaryOp) and isinstance(node.op, (UAdd, USub)):
            operand = _convert(node.operand)
            if isinstance(operand, _NUM_TYPES):
                if isinstance(node.op, UAdd):
                    return + operand
                else:
                    return - operand
        elif isinstance(node, BinOp) and isinstance(node.op, (Add, Sub)):
            left = _convert(node.left)
            right = _convert(node.right)
            if isinstance(left, _NUM_TYPES) and isinstance(right, _NUM_TYPES):
                if isinstance(node.op, Add):
                    return left + right
                else:
                    return left - right
        raise ValueError("malformed node or string: {}".format(repr(node)))

    return _convert(node_or_string)
