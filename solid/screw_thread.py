#! /usr/bin/env python3
import math
from typing import Sequence, Tuple, Union

from euclid3 import Point3, Vector3

from solid import scad_render_to_file
from solid.objects import cylinder, polyhedron, render
from solid.utils import EPSILON, UP_VEC, bounding_box, radians

# NOTE: The PyEuclid on PyPi doesn't include several elements added to
# the module as of 13 Feb 2013.  Add them here until euclid supports them
# TODO: when euclid updates, remove this cruft. -ETJ 13 Feb 2013
from solid import run_euclid_patch
run_euclid_patch()

P2 = Tuple[float, float]
P3 = Tuple[float, float, float]
P23 = Union[P2, P3]
Points = Sequence[P23]

def map_segment(x: float, domain_min:float, domain_max: float, range_min:float, range_max:float) -> float: 
    if domain_min == domain_max or range_min == range_max:
        return range_min
    proportion = (x - domain_min)/(domain_max - domain_min) 
    return (1-proportion) * range_min + proportion * range_max

def thread(outline_pts: Points,
           inner_rad: float,
           pitch: float,
           length: float,
           external: bool = True,
           segments_per_rot: int = 32,
           neck_in_degrees: float = 0,
           neck_out_degrees: float = 0,
           rad_2: float=None,
           inverse_thread_direction:bool=False):
    """
    Sweeps outline_pts (an array of points describing a closed polygon in XY)
    through a spiral.

    :param outline_pts: a list of points (NOT an OpenSCAD polygon) that define the cross section of the thread
    :type outline_pts: list

    :param inner_rad: radius of cylinder the screw will wrap around; at base of screw
    :type inner_rad: number

    :param pitch: height for one revolution; must be <= the height of outline_pts bounding box to avoid self-intersection
    :type pitch: number

    :param length: distance from bottom-most point of screw to topmost
    :type length: number

    :param external: if True, the cross-section is external to a cylinder. If False,the segment is internal to it, and outline_pts will be mirrored right-to-left
    :type external: bool

    :param segments_per_rot: segments per rotation
    :type segments_per_rot: int

    :param neck_in_degrees: degrees through which the outer edge of the screw thread will move from a thickness of zero (inner_rad) to its full thickness
    :type neck_in_degrees: number

    :param neck_out_degrees: degrees through which outer edge of the screw thread will move from full thickness back to zero
    :type neck_out_degrees: number

    :param rad_2: radius of cylinder the screw will wrap around at top of screw. Defaults to inner_rad
    :type rad_2: number    

    NOTE: This functions works by creating and returning one huge polyhedron, with
    potentially thousands of faces.  An alternate approach would make one single
    polyhedron,then repeat it over and over in the spiral shape, unioning them
    all together.  This would create a similar number of SCAD objects and
    operations, but still require a lot of transforms and unions to be done
    in the SCAD code rather than in the python, as here.  Also would take some
    doing to make the neck-in work as well.  Not sure how the two approaches
    compare in terms of render-time. -ETJ 16 Mar 2011

    NOTE: if pitch is less than or equal to the height of each tooth (outline_pts),
    OpenSCAD will likely crash, since the resulting screw would self-intersect
    all over the place.  For screws with essentially no space between
    threads, (i.e., pitch=tooth_height), I use pitch= tooth_height+EPSILON,
    since pitch=tooth_height will self-intersect for rotations >=1
    """
    # FIXME: For small segments_per_rot where length is not a multiple of
    # pitch, the the generated spiral will have irregularities, since we 
    # don't ensure that each level's segments are in line with those above or
    # below. This would require a change in logic to fix. For now, larger values
    # of segments_per_rot and length that divides pitch evenly should avoid this issue
    # -ETJ 02 January 2020

    rad_2 = rad_2 or inner_rad
    rotations = length / pitch

    total_angle = 360 * rotations
    up_step = length / (rotations * segments_per_rot)
    # Add one to total_steps so we have total_steps *segments*
    total_steps = math.ceil(rotations * segments_per_rot) + 1
    step_angle = total_angle / (total_steps - 1)

    all_points = []
    all_tris = []
    euc_up = Vector3(*UP_VEC)
    poly_sides = len(outline_pts)

    # Make Point3s from outline_pts and flip inward for internal threads
    int_ext_angle = 0 if external else math.pi
    outline_pts = [Point3(p[0], p[1], 0).rotate_around(axis=euc_up, theta=int_ext_angle) for p in outline_pts]

    # If this screw is conical, we'll need to rotate tooth profile to 
    # keep it perpendicular to the side of the cone. 
    if inner_rad != rad_2:
        cone_angle = -math.atan((rad_2 - inner_rad)/length) 
        outline_pts = [p.rotate_around(axis=Vector3(*UP_VEC), theta=cone_angle)  for p in outline_pts]

    # outline_pts, since they were created in 2D , are in the XY plane.
    # But spirals move a profile in XZ around the Z-axis.  So swap Y and Z
    # coordinates... and hope users know about this
    euc_points = list([Point3(p[0], 0, p[1]) for p in outline_pts])

    # Figure out how wide the tooth profile is
    min_bb, max_bb = bounding_box(outline_pts)
    outline_w = max_bb[0] - min_bb[0]
    outline_h = max_bb[1] - min_bb[1]

    # Calculate where neck-in and neck-out starts/ends
    neck_out_start = total_angle - neck_out_degrees
    neck_distance = (outline_w + EPSILON) * (1 if external else -1)
    section_rads = [
        # radius at start of thread 
        max(0, inner_rad - neck_distance),
        # end of neck-in
        map_segment(neck_in_degrees, 0, total_angle, inner_rad, rad_2),       
        # start of neck-out
        map_segment(neck_out_start, 0, total_angle, inner_rad, rad_2),
        # end of thread (& neck-out)
        rad_2 - neck_distance
    ]

    for i in range(total_steps):
        angle = i * step_angle

        elevation = i * up_step
        if angle > total_angle:
            angle = total_angle
            elevation = length

        # Handle the neck-in radius for internal and external threads
        if 0 <= angle < neck_in_degrees:
            rad = map_segment(angle, 0, neck_in_degrees, section_rads[0], section_rads[1])
        elif neck_in_degrees <= angle < neck_out_start:
            rad = map_segment( angle, neck_in_degrees, neck_out_start, section_rads[1], section_rads[2])
        elif neck_out_start <= angle <= total_angle:
            rad = map_segment( angle, neck_out_start, total_angle, section_rads[2], section_rads[3])

        elev_vec = Vector3(rad, 0, elevation)

        # create new points
        for p in euc_points:
            theta = radians(angle) * (-1 if inverse_thread_direction else 1)
            pt = (p + elev_vec).rotate_around(axis=euc_up, theta=theta)
            all_points.append(pt.as_arr())

        # Add the connectivity information
        if i < total_steps - 1:
            ind = i * poly_sides
            for j in range(ind, ind + poly_sides - 1):
                all_tris.append([j, j + 1, j + poly_sides])
                all_tris.append([j + 1, j + poly_sides + 1, j + poly_sides])
            all_tris.append([ind, ind + poly_sides - 1 + poly_sides, ind + poly_sides - 1])
            all_tris.append([ind, ind + poly_sides, ind + poly_sides - 1 + poly_sides])

    # End triangle fans for beginning and end
    last_loop = len(all_points) - poly_sides
    for i in range(poly_sides - 2):
        all_tris.append([0, i + 2, i + 1])
        all_tris.append([last_loop, last_loop + i + 1, last_loop + i + 2])

    # Moving in the opposite direction, we need to reverse the order of
    # corners in each face so the OpenSCAD preview renders correctly
    if inverse_thread_direction:
        all_tris = list([reversed(trio) for trio in all_tris])

    # Make the polyhedron; convexity info needed for correct OpenSCAD render
    a = polyhedron(points=all_points, faces=all_tris, convexity=2)

    if external:
        # Intersect with a cylindrical tube to make sure we fit into
        # the correct dimensions
        tube = cylinder(r1=inner_rad + outline_w + EPSILON, r2=rad_2 + outline_w + EPSILON, h=length, segments=segments_per_rot)
        tube -= cylinder(r1=inner_rad, r2=rad_2, h=length, segments=segments_per_rot)
    else:
        # If the threading is internal, intersect with a central cylinder
        # to make sure nothing else remains
        tube = cylinder(r1=inner_rad, r2=rad_2, h=length, segments=segments_per_rot)
    a *= tube 

    return a

def default_thread_section(tooth_height: float, tooth_depth: float):
    """
    An isosceles triangle, tooth_height vertically, tooth_depth wide:
    """
    res = [[0, -tooth_height / 2],
           [tooth_depth, 0],
           [0, tooth_height / 2]
           ]
    return res

def assembly():
    pts = [(0, -1, 0),
           (1, 0, 0),
           (0, 1, 0),
           (-1, 0, 0),
           (-1, -1, 0)]

    a = thread(pts, inner_rad=10, pitch=6, length=2, segments_per_rot=31,
               neck_in_degrees=30, neck_out_degrees=30)

    return a + cylinder(10 + EPSILON, 2)


if __name__ == '__main__':
    a = assembly()
    scad_render_to_file(a)
