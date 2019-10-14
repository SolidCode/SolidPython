#! /usr/bin/env python3
import sys
from math import cos, sin
from typing import Optional

from solid import scad_render_animated_file
from solid.objects import square, translate
from solid.solidpython import OpenSCADObject


def my_animate(_time: Optional[float] = 0) -> OpenSCADObject:
    # _time will range from 0 to 1, not including 1
    rads = _time * 2 * 3.1416
    rad = 15
    c = translate((rad * cos(rads), rad * sin(rads)))(square(10))

    return c


if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else None

    # To animate in OpenSCAD:
    # - Run this program to generate a SCAD file.
    # - Open the generated SCAD file in OpenSCAD
    # - Choose "View -> Animate"
    # - Enter FPS (frames per second) and Steps in the fields
    #       at the bottom of the OpenSCAD window
    # - FPS & Steps are flexible.  For a start, set both to 20 
    #       play around from there      
    file_out = scad_render_animated_file(my_animate,  # A function that takes a float argument
                                         # called '_time' in [0,1)
                                         # and returns an OpenSCAD object
                                         steps=20,  # Number of steps to create one complete motion
                                         back_and_forth=True,  # If true, runs the complete motion
                                         # forward and then in reverse,
                                         # to avoid discontinuity
                                         out_dir=out_dir,
                                         include_orig_code=True)  # Append SolidPython code
    # to the end of the generated
    # OpenSCAD code.
    print(f"{__file__}: SCAD file written to: \n{file_out}")
