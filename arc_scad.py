#! /usr/bin/python2.5
# -*- coding: UTF-8 -*-
import os, sys, re

from pyopenscad import *
from math import *

RIGHT, TOP, LEFT, BOTTOM = range(4)

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

 
 
if __name__ == '__main__':
    res = arc( rad=20, start_degrees=120, end_degrees=30, invert=True)   
    print scad_render(res)
    
    