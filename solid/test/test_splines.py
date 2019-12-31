#! /usr/bin/env python

import unittest
from solid.test.ExpandedTestCase import DiffOutput
from solid import *
from solid.splines import catmull_rom_points

SEGMENTS = 8


class TestCatmullRomPoints(DiffOutput):
    def setUp(self):
        self.tooth_height = 10
        self.tooth_depth = 5

    def test_catmull_rom_points(self):
        expected = ''' '''
        actual = catmull_rom_points()
        self.assertEqual(expected, actual)

if __name__ == '__main__':
    unittest.main()