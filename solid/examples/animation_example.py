#! /usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import division
import os
import sys
import re

from solid import *
from solid.utils import *


def my_animate(_time=0):
    # _time will range from 0 to 1, not including 1
    rads = _time * 2 * 3.1416
    rad = 15
    c = translate([rad * cos(rads), rad * sin(rads)])(square(10))

    return c

if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.curdir
    file_out = os.path.join(out_dir, 'animation_example.scad')

    print("%(__file__)s: SCAD file written to: \n%(file_out)s" % vars())

    # To animate in OpenSCAD:
    # - Run this program to generate a SCAD file.
    # - Open the generated SCAD file in OpenSCAD
    # - Choose "View -> Animate"
    # - Enter FPS (frames per second) and Steps in the fields
    #       at the bottom of the OpenSCAD window
    # - FPS & Steps are flexible.  For a start, set both to 20 
    #       play around from there      
    scad_render_animated_file(my_animate, # A function that takes a float argument
                                           # called '_time' in [0,1)
                                           # and returns an OpenSCAD object
                               steps=20,   # Number of steps to create one complete motion
                               back_and_forth=True, # If true, runs the complete motion
                                                    # forward and then in reverse,
                                                    # to avoid discontinuity
                               filepath=file_out,   # Output file 
                               include_orig_code=True ) # Append SolidPython code
                                                         # to the end of the generated
                                                         # OpenSCAD code.

    