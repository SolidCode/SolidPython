#! /usr/bin/python
# -*- coding: utf-8 -*-
import os, sys, re

sys.path.append(os.path.join( os.getenv('HOME'), 'Desktop', 'SolidPython'))

from pyopenscad import *
from sp_utils import *

sys.path.append( os.path.join( os.getenv('HOME'), 'Desktop','pyeuclid'))
from euclid import *

ONE_THIRD = 1/3.0

def kochify_3d( a, b, c, 
            ab_weight=0.5, bc_weight=0.5, ca_weight=0.5, 
            pyr_a_weight=ONE_THIRD, pyr_b_weight=ONE_THIRD, pyr_c_weight=ONE_THIRD,
            pyr_height_weight=ONE_THIRD
            ):
    '''
    Point3s a, b, and c must be coplanar and define a face 
    ab_weight, etc define the subdivision of the original face
    pyr_a_weight, etc define where the point of the new pyramid face will go
    pyr_height determines how far from the face the new pyramid's point will be
    '''
    triangles = []
    new_a = a.affine_combination( b, ab_weight)
    new_b = b.affine_combination( c, bc_weight)
    new_c = c.affine_combination( a, ca_weight)
    
    triangles.extend( [[a, new_a, new_c], [b, new_b, new_a], [c, new_c, new_b]])
    
    avg_pt_x = a.x*pyr_a_weight + b.x*pyr_b_weight + c.x*pyr_c_weight
    avg_pt_y = a.y*pyr_a_weight + b.y*pyr_b_weight + c.y*pyr_c_weight
    avg_pt_z = a.z*pyr_a_weight + b.z*pyr_b_weight + c.z*pyr_c_weight
    
    center_pt = Point3( avg_pt_x, avg_pt_y, avg_pt_z)
    
    # The top of the pyramid will be on a normal 
    ab_vec = b - a
    bc_vec = c - b
    ca_vec = a - c
    normal = ab_vec.cross( bc_vec).normalized()
    avg_side_length = (abs(ab_vec) + abs(bc_vec) + abs(ca_vec))/3
    pyr_h = avg_side_length * pyr_height_weight
    pyr_pt = LineSegment3( center_pt, normal, pyr_h).p2
    
    
    triangles.extend([[new_a, pyr_pt, new_c], [new_b, pyr_pt, new_a], [new_c, pyr_pt, new_b]])
    
    return triangles
    

def kochify( seg, height_ratio=0.33, left_loc= 0.33, midpoint_loc=0.5, right_loc= 0.66): 
    a, b = seg.p1, seg.p2
    l = a.affine_combination( b, left_loc)
    c = a.affine_combination( b, midpoint_loc)
    r = a.affine_combination( b, right_loc)
    # The point of the new triangle will be  height_ratio * abs(seg) long, 
    # and run perpendicular to seg, through c.
    perp = seg.v.cross().normalized()
    
    c_height = height_ratio* abs(seg)
    perp_pt = LineSegment2( c, perp, -c_height).p2
    
    # For the moment, assume perp_pt is on the right side of seg.
    # Will confirm this later if needed
    return [ LineSegment2( a, l),
             LineSegment2( l, perp_pt),
             LineSegment2( perp_pt, r),
             LineSegment2( r, b)]

def main_3d():
    gens = 4
    
    # Parameters
    ab_weight = 0.5
    bc_weight = 0.5
    ca_weight = 0.5
    pyr_a_weight = ONE_THIRD
    pyr_b_weight = ONE_THIRD
    pyr_c_weight = ONE_THIRD
    pyr_height_weight = ONE_THIRD
    pyr_height_weight = ONE_THIRD
    # pyr_height_weight = .25 
    
    all_polys = union()
    
    # setup
    ax, ay, az = 100, -100, 100
    bx, by, bz = 100, 100,-100
    cx, cy, cz = -100, 100, 100
    dx, dy, dz = -100, -100, -100
    generations =   [   [[ Point3( ax, ay, az), Point3( bx, by, bz), Point3( cx, cy, cz)],
                         [ Point3( bx, by, bz), Point3( ax, ay, az), Point3( dx, dy, dz)],
                         [ Point3( ax, ay, az), Point3( cx, cy, cz), Point3( dx, dy, dz)],
                         [ Point3( cx, cy, cz), Point3( bx, by, bz), Point3( dx, dy, dz)],
                        ]
                    ]
    
    # Recursively generate snowflake segments
    for g in range(1, gens):
        generations.append([]) 
        for a, b, c in generations[g-1]:
            new_tris = kochify_3d( a, b, c,     
                                   ab_weight, bc_weight, ca_weight,
                                   pyr_a_weight, pyr_b_weight,pyr_c_weight,
                                   pyr_height_weight)
            # new_tris = kochify_3d(  a, b, c)
            generations[g].extend( new_tris)
        
    # Put all generations into SCAD
    orig_length = abs( generations[0][0][1] - generations[0][0][0])
    for g, a_gen in enumerate(generations):
        # Move each generation up in y so it doesn't overlap the others
        h = orig_length *1.5 * g
        
        # Build the points and triangles arrays that SCAD needs
        tris = []
        points = []
        for a,b,c in a_gen:
            points.extend([ [a.x, a.y, a.z], [b.x, b.y, b.z], [c.x, c.y, c.z]])
            t = len(points)
            tris.append([t-3, t-2, t-1])
        
        # Do the SCAD
        edges = [range(len(points))]
        all_polys.add( up( h)(
                polyhedron( points, tris)
            )
        )
    
    scad_render_to_file( all_polys, os.path.join( os.getenv('HOME'), 'Desktop', 'koch_3d.scad'))    

def main():
    # Parameters
    midpoint_weight = 0.5
    height_ratio = 0.25
    left_loc = ONE_THIRD
    midpoint_loc = 0.5
    right_loc = 2*ONE_THIRD
    gens = 5
    
    # Results 
    all_polys = union()
    
    # setup
    ax, ay = 0, 0
    bx, by = 100, 0
    cx, cy = 50, 86.6
    base_seg1 = LineSegment2(  Point2( ax, ay), Point2( cx, cy))
    base_seg2 = LineSegment2(  Point2( cx, cy), Point2( bx, by))
    base_seg3 = LineSegment2(  Point2( bx, by), Point2( ax, ay))
    generations = [[base_seg1, base_seg2, base_seg3]]
    
    
    # Recursively generate snowflake segments
    for g in range(1, gens):
        generations.append([]) 
        for seg in generations[g-1]:
            generations[g].extend( kochify( seg, height_ratio, left_loc, midpoint_loc, right_loc))
            # generations[g].extend( kochify( seg))
    
    # # Put all generations into SCAD
    orig_length = abs( generations[0][0])
    for g, a_gen in enumerate(generations):
        points = [s.p1 for s in a_gen ]
        # points.append( a_gen[-1].p2) # add the last point
        
        rect_offset = 10
                
        # Just use arrays for points so SCAD understands
        points = [[p.x, p.y] for p in points]
        
        # Move each generation up in y so it doesn't overlap the others
        h = orig_length *1.5 * g
                
        # Do the SCAD
        edges = [range(len(points))]
        all_polys.add( forward( h)( polygon(points=points, paths=edges )))
    
    scad_render_to_file( all_polys, os.path.join( os.getenv('HOME'), 'Desktop', 'koch.scad'))

if __name__ == '__main__':
    main_3d()
    main()