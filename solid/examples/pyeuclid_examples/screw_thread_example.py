#! /usr/bin/python
# -*- coding: UTF-8 -*-
from __future__ import division
import os, sys, re

from solid import *
from solid.utils import *
from solid import screw_thread 

SEGMENTS = 48

inner_rad = 40
screw_height=80
def assembly():
    section = screw_thread.default_thread_section( tooth_height=10, tooth_depth=5)  
    s = screw_thread.thread( outline_pts=section, inner_rad = inner_rad, 
                            pitch= screw_height, length=screw_height, segments_per_rot=4)
                            #, neck_in_degrees=90, neck_out_degrees=90)    
                        
    c = cylinder( r=inner_rad, h=screw_height )
    return s #+ c

if __name__ == '__main__':
    a = assembly()    
    scad_render_to_file( a, file_header='$fn = %s;'%SEGMENTS, include_orig_code=True)
