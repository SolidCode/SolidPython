#! /usr/bin/env python3

from solid import cylinder, rotate, translate, scad_render_to_file
from solid.customizer import CustomizerSlider
SEGMENTS = 48


def custom_cube():
    side_length = CustomizerSlider('sideLength', 1, min_val=1, max_val=10, step=1)
    offset= CustomizerSlider('offset', 2, 0, 10, 2)
    angle = CustomizerSlider('angle', 0, 0, 90) # Note no step value; OpenSCAD supplies

    # Once you've defined your Customizer objects, use them naturally like you 
    # would Python variables. SolidPython will put the correct OpenSCAD code at 
    # the beginning of the file so that the GUI is defined.
    a = rotate([0, 0, angle])(
        translate([offset, offset, 0])(
            cylinder(r1=2*side_length, r2=side_length, h=3*side_length)
        )
    )

    return a

# FIXME: include examples of ways we *can't* use Customizer objects just like 
# Python variables. Basically, you can use a Customizer as an argument to an OpenSCAD
# function, but if you're doing pure Python things, OpenSCAD won't pick up on the
# use of a Customizer variable. 
# E.g. ```
# slider_val = CustomizedSlider('slider_val', val=4, min_val=2, max_val=10)
# objs = [some_obj(i) for i in range(slider_val)]
# ```
# This will always return 4 objects, since the list comprehension is pure Python
# and won't be passed on to OpenSCAD.

if __name__ == '__main__':
    a = custom_cube()
    out_path = scad_render_to_file(a, file_header='$fn = %s;' % SEGMENTS, include_orig_code=True)
    print(f'Wrote file to {out_path}')