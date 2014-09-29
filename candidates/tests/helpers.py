from __future__ import print_function

import difflib
import pprint

import sys

def p(*args):
    """A helper for printing to stderr"""
    print(file=sys.stderr, *args)

def equal_arg(arg1, arg2):
    """Return True if the args are equal, False otherwise

    If the arguments aren't equal under ==, return True, otherwise
    return False and try to output to stderr a diff of the
    pretty-printed objects."""

    if arg1 == arg2:
        return True

    # This is more or less taken from assertDictEqual in
    # django/utils/unittest/case.py:
    args1_lines = pprint.pformat(arg1).splitlines()
    args2_lines = pprint.pformat(arg2).splitlines()
    diff = difflib.ndiff(args1_lines, args2_lines)

    p("Found the following differences: ====================================")
    for line in diff:
        p(line)
    p("=====================================================================")

    return False

def equal_call_args(args1, args2):
    """Return True if two sequences of arguments are equal

    Otherwise return False and output a diff of the first non-equal
    arguments to stderr."""
    if len(args1) != len(args2):
        message = "The argument lists were different lengths: {0} and {1}"
        p(message.format(len(args1), len(args2)))

    for i, arg1 in enumerate(args1):
        if not equal_arg(arg1, args2[i]):
            return False

    return True
