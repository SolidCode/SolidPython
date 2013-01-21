#! /usr/bin/python
# -*- coding: UTF-8 -*-
import os, sys, re

import unittest

from solid import *
from solid.utils import *
# TODO: many of these tests require pyeuclid, but SolidPython, to date, does
# not.  These tests should account for the possibility of not having PyEuclid
# installed -ETJ 20 Jan 2013
from euclid import *

scad_test_cases = [
    ( up,           [2],   '\n\ntranslate(v = [0, 0, 2]);'),
    ( down,         [2],   '\n\ntranslate(v = [0, 0, -2]);'),
    ( left,         [2],   '\n\ntranslate(v = [-2, 0, 0]);'),
    ( right,        [2],   '\n\ntranslate(v = [2, 0, 0]);'),
    ( forward,      [2],   '\n\ntranslate(v = [0, 2, 0]);'),
    ( back,         [2],   '\n\ntranslate(v = [0, -2, 0]);'),   
    ( arc,          [10, 0, 90, 4], '\n\ndifference() {\n\tcircle(r = 10, $fn = 4);\n\trotate(a = 0) {\n\t\ttranslate(v = [0, -10, 0]) {\n\t\t\tsquare(center = true, size = [30, 20]);\n\t\t}\n\t}\n\trotate(a = -90) {\n\t\ttranslate(v = [0, -10, 0]) {\n\t\t\tsquare(center = true, size = [30, 20]);\n\t\t}\n\t}\n}'),
    ( 'arc_inverted', arc, [10, 0, 90, 4, True], '\n\ndifference() {\n\tdifference() {\n\t\tsquare(center = true, size = 20);\n\t\tcircle(r = 10, $fn = 4);\n\t}\n\trotate(a = 0) {\n\t\ttranslate(v = [0, -10, 0]) {\n\t\t\tsquare(center = true, size = [30, 20]);\n\t\t}\n\t}\n\trotate(a = -90) {\n\t\ttranslate(v = [0, -10, 0]) {\n\t\t\tsquare(center = true, size = [30, 20]);\n\t\t}\n\t}\n}'),
    ( 'transform_to_point_scad', transform_to_point, [cube(2), [2,2,2], [3,3,1]], '\n\nmultmatrix(m = [[0.7071067812, -0.1622214211, -0.6882472016, 2], [-0.7071067812, -0.1622214211, -0.6882472016, 2], [0.0000000000, 0.9733285268, -0.2294157339, 2], [0, 0, 0, 1.0000000000]]) {\n\tcube(size = 2);\n}'),
]   

other_test_cases = [
    (                                   euclidify,      [[0,0,0]],          'Vector3(0.00, 0.00, 0.00)'),
    ( 'euclidify_recursive',            euclidify,      [[[0,0,0], [1,0,0]]], '[Vector3(0.00, 0.00, 0.00), Vector3(1.00, 0.00, 0.00)]'),
    ( 'euclidify_Vector',               euclidify,      [Vector3(0,0,0)], 'Vector3(0.00, 0.00, 0.00)'),
    ( 'euclidify_recursive_Vector',     euclidify, [[Vector3( 0,0,0), Vector3( 0,0,1)]],  '[Vector3(0.00, 0.00, 0.00), Vector3(0.00, 0.00, 1.00)]'),
    (                                   euc_to_arr,     [Vector3(0,0,0)], '[0, 0, 0]'),
    ( 'euc_to_arr_recursive',           euc_to_arr,     [[Vector3( 0,0,0), Vector3( 0,0,1)]], '[[0, 0, 0], [0, 0, 1]]'),
    ( 'euc_to_arr_arr',                 euc_to_arr,     [[0,0,0]], '[0, 0, 0]'),
    ( 'euc_to_arr_arr_recursive',       euc_to_arr,   [[[0,0,0], [1,0,0]]], '[[0, 0, 0], [1, 0, 0]]'),
    (                                   is_scad,        [cube(2)], 'True'),
    ( 'is_scad_false',                  is_scad,        [2], 'False'),
    ( 'transform_to_point_single_arr',  transform_to_point, [[1,0,0], [2,2,2], [3,3,1]], 'Point3(2.71, 1.29, 2.00)'),
    ( 'transform_to_point_single_pt3',  transform_to_point, [Point3(1,0,0), [2,2,2], [3,3,1]], 'Point3(2.71, 1.29, 2.00)'),
    ( 'transform_to_point_arr_arr',     transform_to_point, [[[1,0,0], [0,1,0], [0,0,1]]  , [2,2,2], [3,3,1]], '[Point3(2.71, 1.29, 2.00), Point3(1.84, 1.84, 2.97), Point3(1.31, 1.31, 1.77)]'),
    ( 'transform_to_point_pt3_arr',     transform_to_point, [[Point3(1,0,0), Point3(0,1,0), Point3(0,0,1)], [2,2,2], [3,3,1]], '[Point3(2.71, 1.29, 2.00), Point3(1.84, 1.84, 2.97), Point3(1.31, 1.31, 1.77)]') ,
    
]


class TestSPUtils( unittest.TestCase):
    # test cases will be dynamically added to this instance
    def test_split_body_horizontal( self):
        body = sphere( 20)
        actual_tuple = split_body_horizontal( body, plane_z=10, dowel_holes=True)
        actual = [scad_render( b) for b in actual_tuple]
        expected = ['\n\ndifference() {\n\tintersection() {\n\t\tsphere(r = 20);\n\t\ttranslate(v = [0, 0, -4990]) {\n\t\t\tcube(center = true, size = 10000);\n\t\t}\n\t}\n\tunion() {\n\t\ttranslate(v = [-9.0000000000, 0, 10]) {\n\t\t\tcylinder(h = 30, r = 4.5000000000, center = true);\n\t\t}\n\t\ttranslate(v = [9.0000000000, 0, 10]) {\n\t\t\tcylinder(h = 30, r = 4.5000000000, center = true);\n\t\t}\n\t}\n}',
                    '\n\ndifference() {\n\tintersection() {\n\t\tsphere(r = 20);\n\t\ttranslate(v = [0, 0, 5010]) {\n\t\t\tcube(center = true, size = 10000);\n\t\t}\n\t}\n\tunion() {\n\t\ttranslate(v = [-9.0000000000, 0, 10]) {\n\t\t\tcylinder(h = 30, r = 4.5000000000, center = true);\n\t\t}\n\t\ttranslate(v = [9.0000000000, 0, 10]) {\n\t\t\tcylinder(h = 30, r = 4.5000000000, center = true);\n\t\t}\n\t}\n}']
        self.assertEqual( expected, actual)

def test_generator_scad( func, args, expected):
    def test_scad(self):
        scad_obj = func( *args)
        actual = scad_render( scad_obj)
        self.assertEqual( expected, actual)
    
    return test_scad

def test_generator_no_scad( func, args, expected):
    def test_no_scad( self):
        actual = str( func( *args))
        self.assertEqual( expected, actual)
    
    return test_no_scad

def read_test_tuple( test_tuple):
    if len( test_tuple) == 3:
        # If test name not supplied, create it programmatically
        func, args, expected = test_tuple
        test_name = 'test_%s'%func.__name__
    elif len( test_tuple) == 4:
        test_name, func, args, expected = test_tuple
        test_name = 'test_%s'%test_name
    else:
        print "test_tuple has %d args :%s"%( len(test_tuple), test_tuple)    
    return test_name, func, args, expected    

def create_tests( ):
    for test_tuple in scad_test_cases:
        test_name, func, args, expected = read_test_tuple( test_tuple)
        test = test_generator_scad( func, args, expected)
        setattr( TestSPUtils, test_name, test)     
        
    for test_tuple in other_test_cases:
        test_name, func, args, expected = read_test_tuple( test_tuple)
        test = test_generator_no_scad( func, args, expected)
        setattr( TestSPUtils, test_name, test)      

if __name__ == '__main__':
    create_tests( )
    unittest.main()
