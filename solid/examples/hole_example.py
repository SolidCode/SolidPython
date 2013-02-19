#! /usr/bin/python
# -*- coding: UTF-8 -*-
from __future__ import division
import os, sys, re

# Assumes SolidPython is in site-packages or elsewhwere in sys.path
from solid import *
from solid.utils import *

SEGMENTS = 120

def pipe_intersection_hole():
    pipe_od = 12
    pipe_id = 10
    seg_length = 30    
    
    outer = cylinder( r=pipe_od, h=seg_length, center=True)
    inner = cylinder(r=pipe_id, h=seg_length+2, center=True)
    
    # By declaring that the internal void of pipe_a should
    # explicitly remain empty, the combination of both pipes
    # is empty all the way through.
    
    # Any OpenSCAD / SolidPython object can be declared a hole(), 
    # and after that will always be empty
    pipe_a = outer + hole()(inner)
    # Note that "pipe_a = outer - hole()( inner)" would work identically;
    # inner will always be subtracted now that it's a hole
    
    pipe_b =  rotate( a=90, v=FORWARD_VEC)( pipe_a)
    return pipe_a + pipe_b

def pipe_intersection_no_hole():
    pipe_od = 12
    pipe_id = 10
    seg_length = 30    
    
    outer = cylinder( r=pipe_od, h=seg_length, center=True)
    inner = cylinder(r=pipe_id, h=seg_length+2, center=True)
    pipe_a = outer - inner
    
    pipe_b =  rotate( a=90, v=FORWARD_VEC)( pipe_a)
    # pipe_a and pipe_b are both hollow, but because
    # their central voids aren't explicitly holes,
    # the union of both pipes has unwanted internal walls
    
    return pipe_a + pipe_b

if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.curdir
    file_out = os.path.join( out_dir, 'hole_example.scad')
    
    a = pipe_intersection_no_hole() + right( 45)(pipe_intersection_hole())
    
    print "%(__file__)s: SCAD file written to: \n%(file_out)s \n"%vars()
    scad_render_to_file( a, file_out, file_header='$fn = %s;'%SEGMENTS, include_orig_code=True)

