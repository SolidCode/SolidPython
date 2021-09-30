#! /usr/bin/env python3
from solid.objects import linear_extrude
from solid.solidpython import OpenSCADObject
import sys
from math import cos, radians, sin, pi, tau
from pathlib import Path

from euclid3 import Point2, Point3, Vector3

from solid import scad_render_to_file, text, translate, cube, color, rotate
from solid.utils import UP_VEC, Vector23, distribute_in_grid, extrude_along_path
from solid.utils import down, right, frange, lerp


from typing import Set, Sequence, List, Callable, Optional, Union, Iterable, Tuple

SEGMENTS = 48
PATH_RAD = 50 
SHAPE_RAD = 15

TEXT_LOC = [-0.6 *PATH_RAD, 1.6 * PATH_RAD]

def basic_extrude_example():
    path_rad = PATH_RAD
    shape = star(num_points=5)
    path = sinusoidal_ring(rad=path_rad, segments=240)

    # At its simplest, just sweep a shape along a path
    extruded = extrude_along_path( shape_pts=shape, path_pts=path)
    extruded += make_label('Basic Extrude')
    return extruded
        
def extrude_example_xy_scaling() -> OpenSCADObject:
    num_points = SEGMENTS
    path_rad = PATH_RAD
    circle = circle_points(15)
    path = circle_points(rad = path_rad)

    # If scales aren't included, they'll default to
    # no scaling at each step along path.
    no_scale_obj = make_label('No Scale')
    no_scale_obj += extrude_along_path(circle, path)

    # angles: from 0 to 6*Pi
    angles = list((frange(0, 3*tau, num_steps=len(path))))

    # With a 1-D scale factor, an extrusion grows and shrinks uniformly
    x_scales = [(1 + cos(a)/2) for a in angles]
    x_obj = make_label('1D Scale')
    x_obj += extrude_along_path(circle, path, scales=x_scales)

    # With a 2D scale factor, a shape's X & Y dimensions can scale 
    # independently, leading to more interesting shapes
    # X & Y scales vary between 0.5 & 1.5
    xy_scales = [Point2( 1 + cos(a)/2, 1 + sin(a)/2) for a in angles]
    xy_obj = make_label('2D Scale')
    xy_obj += extrude_along_path(circle, path, scales=xy_scales)

    obj = no_scale_obj + right(3*path_rad)(x_obj) + right(6 * path_rad)(xy_obj)
    return obj

def extrude_example_capped_ends() -> OpenSCADObject:
    num_points = SEGMENTS/2
    path_rad = 50
    circle = star(6)
    path = circle_points(rad = path_rad)[:-4]

    # If `connect_ends` is False or unspecified, ends will be capped.
    # Endcaps will be correct for most convex or mildly concave (e.g. stars) cross sections
    capped_obj = make_label('Capped Ends')
    capped_obj += extrude_along_path(circle, path, connect_ends=False, cap_ends=True)

    # If `connect_ends` is specified, create a continuous manifold object
    connected_obj = make_label('Connected Ends')
    connected_obj += extrude_along_path(circle, path, connect_ends=True)   

    return capped_obj + right(3*path_rad)(connected_obj)

def extrude_example_rotations() -> OpenSCADObject:
    path_rad = PATH_RAD
    shape = star(num_points=5)
    path = circle_points(path_rad, num_points=240)

    # For a simple example, make one complete revolution by the end of the extrusion
    simple_rot = make_label('Simple Rotation')
    simple_rot += extrude_along_path(shape, path, rotations=[360], connect_ends=True)

    # For a more complex set of rotations, add a rotation degree for each point in path
    complex_rotations = []
    degs = 0
    oscillation_max = 60

    for i in frange(0, 1, num_steps=len(path)):
        # For the first third of the path, do one complete rotation
        if i <= 0.333:
            degs = i/0.333*360
        # For the second third of the path, oscillate between +/- oscillation_max degrees 
        elif i <= 0.666:
            angle = lerp(i, 0.333, 0.666, 0, 2*tau)
            degs = oscillation_max * sin(angle)
        # For the last third of the path, oscillate increasingly fast but with smaller magnitude 
        else:
            # angle increases in a nonlinear curve, so
            # oscillations should get quicker and quicker
            x = lerp(i, 0.666, 1.0, 0, 2)
            angle = pow(x, 2.2) * tau
            # decrease the size of the oscillations by a factor of 10
            # over the course of this stretch
            osc = lerp(i, 0.666, 1.0, oscillation_max, oscillation_max/10)
            degs = osc * sin(angle)
        complex_rotations.append(degs)

    complex_rot = make_label('Complex Rotation')
    complex_rot += extrude_along_path(shape, path, rotations=complex_rotations)

    # Make some red markers to show the boundaries between the three sections of this path
    marker_w = SHAPE_RAD * 1.5
    marker = translate([path_rad, 0, 0])(
        cube([marker_w, 1, marker_w], center=True)
    )
    markers = [color('red')(rotate([0,0,120*i])(marker)) for i in range(3)]
    complex_rot += markers

    return simple_rot + right(3*path_rad)(complex_rot)

def extrude_example_transforms() -> OpenSCADObject:
    path_rad = PATH_RAD
    height = 2*SHAPE_RAD
    num_steps = 120

    shape = circle_points(rad=path_rad, num_points=120)
    path = [Point3(0,0,i) for i in frange(0, height, num_steps=num_steps)]

    max_rotation = radians(15)
    max_z_displacement = height/10
    up = Vector3(0,0,1)

    # The transforms argument is powerful. 
    # Each point in the entire extrusion will call this function with unique arguments: 
    #   -- `path_norm` in [0, 1] specifying how far along in the extrusion a point's loop is
    #   -- `loop_norm` in [0, 1] specifying where in its loop a point is.
    def point_trans(point: Point3, path_norm:float, loop_norm: float) -> Point3:
        # scale the point from 1x to 2x in the course of the 
        # extrusion, 
        scale = 1 + path_norm*path_norm/2
        p = scale * point

        # Rotate the points sinusoidally up to max_rotation
        p = p.rotate_around(up, max_rotation*sin(tau*path_norm))

        # Oscillate z values sinusoidally, growing from 
        # 0 magnitude to max_z_displacement, then decreasing to 0 magnitude at path_norm == 1
        max_z = sin(pi*path_norm) * max_z_displacement
        angle = lerp(loop_norm, 0, 1, 0, 10*tau)
        p.z += max_z*sin(angle)
        return p

    no_trans = make_label('No Transform')
    no_trans += down(height/2)(
        extrude_along_path(shape, path, cap_ends=True)
    )

    # We can pass transforms a single function that will be called on all points,
    # or pass a list with a transform function for each point along path
    arb_trans = make_label('Arbitrary Transform')
    arb_trans += down(height/2)(
        extrude_along_path(shape, path, transforms=[point_trans], cap_ends=True)
    )

    return no_trans + right(3*path_rad)(arb_trans)

# ============
# = GEOMETRY =
# ============
def sinusoidal_ring(rad=25, segments=SEGMENTS) -> List[Point3]:
    outline = []
    for i in range(segments):
        angle = radians(i * 360 / segments)
        scaled_rad = (1 + 0.18*cos(angle*5)) * rad
        x = scaled_rad * cos(angle)
        y = scaled_rad * sin(angle)
        z = 0
        # Or stir it up and add an oscillation in z as well
        # z = 3 * sin(angle * 6)
        outline.append(Point3(x, y, z))
    return outline

def star(num_points=5, outer_rad=SHAPE_RAD, dip_factor=0.5) -> List[Point3]:
    star_pts = []
    for i in range(2 * num_points):
        rad = outer_rad - i % 2 * dip_factor * outer_rad
        angle = radians(360 / (2 * num_points) * i)
        star_pts.append(Point3(rad * cos(angle), rad * sin(angle), 0))
    return star_pts

def circle_points(rad: float = SHAPE_RAD, num_points: int = SEGMENTS) -> List[Point2]:
    angles = frange(0, tau, num_steps=num_points, include_end=True)
    points = list([Point2(rad*cos(a), rad*sin(a)) for a in angles])
    return points

def make_label(message:str, text_loc:Tuple[float, float]=TEXT_LOC, height=5) -> OpenSCADObject:
    return translate(text_loc)(
        linear_extrude(height)(
            text(message)
        )
    )

# ===============
# = ENTRY POINT =
# ===============
if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent

    basic_extrude = basic_extrude_example()
    scaled_extrusions = extrude_example_xy_scaling()
    capped_extrusions = extrude_example_capped_ends()
    rotated_extrusions = extrude_example_rotations()
    arbitrary_transforms = extrude_example_transforms()
    all_objs = [basic_extrude, scaled_extrusions, capped_extrusions, rotated_extrusions, arbitrary_transforms]

    a = distribute_in_grid(all_objs, 
                            max_bounding_box=[4*PATH_RAD, 4*PATH_RAD],
                            rows_and_cols=[len(all_objs), 1])

    file_out = scad_render_to_file(a,  out_dir=out_dir, include_orig_code=True)
    print(f"{__file__}: SCAD file written to: \n{file_out}")
