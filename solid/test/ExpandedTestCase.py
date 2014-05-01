"""
A version of unittest that gives output in an easier to use format
"""
import unittest
import difflib


class DiffOutput(unittest.TestCase):
    def assertEqual(self, first, second, msg=None):
        """
        Override assertEqual and print a context diff if msg=None
        """
        if not msg:
            msg = 'Strings are not equal:\n' + ''.join(
                difflib.unified_diff(first, second, fromfile='actual', tofile='expected')
            )
        return super(DiffOutput, self).assertEqual(first, second, msg=msg)
