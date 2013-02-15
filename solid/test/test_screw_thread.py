#! /usr/bin/python
# -*- coding: UTF-8 -*-
from __future__ import division
import os, sys, re

# Assumes SolidPython is in site-packages or elsewhwere in sys.path
import unittest
from solid import *
from solid.screw_thread import thread, default_thread_section

class TestScrewThread( unittest.TestCase):
    def test_thread( self):
        tooth_height = 10
        tooth_depth = 5
        outline = default_thread_section( tooth_height=tooth_height, tooth_depth=tooth_depth)
        actual_obj = thread( outline_pts=outline, inner_rad=20, pitch=2*tooth_height, length=2*tooth_height, segments_per_rot=4,
                        neck_in_degrees=0, neck_out_degrees=0)
        actual = scad_render( actual_obj)
        expected = '\n\nrender() {\n\tdifference() {\n\t\tpolyhedron(points = [[20.0000000000, 0.0000000000, -5.0000000000], [25.0000000000, 0.0000000000, 0.0000000000], [20.0000000000, 0.0000000000, 5.0000000000], [0.0000000000, 20.0000000000, 0.0000000000], [0.0000000000, 25.0000000000, 5.0000000000], [0.0000000000, 20.0000000000, 10.0000000000], [-20.0000000000, 0.0000000000, 5.0000000000], [-25.0000000000, 0.0000000000, 10.0000000000], [-20.0000000000, 0.0000000000, 15.0000000000], [-0.0000000000, -20.0000000000, 10.0000000000], [-0.0000000000, -25.0000000000, 15.0000000000], [-0.0000000000, -20.0000000000, 20.0000000000]], triangles = [[0, 1, 3], [1, 4, 3], [1, 2, 4], [2, 5, 4], [0, 5, 2], [0, 3, 5], [3, 4, 6], [4, 7, 6], [4, 5, 7], [5, 8, 7], [3, 8, 5], [3, 6, 8], [6, 7, 9], [7, 10, 9], [7, 8, 10], [8, 11, 10], [6, 11, 8], [6, 9, 11], [0, 2, 1], [9, 10, 11]]);\n\t\tunion() {\n\t\t\ttranslate(v = [0, 0, -5]) {\n\t\t\t\tcylinder(h = 30, r = 20);\n\t\t\t}\n\t\t\ttranslate(v = [0, 0, -25]) {\n\t\t\t\tcube(center = true, size = 50);\n\t\t\t}\n\t\t\ttranslate(v = [0, 0, 45]) {\n\t\t\t\tcube(center = true, size = 50);\n\t\t\t}\n\t\t}\n\t}\n}'
        self.assertEqual( expected, actual)
    
    def test_thread_internal( self):
        tooth_height = 10
        tooth_depth = 5
        outline = default_thread_section( tooth_height=tooth_height, tooth_depth=tooth_depth)
        actual_obj = thread( outline_pts=outline, inner_rad=20, pitch=2*tooth_height, length=2*tooth_height, 
                                external=False, segments_per_rot=4,neck_in_degrees=0, neck_out_degrees=0)
        actual = scad_render( actual_obj)
        expected = '\n\nrender() {\n\tintersection() {\n\t\tpolyhedron(points = [[20.0000000000, 0.0000000000, -5.0000000000], [15.0000000000, 0.0000000000, 0.0000000000], [20.0000000000, 0.0000000000, 5.0000000000], [0.0000000000, 20.0000000000, 0.0000000000], [0.0000000000, 15.0000000000, 5.0000000000], [0.0000000000, 20.0000000000, 10.0000000000], [-20.0000000000, 0.0000000000, 5.0000000000], [-15.0000000000, 0.0000000000, 10.0000000000], [-20.0000000000, 0.0000000000, 15.0000000000], [-0.0000000000, -20.0000000000, 10.0000000000], [-0.0000000000, -15.0000000000, 15.0000000000], [-0.0000000000, -20.0000000000, 20.0000000000]], triangles = [[0, 1, 3], [1, 4, 3], [1, 2, 4], [2, 5, 4], [0, 5, 2], [0, 3, 5], [3, 4, 6], [4, 7, 6], [4, 5, 7], [5, 8, 7], [3, 8, 5], [3, 6, 8], [6, 7, 9], [7, 10, 9], [7, 8, 10], [8, 11, 10], [6, 11, 8], [6, 9, 11], [0, 2, 1], [9, 10, 11]]);\n\t\tcylinder($fn = 4, h = 20, r = 20);\n\t}\n}'
        self.assertEqual( expected, actual)        
        
    def test_default_thread_section( self):
        expected = [[0, -5], [5, 0], [0, 5]]
        actual = default_thread_section( tooth_height=10, tooth_depth=5)
        self.assertEqual( expected, actual)
    


if __name__ == '__main__':
    unittest.main()