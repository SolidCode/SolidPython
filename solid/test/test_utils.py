#! /usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import sys
import re

import unittest

from solid import *
from solid.utils import *
from euclid3 import *
import difflib
from solid.test.ExpandedTestCase import DiffOutput


tri = [Point3(0, 0, 0), Point3(10, 0, 0), Point3(0, 10, 0)]
scad_test_cases = [
    (                               up,                 [2],   '\n\ntranslate(v = [0, 0, 2]);'),
    (                               down,               [2],   '\n\ntranslate(v = [0, 0, -2]);'),
    (                               left,               [2],   '\n\ntranslate(v = [-2, 0, 0]);'),
    (                               right,              [2],   '\n\ntranslate(v = [2, 0, 0]);'),
    (                               forward,            [2],   '\n\ntranslate(v = [0, 2, 0]);'),
    (                               back,               [2],   '\n\ntranslate(v = [0, -2, 0]);'),   
    (                               arc,                [10, 0, 90, 24], '\n\ndifference() {\n\tcircle($fn = 24, r = 10);\n\trotate(a = 0) {\n\t\ttranslate(v = [0, -10, 0]) {\n\t\t\tsquare(center = true, size = [30, 20]);\n\t\t}\n\t}\n\trotate(a = -90) {\n\t\ttranslate(v = [0, -10, 0]) {\n\t\t\tsquare(center = true, size = [30, 20]);\n\t\t}\n\t}\n}'),
    (                               arc_inverted,       [10, 0, 90, 24], '\n\ndifference() {\n\tintersection() {\n\t\trotate(a = 0) {\n\t\t\ttranslate(v = [-990, 0]) {\n\t\t\t\tsquare(center = false, size = [1000, 1000]);\n\t\t\t}\n\t\t}\n\t\trotate(a = 90) {\n\t\t\ttranslate(v = [-990, -1000]) {\n\t\t\t\tsquare(center = false, size = [1000, 1000]);\n\t\t\t}\n\t\t}\n\t}\n\tcircle($fn = 24, r = 10);\n}'),
    ( 'transform_to_point_scad',    transform_to_point, [cube(2), [2,2,2], [3,3,1]], '\n\nmultmatrix(m = [[0.7071067812, -0.1622214211, -0.6882472016, 2], [-0.7071067812, -0.1622214211, -0.6882472016, 2], [0.0000000000, 0.9733285268, -0.2294157339, 2], [0, 0, 0, 1.0000000000]]) {\n\tcube(size = 2);\n}'),
    ( 'extrude_along_path',         extrude_along_path, [tri, [[0,0,0],[0,20,0]]], '\n\npolyhedron(faces = [[0, 3, 1], [1, 3, 4], [1, 4, 2], [2, 4, 5], [0, 2, 5], [0, 5, 3], [0, 1, 2], [3, 5, 4]], points = [[0.0000000000, 0.0000000000, 0.0000000000], [10.0000000000, 0.0000000000, 0.0000000000], [0.0000000000, 0.0000000000, 10.0000000000], [0.0000000000, 20.0000000000, 0.0000000000], [10.0000000000, 20.0000000000, 0.0000000000], [0.0000000000, 20.0000000000, 10.0000000000]]);'),
    ( 'extrude_along_path_vertical',extrude_along_path, [tri, [[0,0,0],[0,0,20]]], '\n\npolyhedron(faces = [[0, 3, 1], [1, 3, 4], [1, 4, 2], [2, 4, 5], [0, 2, 5], [0, 5, 3], [0, 1, 2], [3, 5, 4]], points = [[0.0000000000, 0.0000000000, 0.0000000000], [-10.0000000000, 0.0000000000, 0.0000000000], [0.0000000000, 10.0000000000, 0.0000000000], [0.0000000000, 0.0000000000, 20.0000000000], [-10.0000000000, 0.0000000000, 20.0000000000], [0.0000000000, 10.0000000000, 20.0000000000]]);'),

]   

other_test_cases = [
    (                                   euclidify,      [[0,0,0]],          'Vector3(0.00, 0.00, 0.00)'),
    ( 'euclidify_recursive',            euclidify,      [[[0,0,0], [1,0,0]]], '[Vector3(0.00, 0.00, 0.00), Vector3(1.00, 0.00, 0.00)]'),
    ( 'euclidify_Vector',               euclidify,      [Vector3(0,0,0)], 'Vector3(0.00, 0.00, 0.00)'),
    ( 'euclidify_recursive_Vector',     euclidify,      [[Vector3(0,0,0), Vector3(0,0,1)]],  '[Vector3(0.00, 0.00, 0.00), Vector3(0.00, 0.00, 1.00)]'),
    (                                   euc_to_arr,     [Vector3(0,0,0)], '[0, 0, 0]'),
    ( 'euc_to_arr_recursive',           euc_to_arr,     [[Vector3(0,0,0), Vector3(0,0,1)]], '[[0, 0, 0], [0, 0, 1]]'),
    ( 'euc_to_arr_arr',                 euc_to_arr,     [[0,0,0]], '[0, 0, 0]'),
    ( 'euc_to_arr_arr_recursive',       euc_to_arr,     [[[0,0,0], [1,0,0]]], '[[0, 0, 0], [1, 0, 0]]'),
    (                                   is_scad,        [cube(2)], 'True'),
    ( 'is_scad_false',                  is_scad,        [2], 'False'),
    ( 'transform_to_point_single_arr',  transform_to_point, [[1,0,0], [2,2,2], [3,3,1]], 'Point3(2.71, 1.29, 2.00)'),
    ( 'transform_to_point_single_pt3',  transform_to_point, [Point3(1,0,0), [2,2,2], [3,3,1]], 'Point3(2.71, 1.29, 2.00)'),
    ( 'transform_to_point_arr_arr',     transform_to_point, [[[1,0,0], [0,1,0], [0,0,1]]  , [2,2,2], [3,3,1]], '[Point3(2.71, 1.29, 2.00), Point3(1.84, 1.84, 2.97), Point3(1.31, 1.31, 1.77)]'),
    ( 'transform_to_point_pt3_arr',     transform_to_point, [[Point3(1,0,0), Point3(0,1,0), Point3(0,0,1)], [2,2,2], [3,3,1]], '[Point3(2.71, 1.29, 2.00), Point3(1.84, 1.84, 2.97), Point3(1.31, 1.31, 1.77)]') ,
    ( 'transform_to_point_redundant',   transform_to_point, [ [Point3(0,0,0), Point3(10,0,0), Point3(0,10,0)], [2,2,2], Vector3(0,0,1), Point3(0,0,0), Vector3(0,1,0), Vector3(0,0,1)], '[Point3(2.00, 2.00, 2.00), Point3(-8.00, 2.00, 2.00), Point3(2.00, 12.00, 2.00)]'),
    ( 'offset_points_inside',           offset_points,  [tri, 2, True],  '[Point3(2.00, 2.00, 0.00), Point3(5.17, 2.00, 0.00), Point3(2.00, 5.17, 0.00)]'),
    ( 'offset_points_outside',          offset_points,  [tri, 2, False], '[Point3(-2.00, -2.00, 0.00), Point3(14.83, -2.00, 0.00), Point3(-2.00, 14.83, 0.00)]'),
    ( 'offset_points_open_poly',        offset_points,  [tri, 2, False, False], '[Point3(0.00, -2.00, 0.00), Point3(14.83, -2.00, 0.00), Point3(1.41, 11.41, 0.00)]'),
]


class TestSPUtils(DiffOutput):
    # Test cases will be dynamically added to this instance
    # using the test case arrays above

    def test_split_body_planar(self):
        offset = [10, 10, 10]
        body = translate(offset)(sphere(20))
        body_bb = BoundingBox([40, 40, 40], offset)
        actual = []
        for split_dir in [RIGHT_VEC, FORWARD_VEC, UP_VEC]:
            actual_tuple = split_body_planar(body, body_bb, cutting_plane_normal=split_dir, cut_proportion=0.25)
            actual.append(actual_tuple)

        # Ignore the bounding box object that come back, taking only the SCAD
        # objects
        actual = [scad_render(a) for splits in actual for a in splits[::2]]

        expected = ['\n\nintersection() {\n\ttranslate(v = [10, 10, 10]) {\n\t\tsphere(r = 20);\n\t}\n\ttranslate(v = [-5.0000000000, 10, 10]) {\n\t\tcube(center = true, size = [10.0000000000, 40, 40]);\n\t}\n}',
                    '\n\nintersection() {\n\ttranslate(v = [10, 10, 10]) {\n\t\tsphere(r = 20);\n\t}\n\ttranslate(v = [15.0000000000, 10, 10]) {\n\t\tcube(center = true, size = [30.0000000000, 40, 40]);\n\t}\n}',
                    '\n\nintersection() {\n\ttranslate(v = [10, 10, 10]) {\n\t\tsphere(r = 20);\n\t}\n\ttranslate(v = [10, -5.0000000000, 10]) {\n\t\tcube(center = true, size = [40, 10.0000000000, 40]);\n\t}\n}',
                    '\n\nintersection() {\n\ttranslate(v = [10, 10, 10]) {\n\t\tsphere(r = 20);\n\t}\n\ttranslate(v = [10, 15.0000000000, 10]) {\n\t\tcube(center = true, size = [40, 30.0000000000, 40]);\n\t}\n}',
                    '\n\nintersection() {\n\ttranslate(v = [10, 10, 10]) {\n\t\tsphere(r = 20);\n\t}\n\ttranslate(v = [10, 10, -5.0000000000]) {\n\t\tcube(center = true, size = [40, 40, 10.0000000000]);\n\t}\n}',
                    '\n\nintersection() {\n\ttranslate(v = [10, 10, 10]) {\n\t\tsphere(r = 20);\n\t}\n\ttranslate(v = [10, 10, 15.0000000000]) {\n\t\tcube(center = true, size = [40, 40, 30.0000000000]);\n\t}\n}'
                    ]
        self.assertEqual(actual, expected)

    def test_fillet_2d_add(self):
        pts = [[0, 5], [5, 5], [5, 0], [10, 0], [10, 10], [0, 10], ]
        p = polygon(pts)
        newp = fillet_2d(euclidify(pts[0:3], Point3), orig_poly=p, fillet_rad=2, remove_material=False)
        expected = '\n\nunion() {\n\tpolygon(paths = [[0, 1, 2, 3, 4, 5]], points = [[0, 5], [5, 5], [5, 0], [10, 0], [10, 10], [0, 10]]);\n\ttranslate(v = [3.0000000000, 3.0000000000, 0.0000000000]) {\n\t\tdifference() {\n\t\t\tintersection() {\n\t\t\t\trotate(a = 358.0000000000) {\n\t\t\t\t\ttranslate(v = [-998, 0]) {\n\t\t\t\t\t\tsquare(center = false, size = [1000, 1000]);\n\t\t\t\t\t}\n\t\t\t\t}\n\t\t\t\trotate(a = 452.0000000000) {\n\t\t\t\t\ttranslate(v = [-998, -1000]) {\n\t\t\t\t\t\tsquare(center = false, size = [1000, 1000]);\n\t\t\t\t\t}\n\t\t\t\t}\n\t\t\t}\n\t\t\tcircle(r = 2);\n\t\t}\n\t}\n}'
        actual = scad_render(newp)
        self.assertEqual(expected, actual)

    def test_fillet_2d_remove(self):
        pts = tri
        poly = polygon(euc_to_arr(tri))

        newp = fillet_2d(tri, orig_poly=poly, fillet_rad=2, remove_material=True)
        expected = '\n\ndifference() {\n\tpolygon(paths = [[0, 1, 2]], points = [[0, 0, 0], [10, 0, 0], [0, 10, 0]]);\n\ttranslate(v = [5.1715728753, 2.0000000000, 0.0000000000]) {\n\t\tdifference() {\n\t\t\tintersection() {\n\t\t\t\trotate(a = 268.0000000000) {\n\t\t\t\t\ttranslate(v = [-998, 0]) {\n\t\t\t\t\t\tsquare(center = false, size = [1000, 1000]);\n\t\t\t\t\t}\n\t\t\t\t}\n\t\t\t\trotate(a = 407.0000000000) {\n\t\t\t\t\ttranslate(v = [-998, -1000]) {\n\t\t\t\t\t\tsquare(center = false, size = [1000, 1000]);\n\t\t\t\t\t}\n\t\t\t\t}\n\t\t\t}\n\t\t\tcircle(r = 2);\n\t\t}\n\t}\n}'
        actual = scad_render(newp)
        if expected != actual:
            print(''.join(difflib.unified_diff(expected, actual)))
        self.assertEqual(expected, actual)


def test_generator_scad(func, args, expected):
    def test_scad(self):
        scad_obj = func(*args)
        actual = scad_render(scad_obj)
        self.assertEqual(expected, actual)

    return test_scad


def test_generator_no_scad(func, args, expected):
    def test_no_scad(self):
        actual = str(func(*args))
        self.assertEqual(expected, actual)

    return test_no_scad


def read_test_tuple(test_tuple):
    if len(test_tuple) == 3:
        # If test name not supplied, create it programmatically
        func, args, expected = test_tuple
        test_name = 'test_%s' % func.__name__
    elif len(test_tuple) == 4:
        test_name, func, args, expected = test_tuple
        test_name = 'test_%s' % test_name
    else:
        print("test_tuple has %d args :%s" % (len(test_tuple), test_tuple))
    return test_name, func, args, expected


def create_tests():
    for test_tuple in scad_test_cases:
        test_name, func, args, expected = read_test_tuple(test_tuple)
        test = test_generator_scad(func, args, expected)
        setattr(TestSPUtils, test_name, test)

    for test_tuple in other_test_cases:
        test_name, func, args, expected = read_test_tuple(test_tuple)
        test = test_generator_no_scad(func, args, expected)
        setattr(TestSPUtils, test_name, test)

if __name__ == '__main__':
    create_tests()
    unittest.main()
