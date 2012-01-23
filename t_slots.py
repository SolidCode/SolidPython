#! /usr/bin/python
# -*- coding: UTF-8 -*-
import os, sys, re

# Assumes SolidPython is in site-packages or elsewhwere in sys.path
from SolidPython.pyopenscad import *
from SolidPython.sp_utils import *


tab_width = 5
tab_offset = 3.5
tab_curve_rad = .35

def tab_poly( material_thickness = 5.0):
    # TODO: round off corners of tabs
    
    tab_pts = [ [ -tab_width - tab_offset, -EPSILON],
                [ -tab_width - tab_offset, material_thickness],
                [ -tab_offset, material_thickness],
                [ -tab_offset, -EPSILON],
                [ tab_width + tab_offset, -EPSILON],
                [ tab_offset, -EPSILON],                
                [ tab_offset, material_thickness],
                [ tab_width + tab_offset, material_thickness],
              ]
    tab_faces = [[0,1,2,3], [4,5,6,7]]
    tab = polygon( tab_pts, tab_faces)
    
    return tab

def t_slot_holes( poly, point, normal, 
                screw_type='m3', material_thickness=5, kerf=0):
    '''
    Cuts a screw hole and two notches in poly so they'll 
    interface with the features cut by t_slot()
    
    Returns a copy of poly with holes removed
        
    -- material_thickness is the thickness of the material *that will
    be attached** to the t-slot, NOT necessarily the material that poly
    will be cut on.        
    
    TODO: add kerf calculations
    '''
    
    # tab_poly() sits ON the x-axis.  We want it to straddle the x-axis, so
    # move it back (down in Y) by material_thickness/2
    tab_holes = back( material_thickness/2)( tab_poly(material_thickness))
    
    # Only valid for m3 screws now
    screw_dict = screw_dimensions.get( screw_type.lower())
    if screw_dict:
        screw_w = screw_dict['screw_outer_diam']
    else:
        raise ValueError( "Don't have screw dimensions for requested screw size %s"%screw_type)        
            
    # add the screw hole
    tab_holes += circle( screw_w/2) # NOTE: needs any extra space?
    
    return poly - transform_to_point( tab_holes, point, normal, two_d=True)

def t_slot( poly, point=None, normal=None, 
            screw_type='m3', screw_length=12, material_thickness=5, 
            kerf=0 ):
    '''
    Cuts a t-shaped shot in poly and adds two tabs
    on the outside edge of poly.  
    
    Needs to be combined with t_slot_holes() on another
    poly to make a valid t-slot connection
    
    -- material_thickness is the thickness of the material *that will
    be attached** to the t-slot, NOT necessarily the material that poly
    will be cut on.
    
    TODO: include kerf in calculations
    '''
    point = point if point else [0,0]
    normal = normal if normal else [0,1]
    
    gap = .05
    
    tab = tab_poly()
    
    # Only valid for m3 screws now
    screw_dict = screw_dimensions.get( screw_type.lower())
    if screw_dict:
        screw_w = screw_dict['screw_outer_diam']
        screw_w2 = screw_w/2
        nut_hole_x = (screw_dict[ 'nut_inner_diam'] + .2)/2 # NOTE: How are these tolerances?
        nut_hole_h = screw_dict['nut_thickness'] + .5
        slot_depth = material_thickness - screw_length 
        past_nut_overhang = 2
        nut_loc = slot_depth  + past_nut_overhang + nut_hole_h
    else:
        raise ValueError( "Don't have screw dimensions for requested screw size %s"%screw_type)
    
    slot_pts = [ [ screw_w2, EPSILON ],
            [ screw_w2, nut_loc],
            [ nut_hole_x, nut_loc], 
            [ nut_hole_x, nut_loc - nut_hole_h],
            [ screw_w2, nut_loc - nut_hole_h],
            [ screw_w2, slot_depth],    
            ]
    # mirror the slot points on the left
    slot_pts += [[-x, y] for x,y in slot_pts][ -1::-1]
            
    # TODO: round off top corners of slot
    
    # Add circles around t edges to prevent acrylic breakage
    slot = polygon( slot_pts)
    slot = union()(
                slot,
                translate( [nut_hole_x, nut_loc])( circle( tab_curve_rad)),
                translate( [-nut_hole_x, nut_loc])( circle( tab_curve_rad))
            )
    
    tab  = transform_to_point( tab,  point, normal, two_d=True)
    slot = transform_to_point( slot, point, normal, two_d=True)
            
    return poly + tab - slot


def assembly():
    a = union()
    
    return a

if __name__ == '__main__':
    a = assembly()    
    scad_render_to_file( a, file_header='$fn = %s;'%SEGMENTS, include_orig_code=True)
