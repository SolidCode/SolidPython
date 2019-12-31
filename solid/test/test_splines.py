#! /usr/bin/env python

import unittest
from solid.test.ExpandedTestCase import DiffOutput
from solid import *
from solid.splines import catmull_rom_points
from euclid3 import Point2, Vector2

SEGMENTS = 8

class TestCatmullRomPoints(DiffOutput):
    def setUp(self):
        self.points = [
            Point2(0,0),
            Point2(1,1),
            Point2(2,1),
        ]

    def test_catmull_rom_points(self):
        expected = [Vector2(0.00, 0.00), Vector2(0.38, 0.44), Vector2(1.00, 1.00), Vector2(1.62, 1.06), Vector2(2.00, 1.00)]
        actual = catmull_rom_points(self.points, subdivisions=2, close_loop=False)
        actual = list((str(v) for v in actual))
        expected = list((str(v) for v in expected))
        self.assertEqual(expected, actual)

        # TODO: verify we always have the right number of points for a given call
        # verify that `close_loop` always behaves correctly 
        # verify that catmull_rom_polygon() returns an OpenSCADObject
        # verify that start_tangent and end_tangent behavior is correct

if __name__ == '__main__':
    unittest.main()