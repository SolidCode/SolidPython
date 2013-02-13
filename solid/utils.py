#! /usr/bin/python
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
def arc( rad, start_degrees, end_degrees, segments=None, invert=False):
    # Note: the circle that this arc is drawn from gets segments,
    # not the arc itself.  That means a quarter-circle arc will
    # have segments/4 segments.
    
    # invert=True will leave the portion of a circumscribed square of sides
    # 2*rad that is NOT in the arc behind.  This is most useful for 90-degree
    # segments, since it's what you'll add to create fillets and take away
    # to create rounds. 
    bottom_half_square = back( rad)(square( [3*rad, 2*rad], center=True))
    top_half_square = forward( rad)( square( [3*rad, 2*rad], center=True))
    
    start_shape = circle( rad, segments=segments)
    if invert:
        start_shape = square(2*rad, center=True) - start_shape
          
    if abs( (end_degrees - start_degrees)%360) <=  180:
        end_angle = end_degrees - 180
        ret = difference()(
            start_shape,
            rotate( a=start_degrees)(   bottom_half_square.copy()),
            rotate( a= end_angle)(      bottom_half_square.copy())
        )
    else:
        ret = intersection( )(
            start_shape,
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
    raise NotImplementedError

# TODO: arc_to that creates an arc from point to another point.
# This is useful for making paths.  See the SVG path command:
# See: http://www.w3.org/TR/SVG/implnote.html#ArcImplementationNotes

# ===================
# = Model Splitting =
# ===================
def split_body_horizontal( body, plane_z=0, 
                            dowel_holes=False, dowel_rad=4.5, hole_depth=15):
    # split body along a plane, returning two pieces
    
    # Optionally, leave holes in both bodies to allow the pieces to be put
    # back together with short dowels.  
    big_num = 10000
    bot_body = body * down( big_num/2 - plane_z)(cube( big_num, center=True)) 
    top_body = body *  up( big_num/2 + plane_z)(cube( big_num, center=True))
    
    # Make holes for dowels if requested. 
    # In case the bodies need to be aligned properly, make two holes, 
    # along the x-axis, separated by one dowel-width
    if dowel_holes:
        dowel = cylinder( r=dowel_rad, h=hole_depth*2, center=True)
        l_dowel = translate([-2*dowel_rad, 0, plane_z])(dowel)
        r_dowel = translate([ 2*dowel_rad, 0, plane_z])(dowel)
        dowels = l_dowel + r_dowel
        bot_body -= dowels
        top_body -= dowels
    
    return ( bot_body, top_body)

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
    # NOTE: The PyEuclid on PyPi doesn't include several elements added to 
    # the module as of 13 Feb 2013.  Add them here until euclid supports them
    def patch_euclid():
        def as_arr_local( self):
            return [ self.x, self.y, self.z]
    
        if 'as_arr' not in dir( Vector3):
            Vector3.as_arr = as_arr_local
    patch_euclid()

    def euclidify( an_obj, intended_class=Vector3):
        # If an_obj is an instance of the appropriate PyEuclid class,
        # return it.  Otherwise, try to turn an_obj into the appropriate
        # class and throw an exception on failure
        
        # Since we often want to convert an entire array
        # of objects (points, etc.) accept arrays of arrays
        
        ret = an_obj
        
        # See if this is an array of arrays.  If so, convert all sublists 
        if isinstance( an_obj, (list, tuple)): 
            if isinstance( an_obj[0], (list,tuple)):
                ret = [intended_class(*p) for p in an_obj]
            elif isinstance( an_obj[0], intended_class):
                # this array is already euclidified; return it
                ret = an_obj
            else:
                try:
                    ret = intended_class( *an_obj)
                except:
                    raise TypeError( "Object: %s ought to be PyEuclid class %s or "
                    "able to form one, but is not."%(an_obj, intended_class.__name__))
        elif not isinstance( an_obj, intended_class):
            try:
                ret = intended_class( *an_obj)
            except:
                raise TypeError( "Object: %s ought to be PyEuclid class %s or "
                "able to form one, but is not."%(an_obj, intended_class.__name__))
        return ret
    
    def euc_to_arr( euc_obj_or_list): # Inverse of euclidify()
        # Call as_arr on euc_obj_or_list or on all its members if it's a list
        if hasattr(euc_obj_or_list, "as_arr"):
            return euc_obj_or_list.as_arr()
        elif isinstance( euc_obj_or_list, (list, tuple)) and hasattr(euc_obj_or_list[0], 'as_arr'):
            return [euc_to_arr( p) for p in euc_obj_or_list]
        else:
            # euc_obj_or_list is neither an array-based PyEuclid object,
            # nor a list of them.  Assume it's a list of points or vectors,
            # and return the list unchanged.  We could be wrong about this, though.
            return euc_obj_or_list
    
    def is_scad( obj):
        return isinstance( obj, openscad_object)
    
    def scad_matrix( euclid_matrix4):
        a = euclid_matrix4
        return [[a.a, a.b, a.c, a.d],
                [a.e, a.f, a.g, a.h],
                [a.i, a.j, a.k, a.l],
                [a.m, a.n, a.o, a.p]
               ]
    

    # ==============
    # = Transforms =
    # ==============
    def transform_to_point( body, dest_point, dest_normal,
            src_point=Point3(0,0,0), src_normal=Vector3(0,1,0), src_up=Vector3(0,0,1)):
        # Transform body to dest_point, looking at dest_normal. 
        # Orientation & offset can be changed by supplying the src arguments
        
        # Body may be:  
        #   -- an openSCAD object
        #   -- a list of 3-tuples  or PyEuclid Point3s
        #   -- a single 3-tuple or Point3
        dest_point = euclidify( dest_point, Point3)
        dest_normal = euclidify( dest_normal, Vector3)
        at = dest_point + dest_normal
        
        look_at_matrix = Matrix4.new_look_at( eye=dest_point, at=at, up=src_up )
        
        if is_scad( body):
            # If the body being altered is a SCAD object, do the matrix mult
            # in OpenSCAD
            sc_matrix = scad_matrix( look_at_matrix)
            res = multmatrix( m=sc_matrix)( body) 
        else:
            body = euclidify( body, Point3)
            if isinstance( body, (list, tuple)):
                res = [look_at_matrix * p for p in body]  
            else:
                res = look_at_matrix *  body
        return res
                     
    
    # ==================
    # = Vector drawing =
    # = -------------- =
    def draw_segment( euc_line=None, endless=False, arrow_rad=7, vec_color=None):
        # Draw a tradtional arrow-head vector in 3-space.
        vec_arrow_rad = arrow_rad
        vec_arrow_head_rad = vec_arrow_rad * 1.5
        vec_arrow_head_length = vec_arrow_rad * 3
        
        if isinstance( euc_line, Vector3):
            p = Point3( *ORIGIN)
            v = euc_line
        elif isinstance( euc_line, Line3): 
            p = euc_line.p
            v = euc_line.v
        elif isinstance( euc_line, list) or isinstance( euc_line, tuple):
            # TODO: This assumes p & v are PyEuclid classes.  
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
        
        arrow = transform_to_point( body=arrow, dest_point=p, dest_normal=v)
        
        if vec_color:
            arrow = color( vec_color)(arrow)
        
        return arrow
    
    # ==========
    # = Offset =
    # = ------ = 
    LEFT, RIGHT = radians(90), radians(-90)
    def parallel_seg( p, q, offset, normal=Vector3( 0, 0, 1), direction=LEFT):
        # returns a PyEuclid Line3 parallel to pq, in the plane determined
        # by p,normal, to the left or right of pq.
        v = q - p
        angle = direction
        rot_v = v.rotate_around( axis=normal, theta=angle)
        rot_v.set_length( offset)
        return Line3( p+rot_v, v )
    
    def inside_direction( a, b, c, offset=10):
        # determines which direction (LEFT, RIGHT) is 'inside' the triangle
        # made by a, b, c.  If ab and bc are parallel, return LEFT
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
    
    def offset_polygon( point_arr, offset, inside=True):
        # returns a closed solidPython polygon offset by offset distance
        # from the polygon described by point_arr.
        op = offset_points( point_arr, offset=offset, inside=inside)
        return polygon( euc_to_arr(op))
    
    def offset_points( point_arr, offset, inside=True):
        # Given a set of points, return a set of points offset from 
        # them.  
        # To get reasonable results, the points need to be all in a plane.
        # ( Non-planar point_arr will still return results, but what constitutes
        # 'inside' or 'outside' would be different in that situation.)
        #
        # What direction inside and outside lie in is determined by the first
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
    
    # ==========================
    # = Extrusion along a path =
    # = ---------------------- =
    def extrude_along_path( shape_pts, path_pts, scale_factors=None): # Possible: twist
        # FIXME: doesn't work with paths of the form [[0,0,0], [0,0,100]]
        
        # Extrude the convex curve defined by shape_pts along path_pts.
        # -- For predictable results, shape_pts must be planar, convex, and lie
        # in the XY plane centered around the origin.
        #
        # -- len( scale_factors) should equal len( path_pts).  If not present, scale
        #       will be assumed to be 1.0 for each point in path_pts
        # -- Future additions might include corner styles (sharp, flattened, round)
        #       or a twist factor
        polyhedron_pts = []
        facet_indices = []
        
        if not scale_factors:
            scale_factors = [1.0] * len(path_pts)
        
        # Make sure we've got Euclid Point3's for all elements
        shape_pts = euclidify( shape_pts, Point3)
        path_pts =  euclidify( path_pts, Point3)
        
        src_up = Vector3( *UP_VEC)
        
        for which_loop in range( len( path_pts) ):
            path_pt = path_pts[which_loop]
            scale = scale_factors[which_loop]
            
            # calculate the tangent to the curve at this point
            if which_loop > 0 and which_loop < len(path_pts) - 1:
                prev_pt = path_pts[which_loop-1]
                next_pt = path_pts[which_loop+1]
                
                v_prev = path_pt - prev_pt
                v_next = next_pt - path_pt
                tangent = v_prev + v_next
            elif which_loop == 0:
                tangent = path_pts[which_loop+1] - path_pt
            elif which_loop == len( path_pts) - 1:
                tangent = path_pt - path_pts[ which_loop -1]
            
            # Scale points
            this_loop = [ (scale*sh) for sh in shape_pts] if scale != 1.0 else shape_pts[:]
                
            # Rotate & translate
            this_loop = transform_to_point( this_loop, dest_point=path_pt, dest_normal=tangent, src_up=src_up)
            
            # Add the transformed points to our final list
            polyhedron_pts += this_loop
            # And calculate the facet indices
            shape_pt_count = len(shape_pts)
            segment_start = which_loop*shape_pt_count
            segment_end = segment_start + shape_pt_count - 1
            if which_loop < len(path_pts) - 1:
                for i in range( segment_start, segment_end):
                    facet_indices.append( [i, i+shape_pt_count, i+1])
                    facet_indices.append( [i+1, i+shape_pt_count, i+shape_pt_count+1])
                facet_indices.append( [segment_start, segment_end, segment_end + shape_pt_count])
                facet_indices.append( [segment_start, segment_end + shape_pt_count, segment_start+shape_pt_count])
        
        # Cap the start of the polyhedron
        for i in range(1, shape_pt_count - 1):
            facet_indices.append( [0, i, i+1])
        
        # And the end ( could be rolled into the earlier loop)
        # FIXME: concave cross-sections will cause this end-capping algorithm to fail
        end_cap_base = len( polyhedron_pts) - shape_pt_count
        for i in range( end_cap_base + 1, len(polyhedron_pts) -1):
            facet_indices.append( [ end_cap_base, i+1, i])
        
        return polyhedron( points = euc_to_arr(polyhedron_pts), triangles=facet_indices)
    
        
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
