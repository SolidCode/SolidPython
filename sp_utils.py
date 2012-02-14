#! /usr/bin/python2.5
# -*- coding: utf-8 -*-
import os, sys, re

from pyopenscad import *
from math import *

RIGHT, TOP, LEFT, BOTTOM = range(4)
EPSILON = 0.01
TAU = 2*pi

UP_VEC      = [ 0, 0, 1]
RIGHT_VEC   = [ 1, 0, 0]
FORWARD_VEC = [ 0, 1, 0]

# ==========
# = Colors =
# ==========
Oak         = [0.65, 0.50, 0.40];
Pine        = [0.85, 0.70, 0.45];
Birch       = [0.90, 0.80, 0.60];
FiberBoard  = [0.70, 0.67, 0.60]   ;
BlackPaint  = [0.20, 0.20, 0.20];
Iron        = [0.36, 0.33, 0.33];
Steel       = [0.65, 0.67, 0.72];
Stainless   = [0.45, 0.43, 0.50]  ;
Aluminum    = [0.77, 0.77, 0.80];
Brass       = [0.88, 0.78, 0.50];
Transparent = [1,    1,    1,   0.2];

# ========================
# = Degrees <==> Radians =
# ========================
def degrees( x_radians):
    return 360.0*x_radians/TAU

def radians( x_degrees):
    return x_degrees/360.0*TAU


# ==============
# = Grid Plane =
# ==============
def grid_plane( grid_unit=12, count=10, line_weight=0.1, plane='xz'):
    
    # Draws a grid of thin lines in the specified plane.  Helpful for 
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
    

def distribute_in_grid( objects, max_bounding_box):
    # Distributes object in a grid in the xy plane
    # with objects spaced max_bounding_box apart
    x_trans, y_trans = max_bounding_box[0:2]
    
    ret = []
    
    grid_size = int(ceil( sqrt(len(objects))))
    objs_placed = 0
    for y in range( grid_size):
        for x in range( grid_size):
            if objs_placed < len(objects):
                ret.append(translate( [x*x_trans, y*y_trans])( objects[objs_placed]))
                objs_placed += 1
            else:
                break
    return union()(ret)

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
def arc( rad, start_degrees, end_degrees, segments=None):
    # Note: the circle arc is drawn from gets segments,
    # not the arc itself.  
    bottom_half_square = back( rad/2.0)(square( [2*rad, rad], center=True))
    top_half_square = forward( rad/2.0)( square( [2*rad, rad], center=True))
    
    if abs( (end_degrees - start_degrees)%360) <=  180:
        end_angle = end_degrees - 180
        
        ret = difference()(
            circle(rad, segments=segments),
            rotate( a=start_degrees)(   bottom_half_square.copy()),
            rotate( a= end_angle)(      bottom_half_square.copy())
        )
    else:
        ret = intersection( )(
            circle( rad, segments=segments),
            union()(
                rotate( a=start_degrees)(   top_half_square.copy()),
                rotate( a=end_degrees)(     bottom_half_square.copy())
            )
        )
    return ret

# TODO: arc_to that creates an arc from point to another point.
# This is useful for making paths.  See the SVG path command:
# See: http://www.w3.org/TR/SVG/implnote.html#ArcImplementationNotes

# =====================
# = Bill of Materials =
# =====================
#   Any part defined in a method can be automatically using the @part()
# decorator. After all parts have been created, call bill_of_materials()
# to generate a report.  Se examples/bom_scad.py for usage
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

def bill_of_materials():
    res = ''
    res +=  "%8s\t%8s\t%8s\t%8s\n"%("Desc.", "Count", "Unit Price", "Total Price")
    all_costs = 0
    for desc,(count, price) in g_parts_dict.items():
        if count > 0:
            if price:
                total = price*count
                all_costs += total
                res += "%8s\t%8d\t%8f\t%8.2f\n"%(desc, count, price, total)
            else:
                res += "%8s\t%8d\n"%(desc, count)
    if all_costs > 0:
        res += "_"*60+'\n'
        res += "Total Cost: %.2f\n"%all_costs
    return res


# ================
# = Bounding Box =
# ================ 
def bounding_box( points):
    all_x = []; all_y = []; all_z = []
    for p in points:
        all_x.append( p[0])
        all_y.append( p[1])
        if len(p) > 2:
            all_z.append( p[2])
        else:
            all_z.append(0)
    
    return [ [min(all_x), min(all_y), min(all_z)], [max(all_x), max(all_y), max(all_z)]]
    


# =======================
# = Hardware dimensions =
# =======================
screw_dimensions = {
    'm3': { 'nut_thickness':2.4, 'nut_inner_diam': 5.4, 'nut_outer_diam':6.1, 'screw_outer_diam':3.0, 'cap_diam':5.5 ,'cap_height':3.0 },
    'm4': { 'nut_thickness':3.1, 'nut_inner_diam': 7.0, 'nut_outer_diam':7.9, 'screw_outer_diam':4.0, 'cap_diam':6.9 ,'cap_height':3.9 },
}

def screw( screw_type='m3', screw_length=16):
    dims = screw_dimensions[screw_type.lower()]
    shaft_rad  = dims['screw_outer_diam']/2
    cap_rad    = dims['cap_diam']/2
    cap_height = dims['cap_height']
    
    ret = union()(
        cylinder( shaft_rad, screw_length),
        up(screw_length)(
            cylinder( cap_rad, cap_height)
        )
    )
    return ret

def nut( screw_type='m3'):
    dims = screw_dimensions[screw_type.lower()]
    outer_rad = dims['nut_outer_diam']
    inner_rad = dims['screw_outer_diam']
    
    ret = difference()(
        circle( outer_rad, segments=6),
        circle( inner_rad)
    )
    return ret

    
# ==============
# = Transforms =
# ==============
def transform_to_point( body, point, normal, two_d=False):
    '''
    Transforms body from horizontal at the origin to point, rotating it so
    vertical now matches the supplied normal.
    
    If two_d is False, rotate the up vector ( [0,0,1]) to match normal.
    If two_d is True, assume we're functioning in XY, and rotate [0,1] to match normal
    
    This is useful for adding objects to arbitrary points on existing objects
    
    Returns body, transformed appropriately
    
    Use case:
        -- make a 2-d shape that will be the side of an acrylic box
        -- identify points on that shape that will need t-slots, and the normals
            to the sides where the slots will be added
        -- draw the t-slot shape at the origin, facing up.
        -- at each point you want to place a slot, call 
            transform_to_point( t_slot_poly, p, n, two_d=True)
    '''
    # TODO: move euclid  functions to a separate file
    from pyeuclid.euclid import Vector3
    
    if two_d:
        up = FORWARD_VEC
    else:
        up = UP_VEC
    
    euc_up = Vector3( *up)
    euc_norm = Vector3( *normal)
    
    rot_angle = degrees( euc_norm.angle_between( euc_up))
    rot_vec = euc_up.cross( euc_norm).as_arr()
    
    if rot_angle == 180:
        rot_vec = up
            
    # # ETJ DEBUG
    # print "************************************************************"
    # classOrFile = self.__class__.__name__ if 'self' in vars() else os.path.basename(__file__)
    # method = sys._getframe().f_code.co_name
    # print "%(classOrFile)s:%(method)s"%vars()
    # print '\trot_angle:  %s'% rot_angle
    # print '\trot_vec:    %s'% rot_vec
    # print "************************************************************"
    # 
    # # END DEBUG
    
    
    
    # TODO: figure out how to get these points
    return translate( point)(
                rotate( a=rot_angle, v=rot_vec)(
                    body
                )
            )


## {{{ http://code.activestate.com/recipes/577068/ (r1)
def frange(*args):
    """frange([start, ] end [, step [, mode]]) -> generator
    
    A float range generator. If not specified, the default start is 0.0
    and the default step is 1.0.
    
    Optional argument mode sets whether frange outputs an open or closed
    interval. mode must be an int. Bit zero of mode controls whether start is
    included (on) or excluded (off); bit one does the same for end. Hence:
        
        0 -> open interval (start and end both excluded)
        1 -> half-open (start included, end excluded)
        2 -> half open (start excluded, end included)
        3 -> closed (start and end both included)
    
    By default, mode=1 and only start is included in the output.
    """
    mode = 1  # Default mode is half-open.
    n = len(args)
    if n == 1:
        args = (0.0, args[0], 1.0)
    elif n == 2:
        args = args + (1.0,)
    elif n == 4:
        mode = args[3]
        args = args[0:3]
    elif n != 3:
        raise TypeError('frange expects 1-4 arguments, got %d' % n)
    assert len(args) == 3
    try:
        start, end, step = [a + 0.0 for a in args]
    except TypeError:
        raise TypeError('arguments must be numbers')
    if step == 0.0:
        raise ValueError('step must not be zero')
    if not isinstance(mode, int):
        raise TypeError('mode must be an int')
    if mode & 1:
        i, x = 0, start
    else:
        i, x = 1, start+step
    if step > 0:
        if mode & 2:
            from operator import le as comp
        else:
            from operator import lt as comp
    else:
        if mode & 2:
            from operator import ge as comp
        else:
            from operator import gt as comp
    while comp(x, end):
        yield x
        i += 1
        x = start + i*step

## end of http://code.activestate.com/recipes/577068/ }}}
