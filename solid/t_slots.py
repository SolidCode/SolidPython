#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
import os
import sys
import re

# Assumes SolidPython is in site-packages or elsewhwere in sys.path
from solid import *
from solid.utils import *

SEGMENTS = 24

# FIXME: ought to be 5
DFM = 5  # Default Material thickness

tab_width = 5
tab_offset = 4
tab_curve_rad = .35

# TODO: Slots & tabs make it kind of difficult to align pieces, since we
# always need the slot piece to overlap the tab piece by a certain amount.
# It might be easier to have the edges NOT overlap at all and then have tabs
# for the slots added programmatically.  -ETJ 06 Mar 2013


def t_slot_holes(poly, point=None, edge_vec=RIGHT_VEC, screw_vec=DOWN_VEC, screw_type='m3', screw_length=16, material_thickness=DFM, kerf=0):
    '''
    Cuts a screw hole and two notches in poly so they'll 
    interface with the features cut by t_slot()

    Returns a copy of poly with holes removed

    -- material_thickness is the thickness of the material *that will
    be attached** to the t-slot, NOT necessarily the material that poly
    will be cut on.  

    -- screw_vec is the direction the screw through poly will face; normal to poly      
    -- edge_vec orients the holes to the edge they run parallel to

    TODO: add kerf calculations
    '''
    point = point if point else ORIGIN
    point = euclidify(point, Point3)
    screw_vec = euclidify(screw_vec, Vector3)
    edge_vec = euclidify(edge_vec, Vector3)

    src_up = screw_vec.cross(edge_vec)

    a_hole = square([tab_width, material_thickness], center=True)
    move_hole = tab_offset + tab_width / 2
    tab_holes = left(move_hole)(a_hole) + right(move_hole)(a_hole)

    # Only valid for m3-m5 screws now
    screw_dict = screw_dimensions.get(screw_type.lower())
    if screw_dict:
        screw_w = screw_dict['screw_outer_diam']
    else:
        raise ValueError(
            "Don't have screw dimensions for requested screw size %s" % screw_type)

    # add the screw hole
    tab_holes += circle(screw_w / 2)  # NOTE: needs any extra space?

    tab_holes = transform_to_point(
        tab_holes,  point, dest_normal=screw_vec, src_normal=UP_VEC, src_up=src_up)

    return poly - tab_holes


def t_slot(poly, point=None, screw_vec=DOWN_VEC, face_normal=UP_VEC, screw_type='m3', screw_length=16, material_thickness=DFM, kerf=0):
    '''
    Cuts a t-shaped shot in poly and adds two tabs
    on the outside edge of poly.  

    Needs to be combined with t_slot_holes() on another
    poly to make a valid t-slot connection

    -- material_thickness is the thickness of the material *that will
    be attached** to the t-slot, NOT necessarily the material that poly
    will be cut on.

    -- This method will align the t-slots where you tell them to go, 
    using point, screw_vec (the direction the screw will be inserted), and
    face_normal, a vector normal to the face being altered.  To avoid confusion,
    it's often easiest to work on the XY plane. 


    TODO: include kerf in calculations
    '''
    point = point if point else ORIGIN
    point = euclidify(point, Point3)
    screw_vec = euclidify(screw_vec, Vector3)
    face_normal = euclidify(face_normal, Vector3)

    tab = tab_poly(material_thickness=material_thickness)
    slot = nut_trap_slot(
        screw_type, screw_length, material_thickness=material_thickness)

    # NOTE: dest_normal & src_normal are the same.  This should matter, right?
    tab = transform_to_point(
        tab,  point, dest_normal=face_normal, src_normal=face_normal, src_up=-screw_vec)
    slot = transform_to_point(
        slot, point, dest_normal=face_normal, src_normal=face_normal, src_up=-screw_vec)

    return poly + tab - slot


def tab_poly(material_thickness=DFM):

    r = [[tab_width + tab_offset,   -EPSILON],
         [tab_offset,               -EPSILON],
         [tab_offset,               material_thickness],
         [tab_width + tab_offset,   material_thickness], ]

    l = [[-rp[0], rp[1]] for rp in r]
    tab_pts = l + r

    tab_faces = [[0, 1, 2, 3], [4, 5, 6, 7]]
    tab = polygon(tab_pts, tab_faces)

    # Round off the top points so tabs slide in more easily
    round_tabs = False
    if round_tabs:
        points_to_round = [[r[1], r[2], r[3]],
                           [r[2], r[3], r[0]],
                           [l[1], l[2], l[3]],
                           [l[2], l[3], l[0]],
                           ]
        tab = fillet_2d(three_point_sets=points_to_round, orig_poly=tab,
                        fillet_rad=1, remove_material=True)

    return tab


def nut_trap_slot(screw_type='m3', screw_length=16, material_thickness=DFM):
    # This shape has a couple uses.
    # 1) Right angle joint between two pieces of material.
    # A bolt goes through the second piece and into the first.

    # 2) Set-screw for attaching to motor spindles.
    # Bolt goes full length into a sheet of material.  Set material_thickness
    # to something small (1-2 mm) to make sure there's adequate room to
    # tighten onto the shaft

    # Only valid for m3-m5 screws now
    screw_dict = screw_dimensions.get(screw_type.lower())
    if screw_dict:
        screw_w = screw_dict['screw_outer_diam']
        screw_w2 = screw_w / 2
        # NOTE: How are these tolerances?
        nut_hole_x = (screw_dict['nut_inner_diam'] + 0.2) / 2
        nut_hole_h = screw_dict['nut_thickness'] + 0.5
        slot_depth = material_thickness - screw_length - 0.5
        # If a nut isn't far enough into the material, the sections
        # that hold the nut in may break off.  Make sure it's at least
        # half a centimeter.  More would be better, actually
        nut_loc = -5
    else:
        raise ValueError(
            "Don't have screw dimensions for requested screw size %s" % screw_type)

    slot_pts = [[screw_w2, EPSILON],
                [screw_w2, nut_loc],
                [nut_hole_x, nut_loc],
                [nut_hole_x, nut_loc - nut_hole_h],
                [screw_w2, nut_loc - nut_hole_h],
                [screw_w2, slot_depth],
                ]
    # mirror the slot points on the left
    slot_pts += [[-x, y] for x, y in slot_pts][-1::-1]

    # TODO: round off top corners of slot

    # Add circles around t edges to prevent acrylic breakage
    slot = polygon(slot_pts)
    slot = union()(
        slot,
        translate([nut_hole_x, nut_loc])(circle(tab_curve_rad)),
        translate([-nut_hole_x, nut_loc])(circle(tab_curve_rad))
    )
    return render()(slot)


def assembly():
    a = union()

    return a

if __name__ == '__main__':
    a = assembly()
    scad_render_to_file(a, file_header='$fn = %s;' %
                        SEGMENTS, include_orig_code=True)
