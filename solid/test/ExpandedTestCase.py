"""
A version of unittest that gives output in an easier to use format
"""
import sys
import unittest
import difflib


class DiffOutput(unittest.TestCase):

    def assertEqual(self, first, second, msg=None):
        """
        Override assertEqual and print(a context diff if msg=None)
        """
        # Test if both are strings, in Python 2 & 3
        string_types = str if sys.version_info[0] == 3 else basestring

        if isinstance(first, string_types) and isinstance(second, string_types):
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
