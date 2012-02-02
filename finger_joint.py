#! /usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
import os, sys, re

# Assumes SolidPython is in site-packages or elsewhwere in sys.path
from SolidPython.pyopenscad import *
from SolidPython.sp_utils import *

SEGMENTS = 48

def finger_joint( poly, p_a, p_b, poly_sheet_thick, other_sheet_thick, joint_width=None, kerf=0.1):
    if not joint_width: joint_width = poly_sheet_thick
    
    # Should get this passed in from poly, really
    edge_length = 50
    
    k2 = kerf/2
    points = [  [ 0,-k2],  
                [joint_width + k2, -k2],
                [joint_width + k2, other_sheet_thick - k2],
                [2*(joint_width + k2), other_sheet_thick -k2],
                [2*(joint_width + k2), -k2],
            ]
    

def assembly():
    
    a = finger_joint( p, poly_sheet_thick=4.75, other_sheet_thick=4.75, joint_width=None, kerf=0.1)
    
    return a

if __name__ == '__main__':
    a = assembly()    
    scad_render_to_file( a, file_header='$fn = %s;'%SEGMENTS, include_orig_code=True)
