#! /usr/bin/env python3
import sys

from solid import scad_render_to_file
from solid.objects import cube, cylinder, difference, translate, union
from solid.utils import right

SEGMENTS = 48


def basic_geometry():
    # SolidPython code can look a lot like OpenSCAD code.  It also has
    # some syntactic sugar built in that can make it look more pythonic.
    # Here are two identical pieces of geometry, one left and one right.

    # left_piece uses standard OpenSCAD grammar (note the commas between
    # block elements; OpenSCAD doesn't require this)
    left_piece = union()(
            translate((-15, 0, 0))(
                    cube([10, 5, 3], center=True)
            ),
            translate((-10, 0, 0))(
                    difference()(
                            cylinder(r=5, h=15, center=True),
                            cylinder(r=4, h=16, center=True)
                    )
            )
    )

    # Right piece uses a more Pythonic grammar.  + (plus) is equivalent to union(), 
    # - (minus) is equivalent to difference() and * (star) is equivalent to intersection
    # solid.utils also defines up(), down(), left(), right(), forward(), and back()
    # for common transforms.
    right_piece = right(15)(cube([10, 5, 3], center=True))
    cyl = cylinder(r=5, h=15, center=True) - cylinder(r=4, h=16, center=True)
    right_piece += right(10)(cyl)

    return union()(left_piece, right_piece)


if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else None

    a = basic_geometry()

    # Adding the file_header argument as shown allows you to change
    # the detail of arcs by changing the SEGMENTS variable.  This can
    # be expensive when making lots of small curves, but is otherwise
    # useful.
    file_out = scad_render_to_file(a, out_dir=out_dir, file_header=f'$fn = {SEGMENTS};')
    print(f"{__file__}: SCAD file written to: \n{file_out}")
