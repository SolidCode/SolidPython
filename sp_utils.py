#! /usr/bin/python2.5
# -*- coding: UTF-8 -*-
import os, sys, re

from pyopenscad import *
from math import *

RIGHT, TOP, LEFT, BOTTOM = range(4)
EPSILON = 0.01

# ==========
# = Colors =
# ==========
Oak = [0.65, 0.5, 0.4];
Pine = [0.85, 0.7, 0.45];
Birch = [0.9, 0.8, 0.6];
FiberBoard = [0.7, 0.67, 0.6];
BlackPaint = [0.2, 0.2, 0.2];
Iron = [0.36, 0.33, 0.33];
Steel = [0.65, 0.67, 0.72];
Stainless = [0.45, 0.43, 0.5];
Aluminum = [0.77, 0.77, 0.8];
Brass = [0.88, 0.78, 0.5];
Transparent = [1, 1, 1, 0.2];

# ==============
# = Grid Plane =
# ==============
def grid_plane( grid_unit=12, count=10, line_weight=0.1, plane='xz'):
    
    # Draws a grid of thin lines in the XZ plane.  Helpful for 
    # reference during debugging.  
    l = count*grid_unit
    t = union()
    t.set_modifier('background')
    for i in range(-count/2, count/2+1):
        if 'xz' in plane:
            # xz-plane
            h = up(   i*grid_unit)( cube( [ l, line_weight, line_weight], center=True))
            v = right(i*grid_unit)( cube( [ line_weight, line_weight, l], center=True))
            t.add([h,v])
        
        # xy plane
        if 'xy' in plane:
            h = forward(i*grid_unit)( cube([ l, line_weight, line_weight], center=True))
            v = right(  i*grid_unit)( cube( [ line_weight, l, line_weight], center=True))
            t.add([h,v])
            
        # yz plane
        if 'yz' in plane:
            h = up(      i*grid_unit)( cube([ line_weight, l, line_weight], center=True))
            v = forward( i*grid_unit)( cube([ line_weight, line_weight, l], center=True))
            
            t.add([h,v])
            
    return t
    

# ==============
# = Directions =
# ==============
def up( z):
    return translate( [0,0,z])

def down( z):
    return translate( [0,0,-z])

def right( x):
    return translate( [x, 0,0])

def left( x):
    return translate( [-x, 0,0])

def forward(y):
    return translate( [0,y,0])

def back( y):
    return translate( [0,-y,0])


# =======
# = Arc =
# =======
def arc( rad, start_degrees, end_degrees, invert=False):
    # Draws a portion of a circle specified by start_degrees & end_degrees.
    # invert=True specifies will draw portions of that arc that lie in a 
    # square of sidelength 2*rad, but not in the circle itself.  This is
    # useful for creating fillets
    
    start_degrees %= 360
    end_degrees %= 360
    if start_degrees > end_degrees:
        start_degrees, end_degrees = end_degrees, start_degrees
    
    start_point = [rad* cos( radians( start_degrees)), rad*sin( radians( start_degrees))] 
    end_point   = [rad* cos( radians( end_degrees)),   rad*sin( radians( end_degrees))] 
        
    points = [[0,0], start_point]
    
    # second point is on the square, but in line (vertically or horizontally) with start_point
    # penultimate_point is the same w.r.t to end_point
    if start_degrees not in [0, 90, 180, 270]: 
        points.append( side_point_for_degrees( start_degrees, rad))
    
        
    # From start_point, work counterclockwise to end_point, with all intermediate 
    # points on the circumscribed square
    for side in range( which_side(start_degrees), which_side(end_degrees)):
        points.append( next_corner_for_side( side, rad))
        
    
    if end_degrees not in [0, 90, 180, 270]: 
        points.append( side_point_for_degrees( end_degrees, rad))
    points.append( end_point)
    paths = [range(len(points))]
    
    square_poly = polygon( points, paths)
    whole_circle = circle( rad)
        
    if invert:
        top = difference()
        top.add( square_poly)
        top.add( whole_circle)
    else:
        top = intersection()
        top.add( whole_circle)
        top.add( square_poly)
    
    return top

# =========================
# = Arc Helpers... ignore =
# =========================
def next_corner_for_side( side, rad):
    corners = { RIGHT:  [rad, rad],
                TOP:    [-rad, rad],
                LEFT:   [-rad, -rad],
                BOTTOM: [rad, -rad]
         }
    return corners[side]

def side_point_for_degrees( degrees, rad):
    # returns a line on a circle's circumscribed square
    # that is horizontally or vertically aligned with the
    # point at degrees on the circle
    x = rad * cos( radians( degrees))
    y = rad * sin( radians( degrees))
    
    side = which_side(degrees)
    points = {  RIGHT:  [rad, y],
                TOP:    [x, rad],
                LEFT:   [-rad, y],
                BOTTOM: [x, -rad],
            }
    
    return points[side]

def which_side( degrees):
    # sides:  0: right, 1: top, 2:left, 3:bottom
    if degrees > 315 or degrees <=45:   return RIGHT
    if degrees > 45 and degrees <=135:  return TOP
    if degrees > 135 and degrees <=225: return LEFT
    else:                               return BOTTOM

 
# =====================
# = Bill of Materials =
# =====================
g_parts_dict = {}
def part( description='', per_unit_price=None):
    def wrap(f):
        name = description if description else f.__name__
        g_parts_dict[name] = [0, per_unit_price]
        def wrapped_f( *args):
            name = description if description else f.__name__
            g_parts_dict[name][0] += 1
            return f(*args)
        
        return wrapped_f
    
    return wrap

def print_BOM():
    print "%8s\t%8s\t%8s\t%8s"%("Desc.", "Count", "Unit Price", "Total Price")
    all_costs = 0
    for desc,(count, price) in g_parts_dict.items():
        if count > 0:
            if price:
                total = price*count
                all_costs += total
                print "%8s\t%8d\t%8f\t%8.2f"%(desc, count, price, total)
            else:
                print "%8s\t%8d"%(desc, count)
    if all_costs > 0:
        print "_"*60
        print "Total Cost: %.2f"%all_costs

 
if __name__ == '__main__':
    res = arc( rad=20, start_degrees=120, end_degrees=30, invert=True)   
    print scad_render(res)
    
    