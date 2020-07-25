#! /usr/bin/env python
import difflib
import unittest
import re
from euclid3 import Point3, Vector3, Point2

from solid import scad_render
from solid.objects import cube, polygon, sphere, translate
from solid.test.ExpandedTestCase import DiffOutput
from solid.utils import BoundingBox, arc, arc_inverted, euc_to_arr, euclidify 
from solid.utils import extrude_along_path, fillet_2d, is_scad, offset_points
from solid.utils import split_body_planar, transform_to_point, project_to_2D
from solid.utils import path_2d, path_2d_polygon
from solid.utils import FORWARD_VEC, RIGHT_VEC, UP_VEC
from solid.utils import back, down, forward, left, right, up
from solid.utils import label

tri = [Point3(0, 0, 0), Point3(10, 0, 0), Point3(0, 10, 0)]

scad_test_cases = [
    # Test name, function, args, expected value
    ('up', up, [2], '\n\ntranslate(v = [0, 0, 2]);'),
    ('down', down, [2], '\n\ntranslate(v = [0, 0, -2]);'),
    ('left', left, [2], '\n\ntranslate(v = [-2, 0, 0]);'),
    ('right', right, [2], '\n\ntranslate(v = [2, 0, 0]);'),
    ('forward', forward, [2], '\n\ntranslate(v = [0, 2, 0]);'),
    ('back', back, [2], '\n\ntranslate(v = [0, -2, 0]);'),
    ('arc', arc, [10, 0, 90, 24], '\n\ndifference() {\n\tcircle($fn = 24, r = 10);\n\trotate(a = 0) {\n\t\ttranslate(v = [0, -10, 0]) {\n\t\t\tsquare(center = true, size = [30, 20]);\n\t\t}\n\t}\n\trotate(a = -90) {\n\t\ttranslate(v = [0, -10, 0]) {\n\t\t\tsquare(center = true, size = [30, 20]);\n\t\t}\n\t}\n}'),
    ('arc_inverted', arc_inverted, [10, 0, 90, 24], '\n\ndifference() {\n\tintersection() {\n\t\trotate(a = 0) {\n\t\t\ttranslate(v = [-990, 0, 0]) {\n\t\t\t\tsquare(center = false, size = [1000, 1000]);\n\t\t\t}\n\t\t}\n\t\trotate(a = 90) {\n\t\t\ttranslate(v = [-990, -1000, 0]) {\n\t\t\t\tsquare(center = false, size = [1000, 1000]);\n\t\t\t}\n\t\t}\n\t}\n\tcircle($fn = 24, r = 10);\n}'),
    ('transform_to_point_scad', transform_to_point, [cube(2), [2, 2, 2], [3, 3, 1]], '\n\nmultmatrix(m = [[0.7071067812, -0.1622214211, -0.6882472016, 2], [-0.7071067812, -0.1622214211, -0.6882472016, 2], [0.0000000000, 0.9733285268, -0.2294157339, 2], [0, 0, 0, 1.0000000000]]) {\n\tcube(size = 2);\n}'),
    ('extrude_along_path', extrude_along_path, [tri, [[0, 0, 0], [0, 20, 0]]], '\n\npolyhedron(faces = [[0, 3, 1], [1, 3, 4], [1, 4, 2], [2, 4, 5], [0, 2, 5], [0, 5, 3], [0, 1, 2], [3, 5, 4]], points = [[0.0000000000, 0.0000000000, 0.0000000000], [10.0000000000, 0.0000000000, 0.0000000000], [0.0000000000, 0.0000000000, 10.0000000000], [0.0000000000, 20.0000000000, 0.0000000000], [10.0000000000, 20.0000000000, 0.0000000000], [0.0000000000, 20.0000000000, 10.0000000000]]);'),
    ('extrude_along_path_vertical', extrude_along_path, [tri, [[0, 0, 0], [0, 0, 20]]], '\n\npolyhedron(faces = [[0, 3, 1], [1, 3, 4], [1, 4, 2], [2, 4, 5], [0, 2, 5], [0, 5, 3], [0, 1, 2], [3, 5, 4]], points = [[0.0000000000, 0.0000000000, 0.0000000000], [-10.0000000000, 0.0000000000, 0.0000000000], [0.0000000000, 10.0000000000, 0.0000000000], [0.0000000000, 0.0000000000, 20.0000000000], [-10.0000000000, 0.0000000000, 20.0000000000], [0.0000000000, 10.0000000000, 20.0000000000]]);'),

]

other_test_cases = [
    # Test name, function, args, expected value
    ('euclidify', euclidify, [[0, 0, 0]], 'Vector3(0.00, 0.00, 0.00)'),
    ('euclidify_recursive', euclidify, [[[0, 0, 0], [1, 0, 0]]], '[Vector3(0.00, 0.00, 0.00), Vector3(1.00, 0.00, 0.00)]'),
    ('euclidify_Vector', euclidify, [Vector3(0, 0, 0)], 'Vector3(0.00, 0.00, 0.00)'),
    ('euclidify_recursive_Vector', euclidify, [[Vector3(0, 0, 0), Vector3(0, 0, 1)]], '[Vector3(0.00, 0.00, 0.00), Vector3(0.00, 0.00, 1.00)]'),
    ('euclidify_3_to_2', euclidify, [Point3(0,1,2), Point2], 'Point2(0.00, 1.00)'),
    ('euc_to_arr', euc_to_arr, [Vector3(0, 0, 0)], '[0, 0, 0]'),
    ('euc_to_arr_recursive', euc_to_arr, [[Vector3(0, 0, 0), Vector3(0, 0, 1)]], '[[0, 0, 0], [0, 0, 1]]'),
    ('euc_to_arr_arr', euc_to_arr, [[0, 0, 0]], '[0, 0, 0]'),
    ('euc_to_arr_arr_recursive', euc_to_arr, [[[0, 0, 0], [1, 0, 0]]], '[[0, 0, 0], [1, 0, 0]]'),
    ('is_scad', is_scad, [cube(2)], 'True'),
    ('is_scad_false', is_scad, [2], 'False'),
    ('transform_to_point_single_arr', transform_to_point, [[1, 0, 0], [2, 2, 2], [3, 3, 1]], 'Point3(2.71, 1.29, 2.00)'),
    ('transform_to_point_single_pt3', transform_to_point, [Point3(1, 0, 0), [2, 2, 2], [3, 3, 1]], 'Point3(2.71, 1.29, 2.00)'),
    ('transform_to_point_arr_arr', transform_to_point, [[[1, 0, 0], [0, 1, 0], [0, 0, 1]], [2, 2, 2], [3, 3, 1]], '[Point3(2.71, 1.29, 2.00), Point3(1.84, 1.84, 2.97), Point3(1.31, 1.31, 1.77)]'),
    ('transform_to_point_pt3_arr', transform_to_point, [[Point3(1, 0, 0), Point3(0, 1, 0), Point3(0, 0, 1)], [2, 2, 2], [3, 3, 1]], '[Point3(2.71, 1.29, 2.00), Point3(1.84, 1.84, 2.97), Point3(1.31, 1.31, 1.77)]'),
    ('transform_to_point_redundant', transform_to_point, [[Point3(0, 0, 0), Point3(10, 0, 0), Point3(0, 10, 0)], [2, 2, 2], Vector3(0, 0, 1), Point3(0, 0, 0), Vector3(0, 1, 0), Vector3(0, 0, 1)], '[Point3(2.00, 2.00, 2.00), Point3(-8.00, 2.00, 2.00), Point3(2.00, 12.00, 2.00)]'),
    ('offset_points_inside', offset_points, [tri, 2, True], '[Point2(2.00, 2.00), Point2(5.17, 2.00), Point2(2.00, 5.17)]'),
    ('offset_points_outside', offset_points, [tri, 2, False], '[Point2(-2.00, -2.00), Point2(14.83, -2.00), Point2(-2.00, 14.83)]'),
]


class TestSPUtils(DiffOutput):
    # Test cases will be dynamically added to this instance
    # using the test case arrays above
    def assertEqualNoWhitespace(self, a, b):
        remove_whitespace = lambda s: re.subn(r'[\s\n]','', s)[0]
        self.assertEqual(remove_whitespace(a), remove_whitespace(b))

    def test_split_body_planar(self):
        offset = [10, 10, 10]
        body = translate(offset)(sphere(20))
        body_bb = BoundingBox([40, 40, 40], offset)
        actual = []
        for split_dir in [RIGHT_VEC, FORWARD_VEC, UP_VEC]:
            actual_tuple = split_body_planar(body, body_bb, cutting_plane_normal=split_dir, cut_proportion=0.25)
            actual.append(actual_tuple)

        # Ignore the bounding box object that come back, taking only the SCAD objects
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
        three_points = [euclidify(pts[0:3], Point2)]
        newp = fillet_2d(three_points, orig_poly=p, fillet_rad=2, remove_material=False)
        expected = 'union(){polygon(paths=[[0,1,2,3,4,5]],points=[[0,5],[5,5],[5,0],[10,0],[10,10],[0,10]]);translate(v=[3.0000000000,3.0000000000]){difference(){intersection(){rotate(a=359.9000000000){translate(v=[-998,0,0]){square(center=false,size=[1000,1000]);}}rotate(a=450.1000000000){translate(v=[-998,-1000,0]){square(center=false,size=[1000,1000]);}}}circle(r=2);}}}'
        actual = scad_render(newp)
        self.assertEqualNoWhitespace(expected, actual)

    def test_fillet_2d_remove(self):
        pts = list((project_to_2D(p) for p in tri))
        poly = polygon(euc_to_arr(pts))
        newp = fillet_2d([pts], orig_poly=poly, fillet_rad=2, remove_material=True)
        expected = 'difference(){polygon(paths=[[0,1,2]],points=[[0,0],[10,0],[0,10]]);translate(v=[5.1715728753,2.0000000000]){difference(){intersection(){rotate(a=-90.1000000000){translate(v=[-998,0,0]){square(center=false,size=[1000,1000]);}}rotate(a=45.1000000000){translate(v=[-998,-1000,0]){square(center=false,size=[1000,1000]);}}}circle(r=2);}}}'
        actual = scad_render(newp)

        self.assertEqualNoWhitespace(expected, actual)
    
    def test_euclidify_non_mutating(self):
        base_tri = [Point2(0, 0), Point2(10, 0), Point2(0, 10)]
        next_tri = euclidify(base_tri, Point2)
        expected = 3
        actual = len(base_tri)
        self.assertEqual(expected, actual, 'euclidify should not mutate its arguments')

    def test_offset_points_closed(self):
        actual = euc_to_arr(offset_points(tri, offset=1, closed=True))
        expected = [[1.0, 1.0], [7.585786437626904, 1.0], [1.0, 7.585786437626905]]
        self.assertEqual(expected, actual)

    def test_offset_points_open(self):
        actual = euc_to_arr(offset_points(tri, offset=1, closed=False))
        expected = [[0.0, 1.0], [7.585786437626904, 1.0], [-0.7071067811865479, 9.292893218813452]]
        self.assertEqual(expected, actual)

    def test_path_2d(self):
        base_tri = [Point2(0, 0), Point2(10, 0), Point2(10, 10)]
        actual = euc_to_arr(path_2d(base_tri, width=2, closed=False))
        expected = [
            [0.0, 1.0], [9.0, 1.0], [9.0, 10.0], 
            [11.0, 10.0], [11.0, -1.0], [0.0, -1.0]
        ]
        self.assertEqual(expected, actual)

    def test_path_2d_polygon(self):
        base_tri = [Point2(0, 0), Point2(10, 0), Point2(10, 10), Point2(0,10)]
        poly = path_2d_polygon(base_tri, width=2, closed=True)
        expected = [
            (1.0, 1.0), (9.0, 1.0), (9.0, 9.0), (1.0, 9.0), 
            (-1.0, 11.0), (11.0, 11.0), (11.0, -1.0), (-1.0, -1.0)
        ]
        actual = euc_to_arr(poly.params['points'])
        self.assertEqual(expected, actual)

        # Make sure the inner and outer paths in the polygon are disjoint
        expected = [[0,1,2,3],[4,5,6,7]]
        actual = poly.params['paths']
        self.assertEqual(expected, actual)
    
    # def test_offset_points_inside(self):
    #     expected = ''
    #     actual = scad_render(offset_points(tri2d, offset=2, internal=True))
    #     self.assertEqualNoWhitespace(expected, actual)

    def test_extrude_along_path_numpy(self):
        try: 
            import numpy as np
        except ImportError:
            return

        N = 3
        thetas=np.linspace(0,np.pi,N) 
        path=list(zip(3*np.sin(thetas),3*np.cos(thetas),thetas)) 
        profile=list(zip(np.sin(thetas),np.cos(thetas), [0]*len(thetas))) 
        scalepts=list(np.linspace(1,.1,N))   

        # in earlier code, this would have thrown an exception
        a = extrude_along_path(shape_pts=profile, path_pts=path, scale_factors=scalepts)
 
    
    def test_label(self):
        expected = 'translate(v=[0,5.0000000000,0]){resize(newsize=[15,0,0.5000000000]){union(){translate(v=[0,0.0000000000,0]){linear_extrude(height=1){text($fn=40,font="MgOpenModata:style=Bold",halign="left",spacing=1,text="Hello,",valign="baseline");}}translate(v=[0,-11.5000000000,0]){linear_extrude(height=1){text($fn=40,font="MgOpenModata:style=Bold",halign="left",spacing=1,text="World",valign="baseline");}}}}}'
        actual = scad_render(label("Hello,\nWorld"))
        self.assertEqualNoWhitespace(expected, actual)


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
        test_name = f'test_{func.__name__}'
    elif len(test_tuple) == 4:
        test_name, func, args, expected = test_tuple
        test_name = f'test_{test_name}'
    else:
        print(f"test_tuple has {len(test_tuple):d} args :{test_tuple}")
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
