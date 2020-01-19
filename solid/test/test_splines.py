#! /usr/bin/env python

import unittest
from solid.test.ExpandedTestCase import DiffOutput
from solid import *
from solid.splines import catmull_rom_points, bezier_points
from euclid3 import Point2, Vector2

SEGMENTS = 8

class TestSplines(DiffOutput):
    def setUp(self):
        self.points = [
            Point2(0,0),
            Point2(1,1),
            Point2(2,1),
        ]
        self.bezier_controls = [
            Point2(0,0),
            Point2(1,1),
            Point2(2,1),
            Point2(2,-1),
        ]
        self.subdivisions = 2

    def assertPointsListsEqual(self, a, b):
        str_list = lambda x: list(str(v) for v in x)
        self.assertEqual(str_list(a), str_list(b))

    def test_catmull_rom_points(self):
        expected = [Vector2(0.00, 0.00), Vector2(0.38, 0.44), Vector2(1.00, 1.00), Vector2(1.62, 1.06), Vector2(2.00, 1.00)]
        actual = catmull_rom_points(self.points, subdivisions=self.subdivisions, close_loop=False)
        self.assertPointsListsEqual(expected, actual)
        # actual = list((str(v) for v in actual))
        # expected = list((str(v) for v in expected))
        # self.assertEqual(expected, actual)

        # TODO: verify we always have the right number of points for a given call
        # verify that `close_loop` always behaves correctly 
        # verify that catmull_rom_polygon() returns an OpenSCADObject
        # verify that start_tangent and end_tangent behavior is correct

    def test_bezier_points(self):
        expected = [Point2(0.00, 0.00), Point2(1.38, 0.62), Point2(2.00, -1.00)]
        actual = bezier_points(self.bezier_controls, subdivisions=self.subdivisions)
        self.assertPointsListsEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()