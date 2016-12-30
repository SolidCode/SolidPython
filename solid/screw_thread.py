#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import re

from solid import *
from solid.utils import *
from euclid3 import *
# NOTE: The PyEuclid on PyPi doesn't include several elements added to
# the module as of 13 Feb 2013.  Add them here until euclid supports them
# TODO: when euclid updates, remove this cruft. -ETJ 13 Feb 2013
import solid.patch_euclid
solid.patch_euclid.run_patch()


def thread(outline_pts, inner_rad, pitch, length, external=True, segments_per_rot=32, neck_in_degrees=0, neck_out_degrees=0):
    '''Sweeps outline_pts (an array of points describing a closed polygon in XY)
    through a spiral. 

    :param outline_pts: a list of points (NOT an OpenSCAD polygon) that define the cross section of the thread
    :type outline_pts: list
    
    :param inner_rad: radius of cylinder the screw will wrap around
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
    
    NOTE: This functions works by creating and returning one huge polyhedron, with 
    potentially thousands of faces.  An alternate approach would make one single 
    polyhedron,then repeat it over and over in the spiral shape, unioning them 
    all together.  This would create a similar number of SCAD objects and 
    operations, but still require a lot of transforms and unions to be done 
    in the SCAD code rather than in the python, as here.  Also would take some 
    doing to make the neck-in work as well.  Not sure how the two approaches 
    compare in terms of render-time. -ETJ 16 Mar 2011     

    NOTE: if pitch is less than the or equal to the height of each tooth (outline_pts), 
    OpenSCAD will likely crash, since the resulting screw would self-intersect 
    all over the place.  For screws with essentially no space between 
    threads, (i.e., pitch=tooth_height), I use pitch= tooth_height+EPSILON, 
    since pitch=tooth_height will self-intersect for rotations >=1
    '''
    a = union()
    rotations = float(length) / pitch

    total_angle = 360.0 * rotations
    up_step = float(length) / (rotations * segments_per_rot)
    # Add one to total_steps so we have total_steps *segments*
    total_steps = int(ceil(rotations * segments_per_rot)) + 1
    step_angle = total_angle / (total_steps - 1)

    all_points = []
    all_tris = []
    euc_up = Vector3(*UP_VEC)
    poly_sides = len(outline_pts)

    # Figure out how wide the tooth profile is
    min_bb, max_bb = bounding_box(outline_pts)
    outline_w = max_bb[0] - min_bb[0]
    outline_h = max_bb[1] - min_bb[1]

    min_rad = max(0, inner_rad - outline_w - EPSILON)
    max_rad = inner_rad + outline_w + EPSILON

    # outline_pts, since they were created in 2D , are in the XY plane.
    # But spirals move a profile in XZ around the Z-axis.  So swap Y and Z
    # co-ords... and hope users know about this
    # Also add inner_rad to the profile
    euc_points = []
    for p in outline_pts:
        # If p is in [x, y] format, make it [x, y, 0]
        if len(p) == 2:
            p.append(0)
        # [x, y, z] => [ x+inner_rad, z, y]
        external_mult = 1 if external else -1
        # adding inner_rad, swapping Y & Z
        s = Point3(external_mult * p[0], p[2], p[1])
        euc_points.append(s)

    for i in range(total_steps):
        angle = i * step_angle

        elevation = i * up_step
        if angle > total_angle:
            angle = total_angle
            elevation = length

        # Handle the neck-in radius for internal and external threads
        rad = inner_rad
        int_ext_mult = 1 if external else -1
        neck_in_rad = min_rad if external else max_rad

        if angle < neck_in_degrees:
            rad = neck_in_rad + int_ext_mult * angle / neck_in_degrees * outline_w
        elif angle > total_angle - neck_in_degrees:
            rad = neck_in_rad + int_ext_mult * (total_angle - angle) / neck_out_degrees * outline_w

        elev_vec = Vector3(rad, 0, elevation)

        # create new points
        for p in euc_points:
            pt = (p + elev_vec).rotate_around(axis=euc_up, theta=radians(angle))
            all_points.append(pt.as_arr())

        # Add the connectivity information
        if i < total_steps - 1:
            ind = i * poly_sides
            for j in range(ind, ind + poly_sides - 1):
                all_tris.append([j, j + 1,   j + poly_sides])
                all_tris.append([j + 1, j + poly_sides + 1, j + poly_sides])
            all_tris.append([ind, ind + poly_sides - 1 + poly_sides, ind + poly_sides - 1])
            all_tris.append([ind, ind + poly_sides, ind + poly_sides - 1 + poly_sides])

    # End triangle fans for beginning and end
    last_loop = len(all_points) - poly_sides
    for i in range(poly_sides - 2):
        all_tris.append([0,  i + 2, i + 1])
        all_tris.append([last_loop, last_loop + i + 1, last_loop + i + 2])

    # Make the polyhedron
    a = polyhedron(points=all_points, faces=all_tris)

    if external:
        # Intersect with a cylindrical tube to make sure we fit into
        # the correct dimensions
        tube = cylinder(r=inner_rad + outline_w + EPSILON, h=length, segments=segments_per_rot)
        tube -= cylinder(r=inner_rad, h=length, segments=segments_per_rot)
    else:
        # If the threading is internal, intersect with a central cylinder
        # to make sure nothing else remains
        tube = cylinder(r=inner_rad, h=length, segments=segments_per_rot)
    a *= tube
    return render()(a)


def default_thread_section(tooth_height, tooth_depth):
    # An isoceles triangle, tooth_height vertically, tooth_depth wide:
    res = [[0, -tooth_height / 2],
           [tooth_depth, 0],
           [0, tooth_height / 2]
           ]
    return res


def assembly():
    # Scad code here
    a = union()

    rad = 5
    pts = [[0, -1, 0],
           [1,  0, 0],
           [0,  1, 0],
           [-1, 0, 0],
           [-1, -1, 0]]

    a = thread(pts, inner_rad=10, pitch=6, length=2, segments_per_rot=31,
               neck_in_degrees=30, neck_out_degrees=30)

    return a + cylinder(10 + EPSILON, 2)

if __name__ == '__main__':
    a = assembly()
    scad_render_to_file(a)
