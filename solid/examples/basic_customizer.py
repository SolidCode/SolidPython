#! /usr/bin/env python3

from solid import (cylinder, rotate, translate, scad_render_to_file, union, cube, text)
from solid.customizer import (CustomizerCheckbox, CustomizerDropdownString, CustomizerSlider,
    CustomizerDropdownNumber, CustomizerSpinbox, CustomizerTextbox)
SEGMENTS = 48

def ported_scad_example():
    elts = []

    # // combo box for number
    # SCAD: a_numbers_dropdown = 4; // [2, 4, 12, 14]
    a_numbers_dropdown = CustomizerDropdownNumber('a_numbers_dropdown', 4, [2, 4, 12, 14])
    elts.append (cube(a_numbers_dropdown))

    # // combo box for string
    # SCAD: b_strings_dropdown = "foo"; // [foo, bar, baz]    
    b_strings_dropdown = CustomizerDropdownString('b_strings_dropdown', 'foo', ['foo', 'bar', 'baz']  )
    elts.append( text(b_strings_dropdown))

    # // labeled combo box for string
    # Strings = "M"; // []

    # // slider widget for number
    # SCAD: slider =34; // [10:100]
    c_slider = CustomizerSlider('c_slider', 3, 1, 10)
    elts.append( cube(c_slider))

    # //step slider for number
    # SCAD: stepSlider=2; //[0:5:100]
    d_step_slider = CustomizerSlider('d_step_slider', 2, 0, 100, 5)
    elts.append( cube(d_step_slider))

    # Checkbox
    # SCAD: e_checkbox = true;
    e_checkbox = CustomizerCheckbox('e_checkbox', True)
    elts.append( cube(size=5, center=e_checkbox))

    # Spinbox with step size 1
    # SCAD: f_spinbox = 5;
    f_spinbox = CustomizerSpinbox('f_spinbox', 5)
    elts.append( cube(f_spinbox))

    # // spinbox with step size 0.01
    # SCAD: g_float_spinbox = 5.1;
    g_float_spinbox = CustomizerSpinbox('g_float_spinbox', 5.1)
    elts.append( cube(g_float_spinbox))

    # Textbox:
    # // Text box for string
    # SCAD: h_textbox = "hello";    
    h_textbox = CustomizerTextbox('h_textbox', 'hello')
    elts.append( text(h_textbox))

    # TODO: compound Spinboxes for 1-4 numbers, & textbox for 5+ numbers

    # Move everything down in a line from y=0 so we can see the different objects
    elts = [translate([0,-10*i,0])(e) for i,e in enumerate(elts)]

    # And return everything; Customizer instances that aren't used in OpenSCAD
    # objects and rendered won't appear in the final SCAD file
    a = union()( elts )
    return a

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
    a = ported_scad_example()
    out_path = scad_render_to_file(a, file_header='$fn = %s;' % SEGMENTS, include_orig_code=True)
    print(f'Wrote file to {out_path}')