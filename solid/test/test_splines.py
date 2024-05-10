#! /usr/bin/env python

import unittest
from solid.test.ExpandedTestCase import DiffOutput
from solid import *
from solid.utils import euclidify
from solid.splines import (
    catmull_rom_points,
    catmull_rom_prism,
    bezier_points,
    bezier_polygon,
    hobby_points,
)
from euclid3 import Point2, Point3, Vector2, Vector3
from math import pi

SEGMENTS = 8


class TestSplines(DiffOutput):
    def setUp(self):
        self.points = [
            Point3(0, 0),
            Point3(1, 1),
            Point3(2, 1),
        ]
        self.points_raw = [
            (0, 0),
            (1, 1),
            (2, 1),
        ]
        self.bezier_controls = [
            Point3(0, 0),
            Point3(1, 1),
            Point3(2, 1),
            Point3(2, -1),
        ]
        self.bezier_controls_raw = [(0, 0), (1, 1), (2, 1), (2, -1)]
        self.hobby_omega = 0.69
        self.subdivisions = 2

    def assertPointsListsEqual(self, a, b):
        str_list = lambda x: list(str(v) for v in x)
        self.assertEqual(str_list(a), str_list(b))

    def test_catmull_rom_points(self):
        expected = [
            Point3(0.00, 0.00),
            Point3(0.38, 0.44),
            Point3(1.00, 1.00),
            Point3(1.62, 1.06),
            Point3(2.00, 1.00),
        ]
        actual = catmull_rom_points(
            self.points, subdivisions=self.subdivisions, close_loop=False
        )
        self.assertPointsListsEqual(expected, actual)

        # TODO: verify we always have the right number of points for a given call
        # verify that `close_loop` always behaves correctly
        # verify that start_tangent and end_tangent behavior is correct

    def test_catmull_rom_points_raw(self):
        # Verify that we can use raw sequences of floats as inputs (e.g [(1,2), (3.2,4)])
        # rather than sequences of Point2s
        expected = [
            Point3(0.00, 0.00),
            Point3(0.38, 0.44),
            Point3(1.00, 1.00),
            Point3(1.62, 1.06),
            Point3(2.00, 1.00),
        ]
        actual = catmull_rom_points(
            self.points_raw, subdivisions=self.subdivisions, close_loop=False
        )
        self.assertPointsListsEqual(expected, actual)

    def test_catmull_rom_points_3d(self):
        points = [Point3(-1, -1, 0), Point3(0, 0, 1), Point3(1, 1, 0)]
        expected = [
            Point3(-1.00, -1.00, 0.00),
            Point3(-0.62, -0.62, 0.50),
            Point3(0.00, 0.00, 1.00),
            Point3(0.62, 0.62, 0.50),
            Point3(1.00, 1.00, 0.00),
        ]
        actual = catmull_rom_points(points, subdivisions=2)
        self.assertPointsListsEqual(expected, actual)

    def test_bezier_points(self):
        expected = [Point3(0.00, 0.00), Point3(1.38, 0.62), Point3(2.00, -1.00)]
        actual = bezier_points(self.bezier_controls, subdivisions=self.subdivisions)
        self.assertPointsListsEqual(expected, actual)

    def test_bezier_points_raw(self):
        # Verify that we can use raw sequences of floats as inputs (e.g [(1,2), (3.2,4)])
        # rather than sequences of Point2s
        expected = [Point3(0.00, 0.00), Point3(1.38, 0.62), Point3(2.00, -1.00)]
        actual = bezier_points(self.bezier_controls_raw, subdivisions=self.subdivisions)
        self.assertPointsListsEqual(expected, actual)

    def test_bezier_points_3d(self):
        # verify that we get a valid bezier curve back even when its control points
        # are outside the XY plane and aren't coplanar
        controls_3d = [
            Point3(-2, -1, 0),
            Point3(-0.5, -0.5, 1),
            Point3(0.5, 0.5, 1),
            Point3(2, 1, 0),
        ]
        actual = bezier_points(controls_3d, subdivisions=self.subdivisions)
        expected = [
            Point3(-2.00, -1.00, 0.00),
            Point3(0.00, 0.00, 0.75),
            Point3(2.00, 1.00, 0.00),
        ]
        self.assertPointsListsEqual(expected, actual)

    def test_hobby_points(self):
        expected = [
            Point3(0.00, 0.00, 0.00),
            Point3(0.07, 0.50, 0.00),
            Point3(0.52, 0.82, 0.00),
            Point3(1.00, 1.00, 0.00),
            Point3(1.33, 1.12, 0.00),
            Point3(1.71, 1.19, 0.00),
            Point3(2.00, 1.00, 0.00),
            Point3(2.63, 0.60, 0.00),
            Point3(2.35, -0.28, 0.00),
            Point3(2.00, -1.00, 0.00),
        ]

        actual = hobby_points(self.bezier_controls, self.hobby_omega, close_loop=False)
        self.assertPointsListsEqual(expected, actual)

    def test_hobby_points_raw(self):
        expected = [
            Point3(0.00, 0.00, 0.00),
            Point3(0.07, 0.50, 0.00),
            Point3(0.52, 0.82, 0.00),
            Point3(1.00, 1.00, 0.00),
            Point3(1.33, 1.12, 0.00),
            Point3(1.71, 1.19, 0.00),
            Point3(2.00, 1.00, 0.00),
            Point3(2.63, 0.60, 0.00),
            Point3(2.35, -0.28, 0.00),
            Point3(2.00, -1.00, 0.00),
        ]
        actual = hobby_points(
            self.bezier_controls_raw, self.hobby_omega, close_loop=False
        )
        self.assertPointsListsEqual(expected, actual)

    def test_hobby_points_3d(self):
        controls_3d = [
            Point3(-2, -1, 0),
            Point3(-0.5, -0.5, 1),
            Point3(0.5, 0.5, 1),
            Point3(2, 1, 0),
        ]
        expected = [
            Point3(-2.00, -1.00, 0.00),
            Point3(-1.75, -1.03, 0.62),
            Point3(-1.04, -0.90, 0.86),
            Point3(-0.50, -0.50, 1.00),
            Point3(-0.12, -0.22, 1.10),
            Point3(0.11, 0.24, 1.13),
            Point3(0.50, 0.50, 1.00),
            Point3(1.01, 0.84, 0.83),
            Point3(1.55, 0.88, 0.44),
            Point3(2.00, 1.00, 0.00),
        ]

        actual = hobby_points(controls_3d, self.hobby_omega, close_loop=False)
        self.assertPointsListsEqual(expected, actual)

    def test_catmull_rom_prism(self):
        sides = 3
        UP = Vector3(0, 0, 1)

        control_points = [[10, 10, 0], [10, 10, 5], [8, 8, 15]]

        cat_tube = []
        angle_step = 2 * pi / sides
        for i in range(sides):
            rotated_controls = list(
                (
                    euclidify(p, Point3).rotate_around(UP, angle_step * i)
                    for p in control_points
                )
            )
            cat_tube.append(rotated_controls)

        poly = catmull_rom_prism(
            cat_tube, self.subdivisions, closed_ring=True, add_caps=True
        )
        actual = (len(poly.params["points"]), len(poly.params["faces"]))
        expected = (37, 62)
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
