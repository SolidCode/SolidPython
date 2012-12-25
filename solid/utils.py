#! /usr/bin/python2.5
# -*- coding: utf-8 -*-
import os, sys, re

from solid import *
from math import *

RIGHT, TOP, LEFT, BOTTOM = range(4)
EPSILON = 0.01
TAU = 2*pi

ORIGIN      = [ 0, 0, 0]
UP_VEC      = [ 0, 0, 1]
RIGHT_VEC   = [ 1, 0, 0]
FORWARD_VEC = [ 0, 1, 0]

# ==========
# = Colors =
# ========== 
Red         = [ 1, 0, 0]
Green       = [ 0, 1, 0]
Blue        = [ 0, 0, 1]
Cyan        = [ 0, 1, 1]
Magenta     = [ 1, 0, 1]
Yellow      = [ 1, 1, 0]
Black       = [ 0, 0, 0]
White       = [ 1, 1, 1]
Oak         = [0.65, 0.50, 0.40]
Pine        = [0.85, 0.70, 0.45]
Birch       = [0.90, 0.80, 0.60]
FiberBoard  = [0.70, 0.67, 0.60]
BlackPaint  = [0.20, 0.20, 0.20]
Iron        = [0.36, 0.33, 0.33]
Steel       = [0.65, 0.67, 0.72]
Stainless   = [0.45, 0.43, 0.50]
Aluminum    = [0.77, 0.77, 0.80]
Brass       = [0.88, 0.78, 0.50]
Transparent = [1,    1,    1,   0.2]

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
    # not the arc itself.  That means a quarter-circle arc will
    # have segments/4 segments
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

def fillet_2d( a, b, c, rad):
    # a, b, and c are three points that form a corner at b.  
    # Return a negative arc (the area NOT covered by a circle) of radius rad
    # in the direction of the more acute angle between 
    
    # Note that if rad is greater than a.distance(b) or c.distance(b), for a 
    # 90-degree corner, the returned shape will include a jagged edge. In
    # general, best to 
    pass

# TODO: arc_to that creates an arc from point to another point.
# This is useful for making paths.  See the SVG path command:
# See: http://www.w3.org/TR/SVG/implnote.html#ArcImplementationNotes

# =====================
# = Bill of Materials =
# =====================
#   Any part defined in a method can be automatically counted using the 
# @part() decorator. After all parts have been created, call 
# bill_of_materials()
# to generate a report.  Se examples/bom_scad.py for usage
g_parts_dict = {}
def part( description='', per_unit_price=None, currency='US$'):
    def wrap(f):
        name = description if description else f.__name__
        g_parts_dict[name] = [0, currency, per_unit_price]
        def wrapped_f( *args):
            name = description if description else f.__name__
            g_parts_dict[name][0] += 1
            return f(*args)
        
        return wrapped_f
    
    return wrap

def bill_of_materials():
    res = ''
    res +=  "%8s\t%8s\t%8s\t%8s\n"%("Desc.", "Count", "Unit Price", "Total Price")
    all_costs = {}
    for desc,(count, currency, price) in g_parts_dict.items():
        if count > 0:
            if price:
                total = price*count
                try:
                  all_costs[currency] += total
                except:
                  all_costs[currency] = total
                  
                res += "%8s\t%8d\t%s %8f\t%s %8.2f\n"%(desc, count, currency, price, currency, total)
            else:
                res += "%8s\t%8d\n"%(desc, count)
    if all_costs > 0:
        res += "_"*60+'\n'
        res += "Total Cost:\n"
        for currency in all_costs.keys():
          res += "\t\t%s %.2f\n"%(currency, all_costs[currency])
        res+="\n"
    return res


#FIXME: finish this.
def bill_of_materials_justified():
    res = ''
    columns = [s.rjust(8) for s in ("Desc.", "Count", "Unit Price", "Total Price")]
    all_costs = {}
    for desc, (count, currency, price) in g_parts_dict.items():
        if count > 0:
            if price:
                total = price*count
                try: 
                    all_costs[currency] += total
                except: 
                    all_costs[currency] = total
                    
                res += "%(desc)s %(count)s %(currency)s %(price)s %(currency)s %(total)s \n"%vars()
            else:
                res += "%(desc)s %(count)s "%vars()  
    if all_costs > 0:
        res += "_"*60+'\n'
        res += "Total Cost:\n"
        for currency in all_costs.keys():
          res += "\t\t%s %.2f\n"%(currency, all_costs[currency])
        res+="\n"
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
    'm5': { 'nut_thickness':4.7, 'nut_inner_diam': 7.9, 'nut_outer_diam':8.8, 'screw_outer_diam':5.0, 'cap_diam':8.7 ,'cap_height':5 },
    
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


# ==================
# = PyEuclid Utils =
# = -------------- =
try:
    from euclid import *    
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
        from euclid import Vector3
        
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
    
            
    LEFT, RIGHT = radians(90), radians(-90)
    # ==========
    # = Offset =
    # = ------ =          
    def draw_segment( euc_line=None, endless=False, vec_color=None):
        vec_arrow_rad = 7
        vec_arrow_head_rad = vec_arrow_rad * 1.5
        vec_arrow_head_length = vec_arrow_rad * 3
        
        if isinstance( euc_line, Vector3):
            p = ORIGIN
            v = euc_line
        elif isinstance( euc_line, Line3): 
            p = euc_line.p
            v = euc_line.v
        elif isinstance( euc_line, list) or isinstance( euc_line, tuple):
            # TODO: we're assuming p & v are PyEuclid classes.  
            # Really, they could as easily be two 3-tuples. Should
            # check for this.   
            p, v = euc_line[0], euc_line[1]
                 
        
        shaft_length = v.magnitude() - vec_arrow_head_length    
        arrow = cylinder( r= vec_arrow_rad, h = shaft_length)
        arrow += up( shaft_length )( 
                    cylinder(r1=vec_arrow_head_rad, r2=0, h = vec_arrow_head_length)
                 )
        if endless:
            endless_length = max( v.magnitude()*10, 200)
            arrow += cylinder( r=vec_arrow_rad/3, h = endless_length, center=True)
        
        arrow = transform_to_point( body=arrow, point=p.as_arr(), normal=v.as_arr())
        
        if vec_color:
            arrow = color( vec_color)(arrow)
        
        return arrow
    
    def parallel_seg( p, q, offset, normal=Vector3( 0, 0, 1), direction=LEFT):
        v = q - p
        angle = direction
        rot_v = v.rotate_around( axis=normal, theta=angle)
        rot_v.set_length( offset)
        return Line3( p+rot_v, v )
    
    def inside_direction( a, b, c, offset=10):
        x = three_point_normal( a, b, c)
        
        # Make two vectors (left & right) for each segment.
        l_segs = [parallel_seg( p, q, normal=x, offset=offset, direction=LEFT) for p,q in ( (a,b), (b,c))]
        r_segs = [parallel_seg( p, q, normal=x, offset=offset, direction=RIGHT) for p,q in ( (a,b), (b,c))]
        
        # Find their intersections.  
        p1 = l_segs[0].intersect( l_segs[1])
        p2 = r_segs[0].intersect( r_segs[1])
        
        # The only way I've figured out to determine which direction is 
        # 'inside' or 'outside' a joint is to calculate both inner and outer
        # vectors and then to find the intersection point closest to point a.
        # This ought to work but it seems like there ought to be a more direct
        # way to figure this out. -ETJ 21 Dec 2012
        
        # The point that's closer to point a is the inside point. 
        if a.distance( p1) <= a.distance( p2):
            return LEFT
        else:
            return RIGHT
    
    def other_dir( left_or_right):
        if left_or_right == LEFT: 
            return RIGHT
        else:
            return LEFT
    
    def three_point_normal( a, b, c):
        ab = b - a
        bc = c - b
        
        seg_ab = Line3( a, ab)
        seg_bc = Line3( b, bc)
        x = seg_ab.v.cross( seg_bc.v)   
        return x
    
    def offset_polygon( point_arr, offset, inside=True, connect_ends=False):
        op = offset_points( point_arr, offset=offset, inside=inside)
        segments = range( len(op))
        if connect_ends:
            segments.append( 0)
        return polygon( [p.as_arr() for p in op], paths=[segments])
    
    def offset_points( point_arr, offset, inside=True):
        # Given a set of points, return a set of points offset from 
        # them.  
        # To get reasonable results, the points need to be all in a plane.
        # ( Non-planar point_arr will still return results, but what constituetes
        # 'inside' or 'outside' would be different in that situation.)
        #
        # What direction inside and outside lie is determined by the first
        # three points (first corner).  In a convex closed shape, this corresponds
        # to inside and outside.  If the first three points describe a concave
        # portion of a closed shape, inside and outside will be switched.  
        #
        # CAD programs generally require an interactive user choice about which
        # side is outside and which is inside.  Robust behavior with this
        # function will require similar checking.  
        
        # Also note that short segments or narrow areas can cause problems
        # as well.  This method suffices for most planar convex figures where
        # segment length is greater than offset, but changing any of those
        # assumptions will cause unattractive results.  If you want real 
        # offsets, use SolidWorks.
        
        # TODO: check for self-intersections in the line connecting the 
        # offset points, and remove them.
        
        # Using the first three points in point_arr, figure out which direction
        # is inside and what plane to put the points in
        in_dir = inside_direction(   *point_arr[0:3])
        normal = three_point_normal( *point_arr[0:3])
        direction = in_dir if inside else other_dir( in_dir)
        
        # Generate offset points for the correct direction
        # for all of point_arr.
        segs = []  
        offset_pts = []
        point_arr += point_arr[ 0:2] # Add first two points to the end as well
        for i in range( len(point_arr) - 1):
            a, b = point_arr[i:i+2]
            par_seg = parallel_seg( a, b, normal=normal, offset=offset, direction=direction )
            segs.append( par_seg)
            if len(segs) > 1:
                int_pt = segs[-2].intersect(segs[-1])
                if int_pt:
                    offset_pts.append( int_pt)
            
        return offset_pts
    
except:
    # euclid isn't available; these methods won't be either
    pass

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
