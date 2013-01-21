#! /usr/bin/python
# -*- coding: UTF-8 -*-
import os, sys, re

import unittest
from solid import *

scad_test_case_templates = [
{'expected': '\n\npolygon(paths = [[0, 1, 2]], points = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]);', 'args': {'points': [[0, 0, 0], [1, 0, 0], [0, 1, 0]]}, 'name': 'polygon', 'kwargs': {'paths': [[0, 1, 2]]}},
{'expected': '\n\ncircle(r = 1, $fn = 12);', 'args': {}, 'name': 'circle', 'kwargs': {'segments': 12, 'r': 1}},
{'expected': '\n\nsquare(center = false, size = 1);', 'args': {}, 'name': 'square', 'kwargs': {'center': False, 'size': 1}},
{'expected': '\n\nsphere(r = 1, $fn = 12);', 'args': {}, 'name': 'sphere', 'kwargs': {'segments': 12, 'r': 1}},
{'expected': '\n\ncube(center = false, size = 1);', 'args': {}, 'name': 'cube', 'kwargs': {'center': False, 'size': 1}},
{'expected': '\n\ncylinder($fn = 12, h = 1, r = 1, center = false);', 'args': {}, 'name': 'cylinder', 'kwargs': {'r1': None, 'r2': None, 'h': 1, 'segments': 12, 'r': 1, 'center': False}},
{'expected': '\n\npolyhedron(points = [[0, 0, 0], [1, 0, 0], [0, 1, 0]], triangles = [[0, 1, 2]]);', 'args': {'points': [[0, 0, 0], [1, 0, 0], [0, 1, 0]], 'triangles': [[0, 1, 2]]}, 'name': 'polyhedron', 'kwargs': {'convexity': None}},
{'expected': '\n\nunion();', 'args': {}, 'name': 'union', 'kwargs': {}},
{'expected': '\n\nintersection();', 'args': {}, 'name': 'intersection', 'kwargs': {}},
{'expected': '\n\ndifference();', 'args': {}, 'name': 'difference', 'kwargs': {}},
{'expected': '\n\ntranslate(v = [1, 0, 0]);', 'args': {}, 'name': 'translate', 'kwargs': {'v': [1, 0, 0]}},
{'expected': '\n\nscale(v = 0.5000000000);', 'args': {}, 'name': 'scale', 'kwargs': {'v': 0.5}},
{'expected': '\n\nrotate(a = 45, v = [0, 0, 1]);', 'args': {}, 'name': 'rotate', 'kwargs': {'a': 45, 'v': [0, 0, 1]}},
{'expected': '\n\nmirror(v = [0, 0, 1]);', 'args': {'v': [0, 0, 1]}, 'name': 'mirror', 'kwargs': {}},
{'expected': '\n\nmultmatrix(m = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]);', 'args': {'m': [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]}, 'name': 'multmatrix', 'kwargs': {}},
{'expected': '\n\ncolor(c = [1, 0, 0]);', 'args': {'c': [1, 0, 0]}, 'name': 'color', 'kwargs': {}},
{'expected': '\n\nminkowski();', 'args': {}, 'name': 'minkowski', 'kwargs': {}},
{'expected': '\n\nhull();', 'args': {}, 'name': 'hull', 'kwargs': {}},
{'expected': '\n\nrender();', 'args': {}, 'name': 'render', 'kwargs': {'convexity': None}},
{'expected': '\n\nlinear_extrude(center = false, height = 1);', 'args': {}, 'name': 'linear_extrude', 'kwargs': {'twist': None, 'slices': None, 'center': False, 'convexity': None, 'height': 1}},
{'expected': '\n\nrotate_extrude();', 'args': {}, 'name': 'rotate_extrude', 'kwargs': {'convexity': None}},
{'expected': '\n\ndxf_linear_extrude(center = false, height = 1, file = "/Path/to/dummy.dxf");', 'args': {'file': "'/Path/to/dummy.dxf'"}, 'name': 'dxf_linear_extrude', 'kwargs': {'layer': None, 'center': False, 'slices': None, 'height': 1, 'twist': None, 'convexity': None}},
{'expected': '\n\nprojection();', 'args': {}, 'name': 'projection', 'kwargs': {'cut': None}},
{'expected': '\n\nsurface(center = false, file = "/Path/to/dummy.dxf");', 'args': {'file': "'/Path/to/dummy.dxf'"}, 'name': 'surface', 'kwargs': {'center': False, 'convexity': None}},
{'expected': '\n\nimport_stl(filename = "/Path/to/dummy.dxf");', 'args': {'filename': "'/Path/to/dummy.dxf'"}, 'name': 'import_stl', 'kwargs': {'convexity': None}},
{'expected': '\n\nintersection_for(n = [0, 1, 2]);', 'args': {'n': [0, 1, 2]}, 'name': 'intersection_for', 'kwargs': {}},
]

class TestSolidPython( unittest.TestCase):
    # test cases will be dynamically added to this instance
    def test_infix_union( self):
        a = cube(2)
        b = sphere( 2)
        expected = '\n\nunion() {\n\tcube(size = 2);\n\tsphere(r = 2);\n}'
        actual = scad_render( a+b)
        self.assertEqual( expected, actual)
    
    def test_infix_difference( self):
        a = cube(2)
        b = sphere( 2)
        expected = '\n\ndifference() {\n\tcube(size = 2);\n\tsphere(r = 2);\n}'
        actual = scad_render( a-b)
        self.assertEqual( expected, actual)
    
    def test_infix_intersection( self):
        a = cube(2)
        b = sphere( 2)
        expected = '\n\nintersection() {\n\tcube(size = 2);\n\tsphere(r = 2);\n}'
        actual = scad_render( a*b)
        self.assertEqual( expected, actual)
    

def single_test( test_dict):
    name, args, kwargs, expected = test_dict['name'], test_dict['args'], test_dict['kwargs'], test_dict['expected']
    
    def test( self):
        call_str= name + "(" 
        for k, v in args.items():
            call_str += "%s=%s, "%(k,v)
        for k, v in kwargs.items():
            call_str += "%s=%s, "%(k,v)
        call_str += ')'
        
        scad_obj = eval( call_str)
        actual = scad_render( scad_obj)
        
        self.assertEqual( expected, actual)
    
    return test
    
def generate_cases_from_templates():
    for test_dict in scad_test_case_templates:
        test = single_test( test_dict)
        test_name = "test_%(name)s"%test_dict
        setattr( TestSolidPython, test_name, test)     


if __name__ == '__main__':
    generate_cases_from_templates()                           
    unittest.main()