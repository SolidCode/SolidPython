"""
A version of unittest that gives output in an easier to use format
"""
import sys
import unittest
import difflib
import re
from typing import Union
from solid import OpenSCADObject, scad_render

class DiffOutput(unittest.TestCase):

    def assertEqual(self, first, second, msg=None):
        """
        Override assertEqual and print(a context diff if msg=None)
        """
        if isinstance(first, str) and isinstance(second, str):
            if not msg:
                msg = 'Strings are not equal:\n' + ''.join(
                    difflib.unified_diff(
                        [first],
                        [second],
                        fromfile='actual',
                        tofile='expected'
                    )
                )
        return super(DiffOutput, self).assertEqual(first, second, msg=msg)

    def assertEqualNoWhitespace(self, a, b):
        remove_whitespace = lambda s: re.subn(r'[\s\n]','', s)[0]
        self.assertEqual(remove_whitespace(a), remove_whitespace(b))

    def assertEqualOpenScadObject(self, expected:str, actual:Union[OpenSCADObject, str]):
        if isinstance(actual, OpenSCADObject):
            act = scad_render(actual)
        elif isinstance(actual, str):
            act = actual
        self.assertEqualNoWhitespace(expected, act)

