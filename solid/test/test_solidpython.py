#! /usr/bin/python
# -*- coding: UTF-8 -*-
import os, sys, re

import unittest
from solid import *

scad_test_case_templates = [
{'name': 'polygon',     'kwargs': {'paths': [[0, 1, 2]]}, 'expected': '\n\npolygon(paths = [[0, 1, 2]], points = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]);', 'args': {'points': [[0, 0, 0], [1, 0, 0], [0, 1, 0]]}, },
{'name': 'circle',      'kwargs': {'segments': 12, 'r': 1}, 'expected': '\n\ncircle(r = 1, $fn = 12);', 'args': {}, },
{'name': 'square',      'kwargs': {'center': False, 'size': 1}, 'expected': '\n\nsquare(center = false, size = 1);', 'args': {}, },
{'name': 'sphere',      'kwargs': {'segments': 12, 'r': 1}, 'expected': '\n\nsphere(r = 1, $fn = 12);', 'args': {}, },
{'name': 'cube',        'kwargs': {'center': False, 'size': 1}, 'expected': '\n\ncube(center = false, size = 1);', 'args': {}, },
{'name': 'cylinder',    'kwargs': {'r1': None, 'r2': None, 'h': 1, 'segments': 12, 'r': 1, 'center': False}, 'expected': '\n\ncylinder($fn = 12, h = 1, r = 1, center = false);', 'args': {}, },
{'name': 'polyhedron',  'kwargs': {'convexity': None}, 'expected': '\n\npolyhedron(points = [[0, 0, 0], [1, 0, 0], [0, 1, 0]], triangles = [[0, 1, 2]]);', 'args': {'points': [[0, 0, 0], [1, 0, 0], [0, 1, 0]], 'triangles': [[0, 1, 2]]}, },
{'name': 'union',       'kwargs': {}, 'expected': '\n\nunion();', 'args': {}, },
{'name': 'intersection','kwargs': {}, 'expected': '\n\nintersection();', 'args': {}, },
{'name': 'difference',  'kwargs': {}, 'expected': '\n\ndifference();', 'args': {}, },
{'name': 'translate',   'kwargs': {'v': [1, 0, 0]}, 'expected': '\n\ntranslate(v = [1, 0, 0]);', 'args': {}, },
{'name': 'scale',       'kwargs': {'v': 0.5}, 'expected': '\n\nscale(v = 0.5000000000);', 'args': {}, },
{'name': 'rotate',      'kwargs': {'a': 45, 'v': [0, 0, 1]}, 'expected': '\n\nrotate(a = 45, v = [0, 0, 1]);', 'args': {}, },
{'name': 'mirror',      'kwargs': {}, 'expected': '\n\nmirror(v = [0, 0, 1]);', 'args': {'v': [0, 0, 1]}, },
{'name': 'multmatrix',  'kwargs': {}, 'expected': '\n\nmultmatrix(m = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]);', 'args': {'m': [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]}, },
{'name': 'color',       'kwargs': {}, 'expected': '\n\ncolor(c = [1, 0, 0]);', 'args': {'c': [1, 0, 0]}, },
{'name': 'minkowski',   'kwargs': {}, 'expected': '\n\nminkowski();', 'args': {}, },
{'name': 'hull',        'kwargs': {}, 'expected': '\n\nhull();', 'args': {}, },
{'name': 'render',      'kwargs': {'convexity': None}, 'expected': '\n\nrender();', 'args': {}, },
{'name': 'projection',  'kwargs': {'cut': None}, 'expected': '\n\nprojection();', 'args': {}, },
{'name': 'surface',     'kwargs': {'center': False, 'convexity': None}, 'expected': '\n\nsurface(center = false, file = "/Path/to/dummy.dxf");', 'args': {'file': "'/Path/to/dummy.dxf'"}, },
{'name': 'import_stl',  'kwargs': {'convexity': None}, 'expected': '\n\nimport_stl(filename = "/Path/to/dummy.dxf");', 'args': {'filename': "'/Path/to/dummy.dxf'"}, },
{'name': 'linear_extrude',      'kwargs': {'twist': None, 'slices': None, 'center': False, 'convexity': None, 'height': 1}, 'expected': '\n\nlinear_extrude(center = false, height = 1);', 'args': {}, },
{'name': 'rotate_extrude',      'kwargs': {'convexity': None}, 'expected': '\n\nrotate_extrude();', 'args': {}, },
{'name': 'dxf_linear_extrude',  'kwargs': {'layer': None, 'center': False, 'slices': None, 'height': 1, 'twist': None, 'convexity': None}, 'expected': '\n\ndxf_linear_extrude(center = false, height = 1, file = "/Path/to/dummy.dxf");', 'args': {'file': "'/Path/to/dummy.dxf'"}, },
{'name': 'intersection_for',    'kwargs': {}, 'expected': '\n\nintersection_for(n = [0, 1, 2]);', 'args': {'n': [0, 1, 2]}, },
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
    
    def test_parse_scad_callables( self):
        test_str = (""
        "module hex (width=10, height=10,    \n"
        "            flats= true, center=false){}\n"
        "function righty (angle=90) = 1;\n"
        "function lefty( avar) = 2;\n"
        "module more( a=[something, other]) {}\n"
        "module pyramid(side=10, height=-1, square=false, centerHorizontal=true, centerVertical=false){}\n"
        "module no_comments( arg=10,   //test comment\n"
        "other_arg=2, /* some extra comments\n"
        "on empty lines */\n"
        "last_arg=4){}\n"
        "module float_arg( arg=1.0){}\n")
        expected = [{'args': [], 'name': 'hex', 'kwargs': ['width', 'height', 'flats', 'center']}, {'args': [], 'name': 'righty', 'kwargs': ['angle']}, {'args': ['avar'], 'name': 'lefty', 'kwargs': []}, {'args': [], 'name': 'more', 'kwargs': ['a']}, {'args': [], 'name': 'pyramid', 'kwargs': ['side', 'height', 'square', 'centerHorizontal', 'centerVertical']}, {'args': [], 'name': 'no_comments', 'kwargs': ['arg', 'other_arg', 'last_arg']}, {'args': [], 'name': 'float_arg', 'kwargs': ['arg']}]
        actual = parse_scad_callables( test_str)
        self.assertEqual( expected, actual)
    
    def test_background( self):
        a = cube(10)
        expected = '\n\n%cube(size = 10);'
        actual = scad_render( background( a))
        self.assertEqual( expected, actual)
    
    def test_debug( self):
        a = cube(10)
        expected =  '\n\n#cube(size = 10);'
        actual = scad_render( debug( a))
        self.assertEqual( expected, actual)
    
    def test_disable( self):
        a = cube(10)
        expected =  '\n\n*cube(size = 10);'
        actual = scad_render( disable( a))
        self.assertEqual( expected, actual)
    
    def test_root( self):
        a = cube(10)
        expected = '\n\n!cube(size = 10);'
        actual = scad_render( root( a))
        self.assertEqual( expected, actual)
    
    def test_explicit_hole( self):
        a = cube( 10, center=True) + hole()( cylinder(2, 20, center=True))        
        expected = '\ndifference() {\n\tunion() {\n\t\tcube(center = true, size = 10);\n\t}\n\t/* All Holes Below*/\n\tunion(){\n\t\tunion() {\n\t\t\tcylinder(h = 20, r = 2, center = true);\n\t\t}\n\t}\n}'
        actual = scad_render( a)
        self.assertEqual( expected, actual)
    
    def test_hole_transform_propagation( self):
        # earlier versions of holes had problems where a hole
        # that was used a couple places wouldn't propagate correctly.
        # Confirm that's still happening as it's supposed to
        h = hole()( 
                rotate( a=90, v=[0, 1, 0])( 
                    cylinder(2, 20, center=True)
                )
            )
    
        h_vert = rotate( a=-90, v=[0, 1, 0])(
                    h
                )
    
        a = cube( 10, center=True) + h + h_vert
        expected = '\ndifference() {\n\tunion() {\n\t\tunion() {\n\t\t\tcube(center = true, size = 10);\n\t\t}\n\t\trotate(a = -90, v = [0, 1, 0]) {\n\t\t}\n\t}\n\t/* All Holes Below*/\n\tunion(){\n\t\tunion(){\n\t\t\tunion() {\n\t\t\t\trotate(a = 90, v = [0, 1, 0]) {\n\t\t\t\t\tcylinder(h = 20, r = 2, center = true);\n\t\t\t\t}\n\t\t\t}\n\t\t}\n\t\trotate(a = -90, v = [0, 1, 0]){\n\t\t\tunion() {\n\t\t\t\trotate(a = 90, v = [0, 1, 0]) {\n\t\t\t\t\tcylinder(h = 20, r = 2, center = true);\n\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}\n}'
        actual = scad_render( a)
        self.assertEqual( expected, actual)


    def test_scad_render_animated_file( self):
        def my_animate( _time=0):
            import math
            # _time will range from 0 to 1, not including 1
            rads = _time * 2 * math.pi
            rad = 15
            c = translate( [rad*math.cos(rads), rad*math.sin(rads)])( square( 10))
            return c
        import tempfile
        tmp = tempfile.NamedTemporaryFile()
        
        scad_render_animated_file( my_animate, steps=2, back_and_forth=False, 
                filepath=tmp.name, include_orig_code=False)
        tmp.seek(0)
        actual = tmp.read()
        expected = '\nif ($t >= 0.0 && $t < 0.5){   \n\ttranslate(v = [15.0000000000, 0.0000000000]) {\n\t\tsquare(size = 10);\n\t}\n}\nif ($t >= 0.5 && $t < 1.0){   \n\ttranslate(v = [-15.0000000000, 0.0000000000]) {\n\t\tsquare(size = 10);\n\t}\n}\n'
        tmp.close()
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