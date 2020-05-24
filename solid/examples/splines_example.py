#! /usr/bin/env python
import os
import sys
from solid import *
from solid.utils import Red, right, forward, back

from solid.splines import catmull_rom_points, catmull_rom_polygon, control_points
from solid.splines import bezier_polygon, bezier_points
from euclid3 import Vector2, Vector3, Point2, Point3

def assembly():
    # Catmull-Rom Splines
    a = basic_catmull_rom()                         # Top row in OpenSCAD output
    a += back(4)(catmull_rom_spline_variants())     # Row 2
    a += back(12)(bottle_shape(width=2, height=6))  # Row 3, the bottle shape

    # # TODO: include examples for 3D surfaces:
    # a += back(16)(catmull_rom_patches())
    # a += back(20)(catmull_rom_prism())
    # a += back(24)(catmull_rom_prism_smooth())

    # Bezier Splines
    a += back(16)(basic_bezier())                   # Row 4
    a += back(20)(bezier_points_variants())         # Row 5
    return a

def basic_catmull_rom():
    points = [
        Point2(0,0),
        Point2(1,1),
        Point2(2,1),
        Point2(2,-1),
    ]
    # In its simplest form, catmull_rom_polygon() will just make a C1-continuous
    # closed shape. Easy.
    shape_easy = catmull_rom_polygon(points)
    # There are some other options as well...
    shape = catmull_rom_polygon(points, subdivisions=20, extrude_height=5, show_controls=True)
    return shape_easy + right(3)(shape)

def catmull_rom_spline_variants():
    points = [
        Point2(0,0),
        Point2(1,1),
        Point2(2,1),
        Point2(2,-1),
    ]
    controls = control_points(points)

    # By default, catmull_rom_points() will return a closed smooth shape
    curve_points_closed = catmull_rom_points(points, close_loop=True)

    # If `close_loop` is False, it will return only points between the start and
    # end control points, and make a best guess about tangents for the first and last segments
    curve_points_open   = catmull_rom_points(points, close_loop=False)
    
    # By specifying start_tangent and end_tangent, you can change a shape 
    # significantly. This is similar to what you might do with Illustrator's Pen Tool.
    # Try changing these vectors to see the effects this has on the rightmost curve in the example
    start_tangent = Vector2(-2, 0)
    end_tangent = Vector2(3, 0)
    tangent_pts = [points[0] + start_tangent, *points, points[-1] + end_tangent]
    tangent_controls = control_points(tangent_pts)
    curve_points_tangents = catmull_rom_points(points, close_loop=False, 
                                start_tangent=start_tangent, end_tangent=end_tangent)

    closed = polygon(curve_points_closed) + controls
    opened = polygon(curve_points_open) + controls
    tangents = polygon(curve_points_tangents) + tangent_controls

    a = closed + right(3)(opened) + right(10)(tangents)

    return a

def catmull_rom_patches():
    # TODO: write this
    pass

def catmull_rom_prism():
    # TODO: write this
    pass

def catmull_rom_prism_smooth():
    # TODO: write this
    pass

def bottle_shape(width: float, height: float, neck_width:float=None, neck_height:float=None):
    if neck_width == None:
        neck_width = width * 0.4
    
    if neck_height == None:
        neck_height = height * 0.2

    w2 = width/2
    nw2 = neck_width/2
    h = height
    nh = neck_height

    corner_rad = 0.5

    # Add extra tangent points near curves to keep cubics from going crazy. 
    # Try taking some of these out and see how this affects the final shape
    points = [
        Point2(nw2, h),
        Point2(nw2, h-nh + 1),      # <- extra tangent
        Point2(nw2, h - nh),    
        Point2(w2, h-nh-h/6),       # <- extra tangent
        Point2(w2, corner_rad + 1), # <- extra tangent
        Point2(w2, corner_rad),
        Point2(w2-corner_rad, 0),
        Point2(0,0),
    ]
    # Use catmull_rom_points() when you don't want all corners in a polygon 
    # smoothed out or want to combine the curve with other shapes. 
    # Extra points can then be added to the list you get back
    cr_points = catmull_rom_points(points)

    # Insert a point at the top center of the bottle at the beginning of the 
    # points list. This is how the bottle has a sharp right angle corner at the 
    # sides of the neck; otherwise we'd have to insert several extra control 
    # points to make a sharp corner
    cr_points.insert(0, (0,h))
    
    # Make OpenSCAD polygons out of the shapes once all points are calculated
    a = polygon(cr_points) 
    a += mirror(v=(1,0))(a)

    # Show control points. These aren't required for anything, but seeing them
    # makes refining a curve much easier
    controls = control_points(points)
    a += controls
    return a

def basic_bezier():
    # A basic cubic Bezier curve will pass through its first and last 
    # points, but not through the central control points
    controls = [
        Point2(0, 3),
        Point2(1, 1),
        Point2(2, 1),
        Point2(3, 3)
    ]
    shape = bezier_polygon(controls, show_controls=True)
    return shape

def bezier_points_variants():
    controls = [
        Point2(0,0),
        Point2(1,2),
        Point2(2, -1),
        Point2(3,0),
    ]
    points = bezier_points(controls, subdivisions=20)
    # For non-smooth curves, add extra points
    points += [
        Point2(2, -2),
        Point2(1, -2)
    ]
    shape = polygon(points) + control_points(controls, extrude_height=0)
    return shape


if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.curdir

    a = assembly()

    out_path = scad_render_to_file(a, out_dir=out_dir, include_orig_code=True)
    print(f"{__file__}: SCAD file written to: \n{out_path}")

