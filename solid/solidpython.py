#! /usr/bin/env python
# -*- coding: utf-8 -*-

#    Simple Python OpenSCAD Code Generator
#    Copyright (C) 2009    Philipp Tiefenbacher <wizards23@gmail.com>
#    Amendments & additions, (C) 2011 Evan Jones <evan_t_jones@mac.com>
#
#   License: LGPL 2.1 or later
#


import os, sys, re
import inspect
import subprocess
import tempfile



# These are features added to SolidPython but NOT in OpenSCAD.
# Mark them for special treatment
non_rendered_classes = ['hole', 'part']

# ================================
# = Modifier Convenience Methods =
# ================================


def debug(openscad_obj):
    openscad_obj.set_modifier("#")
    return openscad_obj


def background(openscad_obj):
    openscad_obj.set_modifier("%")
    return openscad_obj


def root(openscad_obj):
    openscad_obj.set_modifier("!")
    return openscad_obj


def disable(openscad_obj):
    openscad_obj.set_modifier("*")
    return openscad_obj


# ===============
# = Including OpenSCAD code =
# ===============

# use() & include() mimic OpenSCAD's use/include mechanics.
# -- use() makes methods in scad_file_path.scad available to
#   be called.
# --include() makes those methods available AND executes all code in
#   scad_file_path.scad, which may have side effects.
#   Unless you have a specific need, call use().
def use(scad_file_path, use_not_include=True):
    '''
    Opens scad_file_path, parses it for all usable calls,
    and adds them to caller's namespace.
    '''
    # TODO:  doctest needed
    try:
        module = open(scad_file_path)
        contents = module.read()
        module.close()
    except Exception as e:
        raise Exception("Failed to import SCAD module '%(scad_file_path)s' "
                        "with error: %(e)s " % vars())

    # Once we have a list of all callables and arguments, dynamically
    # add OpenSCADObject subclasses for all callables to the calling module's
    # namespace.
    symbols_dicts = extract_callable_signatures(scad_file_path)

    for sd in symbols_dicts:
        class_str = new_openscad_class_str(sd['name'], sd['args'], sd['kwargs'], 
                                            scad_file_path, use_not_include)
        # If this is called from 'include', we have to look deeper in the stack
        # to find the right module to add the new class to.
        stack_depth = 2 if use_not_include else 3
        exec(class_str, calling_module(stack_depth).__dict__)

    return True


def include(scad_file_path):
    return use(scad_file_path, use_not_include=False)


# =========================================
# = Rendering Python code to OpenSCAD code=
# =========================================
def _find_include_strings(obj):
    include_strings = set()
    if isinstance(obj, IncludedOpenSCADObject):
        include_strings.add(obj.include_string)
    for child in obj.children:
        include_strings.update(_find_include_strings(child))
    return include_strings


def scad_render(scad_object, file_header=''):
    # Make this object the root of the tree
    root = scad_object

    # Scan the tree for all instances of
    # IncludedOpenSCADObject, storing their strings
    include_strings = _find_include_strings(root)

    # and render the string
    includes = ''.join(include_strings) + "\n"
    scad_body = root._render()
    return file_header + includes + scad_body


def scad_render_animated(func_to_animate, steps=20, back_and_forth=True, filepath=None, file_header=''):
    # func_to_animate takes a single float argument, _time in [0, 1), and
    # returns an OpenSCADObject instance.
    #
    # Outputs an OpenSCAD file with func_to_animate() evaluated at "steps"
    # points between 0 & 1, with time never evaluated at exactly 1

    # If back_and_forth is True, smoothly animate the full extent of the motion
    # and then reverse it to the beginning; this avoids skipping between beginning
    # and end of the animated motion

    # NOTE: This is a hacky way to solve a simple problem.  To use OpenSCAD's
    # animation feature, our code needs to respond to changes in the value
    # of the OpenSCAD variable $t, but I can't think of a way to get a
    # float variable from our code and put it into the actual SCAD code.
    # Instead, we just evaluate our code at each desired step, and write it
    # all out in the SCAD code for each case, with an if/else tree.  Depending
    # on the number of steps, this could create hundreds of times more SCAD
    # code than is needed.  But... it does work, with minimal Python code, so
    # here it is. Better solutions welcome. -ETJ 28 Mar 2013

    # NOTE: information on the OpenSCAD manual wiki as of November 2012 implies
    # that the OpenSCAD app does its animation irregularly; sometimes it animates
    # one loop in steps iterations, and sometimes in (steps + 1).  Do it here
    # in steps iterations, meaning that we won't officially reach $t =1.

    # Note also that we check for ranges of time rather than equality; this
    # should avoid any rounding error problems, and doesn't require the file
    # to be animated with an identical number of steps to the way it was
    # created. -ETJ 28 Mar 2013
    scad_obj = func_to_animate()
    include_strings = _find_include_strings(scad_obj)
    # and render the string
    includes = ''.join(include_strings) + "\n"

    rendered_string = file_header + includes

    if back_and_forth:
        steps *= 2

    for i in range(steps):
        time = i * 1.0 / steps
        end_time = (i + 1) * 1.0 / steps
        eval_time = time
        # Looping back and forth means there's no jump between the start and
        # end position
        if back_and_forth:
            if time < 0.5:
                eval_time = time * 2
            else:
                eval_time = 2 - 2 * time
        scad_obj = func_to_animate(_time=eval_time)

        scad_str = indent(scad_obj._render())
        rendered_string += ("if ($t >= %(time)s && $t < %(end_time)s){"
                            "   %(scad_str)s\n"
                            "}\n" % vars())
    return rendered_string


def scad_render_animated_file(func_to_animate, steps=20, back_and_forth=True, 
                              filepath=None, file_header='', include_orig_code=True):
    rendered_string = scad_render_animated(func_to_animate, steps, 
                                            back_and_forth, file_header)
    return _write_code_to_file(rendered_string, filepath, include_orig_code)


def scad_render_to_file(scad_object, filepath=None, file_header='', include_orig_code=True):
    rendered_string = scad_render(scad_object, file_header)
    return _write_code_to_file(rendered_string, filepath, include_orig_code)


def _write_code_to_file(rendered_string, filepath=None, include_orig_code=True):
    try:
        calling_file = os.path.abspath(calling_module(stack_depth=3).__file__)

        if include_orig_code:
            rendered_string += sp_code_in_scad_comment(calling_file)

        # This write is destructive, and ought to do some checks that the write
        # was successful.
        # If filepath isn't supplied, place a .scad file with the same name
        # as the calling module next to it
        if not filepath:
            filepath = os.path.splitext(calling_file)[0] + '.scad'
    except AttributeError as e:
        # If no calling_file was found, this is being called from the terminal.
        # We can't read original code from a file, so don't try,
        # and can't read filename from the calling file either, so just save to
        # solid.scad.
        if not filepath:
            filepath = os.path.abspath('.') + "/solid.scad"

    f = open(filepath, "w")
    f.write(rendered_string)
    f.close()
    return True


def sp_code_in_scad_comment(calling_file):
    # Once a SCAD file has been created, it's difficult to reconstruct
    # how it got there, since it has no variables, modules, etc.  So, include
    # the Python code that generated the scad code as comments at the end of
    # the SCAD code
    pyopenscad_str = open(calling_file, 'r').read()

    # TODO: optimally, this would also include a version number and
    # git hash (& date & github URL?) for the version of solidpython used
    # to create a given file; That would future-proof any given SP-created
    # code because it would point to the relevant dependencies as well as
    # the actual code
    pyopenscad_str = ("\n"
                      "/***********************************************\n"
                      "*********      SolidPython code:      **********\n"
                      "************************************************\n"
                      " \n"
                      "%(pyopenscad_str)s \n"
                      " \n"
                      "************************************************/\n") % vars()
    return pyopenscad_str


# =========================
# = Internal Utilities    =
# =========================
class OpenSCADObject(object):

    def __init__(self, name, params):
        self.name = name
        self.params = params
        self.children = []
        self.modifier = ""
        self.parent = None
        self.is_hole = False
        self.has_hole_children = False
        self.is_part_root = False

    def set_hole(self, is_hole=True):
        self.is_hole = is_hole
        return self

    def set_part_root(self, is_root=True):
        self.is_part_root = is_root
        return self

    def find_hole_children(self, path=None):
        # Because we don't force a copy every time we re-use a node
        # (e.g a = cylinder(2, 6);  b = right(10) (a)
        #  the identical 'a' object appears in the tree twice),
        # we can't count on an object's 'parent' field to trace its
        # path to the root.  Instead, keep track explicitly
        path = path if path else [self]
        hole_kids = []

        for child in self.children:
            path.append(child)
            if child.is_hole:
                hole_kids.append(child)
                # Mark all parents as having a hole child
                for p in path:
                    p.has_hole_children = True
            # Don't append holes from separate parts below us
            elif child.is_part_root:
                continue
            # Otherwise, look below us for children
            else:
                hole_kids += child.find_hole_children(path)
            path.pop()

        return hole_kids

    def set_modifier(self, m):
        # Used to add one of the 4 single-character modifiers: 
        # #(debug) !(root) %(background) or *(disable)
        string_vals = {'disable':      '*',
                       'debug':        '#',
                       'background':   '%',
                       'root':         '!',
                       '*': '*',
                       '#': '#',
                       '%': '%',
                       '!': '!'}

        self.modifier = string_vals.get(m.lower(), '')
        return self

    def _render(self, render_holes=False):
        '''
        NOTE: In general, you won't want to call this method. For most purposes,
        you really want scad_render(), 
        Calling obj._render won't include necessary 'use' or 'include' statements
        '''
        # First, render all children
        s = ""
        for child in self.children:
            # Don't immediately render hole children.
            # Add them to the parent's hole list,
            # And render after everything else
            if not render_holes and child.is_hole:
                continue
            s += child._render(render_holes)

        # Then render self and prepend/wrap it around the children
        # I've added designated parts and explicit holes to SolidPython.
        # OpenSCAD has neither, so don't render anything from these objects
        if self.name in non_rendered_classes:
            pass
        elif not self.children:
            s = self._render_str_no_children() + ";"
        else:
            s = self._render_str_no_children() + " {" + indent(s) + "\n}"

        # If this is the root object or the top of a separate part,
        # find all holes and subtract them after all positive geometry
        # is rendered
        if (not self.parent) or self.is_part_root:
            hole_children = self.find_hole_children()

            if len(hole_children) > 0:
                s += "\n/* Holes Below*/"
                s += self._render_hole_children()

                # wrap everything in the difference
                s = "\ndifference(){" + indent(s) + " /* End Holes */ \n}"
        return s

    def _render_str_no_children(self):
        s = "\n" + self.modifier + self.name + "("
        first = True

        # OpenSCAD doesn't have a 'segments' argument, but it does
        # have '$fn'.  Swap one for the other
        if 'segments' in self.params:
            self.params['$fn'] = self.params.pop('segments')

        valid_keys = self.params.keys()

        # intkeys are the positional parameters
        intkeys = list(filter(lambda x: type(x) == int, valid_keys))
        intkeys.sort()

        # named parameters
        nonintkeys = list(filter(lambda x: not type(x) == int, valid_keys))
        all_params_sorted = intkeys + nonintkeys
        if all_params_sorted:
            all_params_sorted = sorted(all_params_sorted)

        for k in all_params_sorted:
            v = self.params[k]
            if v == None:
                continue

            if not first:
                s += ", "
            first = False

            if type(k) == int:
                s += py2openscad(v)
            else:
                s += k + " = " + py2openscad(v)

        s += ")"
        return s

    def _render_hole_children(self):
        # Run down the tree, rendering only those nodes
        # that are holes or have holes beneath them
        if not self.has_hole_children:
            return ""
        s = ""
        for child in self.children:
            if child.is_hole:
                s += child._render(render_holes=True)
            elif child.has_hole_children:
                # Holes exist in the compiled tree in two pieces:
                # The shapes of the holes themselves, (an object for which
                # obj.is_hole is True, and all its children) and the
                # transforms necessary to put that hole in place, which
                # are inherited from non-hole geometry.

                # Non-hole Intersections & differences can change (shrink)
                # the size of holes, and that shouldn't happen: an
                # intersection/difference with an empty space should be the
                # entirety of the empty space.
                #  In fact, the intersection of two empty spaces should be
                # everything contained in both of them:  their union.
                # So... replace all super-hole intersection/diff transforms
                # with union in the hole segment of the compiled tree.
                # And if you figure out a better way to explain this,
                # please, please do... because I think this works, but I
                # also think my rationale is shaky and imprecise. 
                # -ETJ 19 Feb 2013
                s = s.replace("intersection", "union")
                s = s.replace("difference", "union")
                s += child._render_hole_children()
        if self.name in non_rendered_classes:
            pass
        else:
            s = self._render_str_no_children() + "{" + indent(s) + "\n}"
        return s

    def add(self, child):
        '''
        if child is a single object, assume it's an OpenSCADObject and 
        add it to self.children

        if child is a list, assume its members are all OpenSCADObjects and
        add them all to self.children
        '''
        if isinstance(child, (list, tuple)):
            # __call__ passes us a list inside a tuple, but we only care
            # about the list, so skip single-member tuples containing lists
            if len(child) == 1 and isinstance(child[0], (list, tuple)):
                child = child[0]
            [self.add(c) for c in child]
        else:
            self.children.append(child)
            child.set_parent(self)
        return self

    def set_parent(self, parent):
        self.parent = parent

    def add_param(self, k, v):
        if k == '$fn':
            k = 'segments'
        self.params[k] = v
        return self

    def copy(self):
        # Provides a copy of this object and all children,
        # but doesn't copy self.parent, meaning the new object belongs
        # to a different tree
        # If we're copying a scad object, we know it is an instance of
        # a dynamically created class called self.name.
        # Initialize an instance of that class with the same params
        # that created self, the object being copied.

        # Python can't handle an '$fn' argument, while openSCAD only wants
        # '$fn'.  Swap back and forth as needed; the final renderer will
        # sort this out.
        if '$fn' in self.params:
            self.params['segments'] = self.params.pop('$fn')

        other = globals()[self.name](**self.params)
        other.set_modifier(self.modifier)
        other.set_hole(self.is_hole)
        other.set_part_root(self.is_part_root)
        other.has_hole_children = self.has_hole_children
        for c in self.children:
            other.add(c.copy())
        return other

    def __call__(self, *args):
        '''
        Adds all objects in args to self.  This enables OpenSCAD-like syntax,
        e.g.:
        union()(
            cube(),
            sphere()
        )
        '''
        return self.add(args)

    def __add__(self, x):
        '''
        This makes u = a+b identical to:
        u = union()(a, b )
        '''
        return union()(self, x)

    def __sub__(self, x):
        '''
        This makes u = a - b identical to:
        u = difference()(a, b )
        '''
        return difference()(self, x)

    def __mul__(self, x):
        '''
        This makes u = a * b identical to:
        u = intersection()(a, b )
        '''
        return intersection()(self, x)

    def _repr_png_(self):
        '''
        Allow rich clients such as the IPython Notebook, to display the current
        OpenSCAD rendering of this object.
        '''
        png_data = None
        tmp = tempfile.NamedTemporaryFile(suffix=".scad", delete=False)
        tmp_png = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        try:
            scad_text = scad_render(self).encode("utf-8")
            tmp.write(scad_text)
            tmp.close()
            tmp_png.close()
            subprocess.Popen([
                "openscad",
                "--preview",
                "-o", tmp_png.name,
                tmp.name
            ]).communicate()

            with open(tmp_png.name, "rb") as png:
                png_data = png.read()
        finally:
            os.unlink(tmp.name)
            os.unlink(tmp_png.name)

        return png_data


class IncludedOpenSCADObject(OpenSCADObject):
    # Identical to OpenSCADObject, but each subclass of IncludedOpenSCADObject
    # represents imported scad code, so each instance needs to store the path
    # to the scad file it's included from.

    def __init__(self, name, params, include_file_path, use_not_include=False, **kwargs):
        self.include_file_path = self._get_include_path(include_file_path)

        if use_not_include:
            self.include_string = 'use <%s>\n' % self.include_file_path
        else:
            self.include_string = 'include <%s>\n' % self.include_file_path

        # Just pass any extra arguments straight on to OpenSCAD; it'll accept
        # them
        if kwargs:
            params.update(kwargs)

        OpenSCADObject.__init__(self, name, params)

    def _get_include_path(self, include_file_path):
        # Look through sys.path for anyplace we can find a valid file ending
        # in include_file_path.  Return that absolute path
        if os.path.isabs(include_file_path) and os.path.isfile(include_file_path):
            return include_file_path
        else:
            for p in sys.path:
                whole_path = os.path.join(p, include_file_path)
                if os.path.isfile(whole_path):
                    return os.path.abspath(whole_path)

        # No loadable SCAD file was found in sys.path.  Raise an error
        raise ValueError("Unable to find included SCAD file: "
                         "%(include_file_path)s in sys.path" % vars())


def calling_module(stack_depth=2):
    '''
    Returns the module *2* back in the frame stack.  That means:
    code in module A calls code in module B, which asks calling_module()
    for module A.

    This means that we have to know exactly how far back in the stack
    our desired module is; if code in module B calls another function in 
    module B, we have to increase the stack_depth argument to account for
    this.

    Got that?
    '''
    frm = inspect.stack()[stack_depth]
    calling_mod = inspect.getmodule(frm[0])
    # If calling_mod is None, this is being called from an interactive session.
    # Return that module.  (Note that __main__ doesn't have a __file__ attr,
    # but that's caught elsewhere.)
    if not calling_mod:
        import __main__ as calling_mod
    return calling_mod


def new_openscad_class_str(class_name, args=[], kwargs=[], include_file_path=None, use_not_include=True):
    args_str = ''
    args_pairs = ''

    for arg in args:
        args_str += ', ' + arg
        args_pairs += "'%(arg)s':%(arg)s, " % vars()

    # kwargs have a default value defined in their SCAD versions.  We don't
    # care what that default value will be (SCAD will take care of that), just
    # that one is defined.
    for kwarg in kwargs:
        args_str += ', %(kwarg)s=None' % vars()
        args_pairs += "'%(kwarg)s':%(kwarg)s, " % vars()

    if include_file_path:
        # include_file_path may include backslashes on Windows; escape them
        # again here so any backslashes don't get used as escape characters
        # themselves
        include_file_path = include_file_path.replace('\\', '\\\\')

        # NOTE the explicit import of 'solid' below. This is a fix for:
        # https://github.com/SolidCode/SolidPython/issues/20 -ETJ 16 Jan 2014
        result = ("import solid\n"
                  "class %(class_name)s(solid.IncludedOpenSCADObject):\n"
                  "   def __init__(self%(args_str)s, **kwargs):\n"
                  "       solid.IncludedOpenSCADObject.__init__(self, '%(class_name)s', {%(args_pairs)s }, include_file_path='%(include_file_path)s', use_not_include=%(use_not_include)s, **kwargs )\n"
                  "   \n"
                  "\n" % vars())
    else:
        result = ("class %(class_name)s(OpenSCADObject):\n"
                  "   def __init__(self%(args_str)s):\n"
                  "       OpenSCADObject.__init__(self, '%(class_name)s', {%(args_pairs)s })\n"
                  "   \n"
                  "\n" % vars())

    return result


def py2openscad(o):
    if type(o) == bool:
        return str(o).lower()
    if type(o) == float:
        return "%.10f" % o
    if type(o) == list or type(o) == tuple:
        s = "["
        first = True
        for i in o:
            if not first:
                s += ", "
            first = False
            s += py2openscad(i)
        s += "]"
        return s
    if type(o) == str:
        return '"' + o + '"'
    return str(o)


def indent(s):
    return s.replace("\n", "\n\t")


# ===========
# = Parsing =
# ===========
def extract_callable_signatures(scad_file_path):
    with open(scad_file_path) as f:
        scad_code_str = f.read()
    return parse_scad_callables(scad_code_str)


def parse_scad_callables(scad_code_str):
    callables = []

    # Note that this isn't comprehensive; tuples or nested data structures in
    # a module definition will defeat it.

    # Current implementation would throw an error if you tried to call a(x, y)
    # since Python would expect a(x);  OpenSCAD itself ignores extra arguments,
    # but that's not really preferable behavior

    # TODO:  write a pyparsing grammar for OpenSCAD, or, even better, use the yacc parse grammar
    # used by the language itself.  -ETJ 06 Feb 2011

    no_comments_re = r'(?mxs)(//.*?\n|/\*.*?\*/)'

    # Also note: this accepts: 'module x(arg) =' and 'function y(arg) {', both
    # of which are incorrect syntax
    mod_re = r'(?mxs)^\s*(?:module|function)\s+(?P<callable_name>\w+)\s*\((?P<all_args>.*?)\)\s*(?:{|=)'

    # This is brittle.  To get a generally applicable expression for all arguments,
    # we'd need a real parser to handle nested-list default args or parenthesized statements.
    # For the moment, assume a maximum of one square-bracket-delimited list
    args_re = r'(?mxs)(?P<arg_name>\w+)(?:\s*=\s*(?P<default_val>[\w.-]+|\[.*\]))?(?:,|$)'

    # remove all comments from SCAD code
    scad_code_str = re.sub(no_comments_re, '', scad_code_str)
    # get all SCAD callables
    mod_matches = re.finditer(mod_re, scad_code_str)

    for m in mod_matches:
        callable_name = m.group('callable_name')
        args = []
        kwargs = []
        all_args = m.group('all_args')
        if all_args:
            arg_matches = re.finditer(args_re, all_args)
            for am in arg_matches:
                arg_name = am.group('arg_name')
                if am.group('default_val'):
                    kwargs.append(arg_name)
                else:
                    args.append(arg_name)

        callables.append({'name': callable_name, 'args': args, 'kwargs': kwargs})

    return callables


# ===============================
# Classes for OpenSCAD builtins =
# ===============================
class polygon(OpenSCADObject):
    '''
    Create a polygon with the specified points and paths.

    :param points: the list of points of the polygon
    :type points: sequence of 2 element sequences

    :param paths: Either a single vector, enumerating the point list, ie. the order to traverse the points, or, a vector of vectors, ie a list of point lists for each separate curve of the polygon. The latter is required if the polygon has holes. The parameter is optional and if omitted the points are assumed in order. (The 'pN' components of the *paths* vector are 0-indexed references to the elements of the *points* vector.)
    '''
    def __init__(self, points, paths=None):
        if not paths:
            paths = [list(range(len(points)))]
        OpenSCADObject.__init__(self, 'polygon',
                                {'points': points, 'paths': paths})


class circle(OpenSCADObject):
    '''
    Creates a circle at the origin of the coordinate system. The argument
    name is optional.

    :param r: This is the radius of the circle. Default value is 1.
    :type r: number

    :param d: This is the diameter of the circle. Default value is 1.
    :type d: number

    :param segments: Number of fragments in 360 degrees.
    :type segments: int
    '''
    def __init__(self, r=None, d=None, segments=None):
        OpenSCADObject.__init__(self, 'circle',
                                {'r': r, 'd': d, 'segments': segments})


class square(OpenSCADObject):
    '''
    Creates a square at the origin of the coordinate system. When center is
    True the square will be centered on the origin, otherwise it is created
    in the first quadrant. The argument names are optional if the arguments
    are given in the same order as specified in the parameters

    :param size: If a single number is given, the result will be a square with sides of that length. If a 2 value sequence is given, then the values will correspond to the lengths of the X and Y sides.  Default value is 1.
    :type size: number or 2 value sequence

    :param center: This determines the positioning of the object. If True, object is centered at (0,0). Otherwise, the square is placed in the positive quadrant with one corner at (0,0). Defaults to False.
    :type center: boolean
    '''
    def __init__(self, size=None, center=None):
        OpenSCADObject.__init__(self, 'square',
                                {'size': size, 'center': center})


class sphere(OpenSCADObject):
    '''
    Creates a sphere at the origin of the coordinate system. The argument
    name is optional.

    :param r: Radius of the sphere.
    :type r: number

    :param d: Diameter of the sphere.
    :type d: number

    :param segments: Resolution of the sphere
    :type segments: int
    '''
    def __init__(self, r=None, d=None, segments=None):
        OpenSCADObject.__init__(self, 'sphere',
                                {'r': r, 'd': d, 'segments': segments})


class cube(OpenSCADObject):
    '''
    Creates a cube at the origin of the coordinate system. When center is
    True the cube will be centered on the origin, otherwise it is created in
    the first octant. The argument names are optional if the arguments are
    given in the same order as specified in the parameters

    :param size: If a single number is given, the result will be a cube with sides of that length. If a 3 value sequence is given, then the values will correspond to the lengths of the X, Y, and Z sides. Default value is 1.
    :type size: number or 3 value sequence

    :param center: This determines the positioning of the object. If True, object is centered at (0,0,0). Otherwise, the cube is placed in the positive quadrant with one corner at (0,0,0). Defaults to False
    :type center: boolean
    '''
    def __init__(self, size=None, center=None):
        OpenSCADObject.__init__(self, 'cube',
                                {'size': size, 'center': center})


class cylinder(OpenSCADObject):
    '''
    Creates a cylinder or cone at the origin of the coordinate system. A
    single radius (r) makes a cylinder, two different radi (r1, r2) make a
    cone.

    :param h: This is the height of the cylinder. Default value is 1.
    :type h: number

    :param r: The radius of both top and bottom ends of the cylinder. Use this parameter if you want plain cylinder. Default value is 1.
    :type r: number

    :param r1: This is the radius of the cone on bottom end. Default value is 1.
    :type r1: number

    :param r2: This is the radius of the cone on top end. Default value is 1.
    :type r2: number

    :param d: The diameter of both top and bottom ends of the cylinder.  Use this parameter if you want plain cylinder. Default value is 1.
    :type d: number

    :param d1: This is the diameter of the cone on bottom end. Default value is 1.
    :type d1: number

    :param d2: This is the diameter of the cone on top end. Default value is 1.
    :type d2: number

    :param center: If True will center the height of the cone/cylinder around the origin. Default is False, placing the base of the cylinder or r1 radius of cone at the origin.
    :type center: boolean

    :param segments: The fixed number of fragments to use.
    :type segments: int
    '''
    def __init__(self, r=None, h=None, r1=None, r2=None, d=None, d1=None,
                 d2=None, center=None, segments=None):
        OpenSCADObject.__init__(self, 'cylinder',
                                {'r': r, 'h': h, 'r1': r1, 'r2': r2, 'd': d,
                                 'd1': d1, 'd2': d2, 'center': center,
                                 'segments': segments})


class polyhedron(OpenSCADObject):
    '''
    Create a polyhedron with a list of points and a list of faces. The point
    list is all the vertices of the shape, the faces list is how the points
    relate to the surfaces of the polyhedron.

    *note: if your version of OpenSCAD is lower than 2014.03 replace "faces"
    with "triangles" in the below examples*

    :param points: sequence of points or vertices (each a 3 number sequence).

    :param triangles: (*deprecated in version 2014.03, use faces*) vector of point triplets (each a 3 number sequence). Each number is the 0-indexed point number from the point vector.

    :param faces: (*introduced in version 2014.03*) vector of point n-tuples with n >= 3. Each number is the 0-indexed point number from the point vector.  That is, faces=[[0,1,4]] specifies a triangle made from the first, second, and fifth point listed in points. When referencing more than 3 points in a single tuple, the points must all be on the same plane.

    :param convexity: The convexity parameter specifies the maximum number of front sides (back sides) a ray intersecting the object might penetrate. This parameter is only needed for correctly displaying the object in OpenCSG preview mode and has no effect on the polyhedron rendering.
    :type convexity: int
    '''
    def __init__(self, points, faces, convexity=None, triangles=None):
        OpenSCADObject.__init__(self, 'polyhedron',
                                {'points': points, 'faces': faces,
                                 'convexity': convexity,
                                 'triangles': triangles})


class union(OpenSCADObject):
    '''
    Creates a union of all its child nodes. This is the **sum** of all
    children.
    '''
    def __init__(self):
        OpenSCADObject.__init__(self, 'union', {})


class intersection(OpenSCADObject):
    '''
    Creates the intersection of all child nodes. This keeps the
    **overlapping** portion
    '''
    def __init__(self):
        OpenSCADObject.__init__(self, 'intersection', {})


class difference(OpenSCADObject):
    '''
    Subtracts the 2nd (and all further) child nodes from the first one.
    '''
    def __init__(self):
        OpenSCADObject.__init__(self, 'difference', {})


class hole(OpenSCADObject):
    def __init__(self):
        OpenSCADObject.__init__(self, 'hole', {})
        self.set_hole(True)


class part(OpenSCADObject):
    def __init__(self):
        OpenSCADObject.__init__(self, 'part', {})
        self.set_part_root(True)


class translate(OpenSCADObject):
    '''
    Translates (moves) its child elements along the specified vector.

    :param v: X, Y and Z translation
    :type v: 3 value sequence
    '''
    def __init__(self, v=None):
        OpenSCADObject.__init__(self, 'translate', {'v': v})


class scale(OpenSCADObject):
    '''
    Scales its child elements using the specified vector.

    :param v: X, Y and Z scale factor
    :type v: 3 value sequence
    '''
    def __init__(self, v=None):
        OpenSCADObject.__init__(self, 'scale', {'v': v})


class rotate(OpenSCADObject):
    '''
    Rotates its child 'a' degrees about the origin of the coordinate system
    or around an arbitrary axis.

    :param a: degrees of rotation, or sequence for degrees of rotation in each of the X, Y and Z axis.
    :type a: number or 3 value sequence

    :param v: sequence specifying 0 or 1 to indicate which axis to rotate by 'a' degrees. Ignored if 'a' is a sequence.
    :type v: 3 value sequence
    '''
    def __init__(self, a=None, v=None):
        OpenSCADObject.__init__(self, 'rotate', {'a': a, 'v': v})


class mirror(OpenSCADObject):
    '''
    Mirrors the child element on a plane through the origin.

    :param v: the normal vector of a plane intersecting the origin through which to mirror the object.
    :type v: 3 number sequence

    '''
    def __init__(self, v):
        OpenSCADObject.__init__(self, 'mirror', {'v': v})


class multmatrix(OpenSCADObject):
    '''
    Multiplies the geometry of all child elements with the given 4x4
    transformation matrix.

    :param m: transformation matrix
    :type m: sequence of 4 sequences, each containing 4 numbers.
    '''
    def __init__(self, m):
        OpenSCADObject.__init__(self, 'multmatrix', {'m': m})


class color(OpenSCADObject):
    '''
    Displays the child elements using the specified RGB color + alpha value.
    This is only used for the F5 preview as CGAL and STL (F6) do not
    currently support color. The alpha value will default to 1.0 (opaque) if
    not specified.

    :param c: RGB color + alpha value.
    :type c: sequence of 3 or 4 numbers between 0 and 1
    '''
    def __init__(self, c):
        OpenSCADObject.__init__(self, 'color', {'c': c})


class minkowski(OpenSCADObject):
    '''
    Renders the `minkowski
    sum <http://www.cgal.org/Manual/latest/doc_html/cgal_manual/Minkowski_sum_3/Chapter_main.html>`__
    of child nodes.
    '''
    def __init__(self):
        OpenSCADObject.__init__(self, 'minkowski', {})


class hull(OpenSCADObject):
    '''
    Renders the `convex
    hull <http://www.cgal.org/Manual/latest/doc_html/cgal_manual/Convex_hull_2/Chapter_main.html>`__
    of child nodes.
    '''
    def __init__(self):
        OpenSCADObject.__init__(self, 'hull', {})


class inset(OpenSCADObject):
    '''
    Creates a polygon at an offset `d` inside a 2D shape.

    :param d: offset
    :type d: number
    '''
    def __init__(self, d=None):
        OpenSCADObject.__init__(self, 'inset', {'d': d})


class outset(OpenSCADObject):
    '''
    Creates a polygon at an offset `d` outside a 2D shape.

    :param d: offset
    :type d: number
    '''
    def __init__(self, d=None):
        OpenSCADObject.__init__(self, 'outset', {'d': d})


class fillet(OpenSCADObject):
    '''
    Adds fillets of radius `r` to all concave corners of a 2D shape.

    :param r: radius
    :type r: number
    '''
    def __init__(self, r=None):
        OpenSCADObject.__init__(self, 'fillet', {'r': r})


class rounding(OpenSCADObject):
    '''
    Adds rounding of radius `r` to all convex corners of a 2D shape.

    :param r: radius
    :type r: number
    '''
    def __init__(self, r=None):
        OpenSCADObject.__init__(self, 'rounding', {'r': r})


class render(OpenSCADObject):
    '''
    Always calculate the CSG model for this tree (even in OpenCSG preview
    mode).

    :param convexity: The convexity parameter specifies the maximum number of front sides (back sides) a ray intersecting the object might penetrate. This parameter is only needed for correctly displaying the object in OpenCSG preview mode and has no effect on the polyhedron rendering.
    :type convexity: int
    '''
    def __init__(self, convexity=None):
        OpenSCADObject.__init__(self, 'render', {'convexity': convexity})


class linear_extrude(OpenSCADObject):
    '''
    Linear Extrusion is a modeling operation that takes a 2D polygon as
    input and extends it in the third dimension. This way a 3D shape is
    created.

    :param height: the extrusion height.
    :type height: number

    :param center: determines if the object is centered on the Z-axis after extrusion.
    :type center: boolean

    :param convexity: The convexity parameter specifies the maximum number of front sides (back sides) a ray intersecting the object might penetrate. This parameter is only needed for correctly displaying the object in OpenCSG preview mode and has no effect on the polyhedron rendering.
    :type convexity: int

    :param twist: Twist is the number of degrees of through which the shape is extruded.  Setting to 360 will extrude through one revolution.  The twist direction follows the left hand rule.
    :type twist: number

    :param slices: number of slices to extrude. Can be used to improve the output.
    :type slices: int

    :param scale: relative size of the top of the extrusion compared to the start
    :type scale: number

    '''
    def __init__(self, height=None, center=None, convexity=None, twist=None,
                 slices=None, scale=None):
        OpenSCADObject.__init__(self, 'linear_extrude',
                                {'height': height, 'center': center,
                                 'convexity': convexity, 'twist': twist,
                                 'slices': slices, 'scale':scale})


class rotate_extrude(OpenSCADObject):
    '''
    A rotational extrusion is a Linear Extrusion with a twist, literally.
    Unfortunately, it can not be used to produce a helix for screw threads
    as the 2D outline must be normal to the axis of rotation, ie they need
    to be flat in 2D space.

    The 2D shape needs to be either completely on the positive, or negative
    side (not recommended), of the X axis. It can touch the axis, i.e. zero,
    however if the shape crosses the X axis a warning will be shown in the
    console windows and the rotate\_extrude() will be ignored. If the shape
    is in the negative axis the faces will be inside-out, you probably don't
    want to do that; it may be fixed in the future.

    :param convexity: The convexity parameter specifies the maximum number of front sides (back sides) a ray intersecting the object might penetrate. This parameter is only needed for correctly displaying the object in OpenCSG preview mode and has no effect on the polyhedron rendering.
    :type convexity: int

    :param segments: The fixed number of fragments to use.
    :type segments: int

    '''
    def __init__(self, convexity=None, segments=None):
        OpenSCADObject.__init__(self, 'rotate_extrude',
                                {'convexity': convexity, 'segments': segments})


class dxf_linear_extrude(OpenSCADObject):
    def __init__(self, file, layer=None, height=None, center=None,
                 convexity=None, twist=None, slices=None):
        OpenSCADObject.__init__(self, 'dxf_linear_extrude',
                                {'file': file, 'layer': layer,
                                 'height': height, 'center': center,
                                 'convexity': convexity, 'twist': twist,
                                 'slices': slices})


class projection(OpenSCADObject):
    '''
    Creates 2d shapes from 3d models, and export them to the dxf format.
    It works by projecting a 3D model to the (x,y) plane, with z at 0.

    :param cut: when True only points with z=0 will be considered (effectively cutting the object) When False points above and below the plane will be considered as well (creating a proper projection).
    :type cut: boolean
    '''
    def __init__(self, cut=None):
        OpenSCADObject.__init__(self, 'projection', {'cut': cut})


class surface(OpenSCADObject):
    '''
    Surface reads information from text or image files.

    :param file: The path to the file containing the heightmap data.
    :type file: string

    :param center: This determines the positioning of the generated object. If True, object is centered in X- and Y-axis. Otherwise, the object is placed in the positive quadrant. Defaults to False.
    :type center: boolean

    :param invert: Inverts how the color values of imported images are translated into height values. This has no effect when importing text data files. Defaults to False.
    :type invert: boolean

    :param convexity: The convexity parameter specifies the maximum number of front sides (back sides) a ray intersecting the object might penetrate. This parameter is only needed for correctly displaying the object in OpenCSG preview mode and has no effect on the polyhedron rendering.
    :type convexity: int
    '''
    def __init__(self, file, center=None, convexity=None, invert=None):
        OpenSCADObject.__init__(self, 'surface',
                                {'file': file, 'center': center,
                                 'convexity': convexity, 'invert': invert})


class text(OpenSCADObject):
    '''
    Create text using fonts installed on the local system or provided as separate font file.

    :param text: The text to generate.
    :type text: string

    :param size: The generated text will have approximately an ascent of the given value (height above the baseline). Default is 10.  Note that specific fonts will vary somewhat and may not fill the size specified exactly, usually slightly smaller.
    :type size: number

    :param font: The name of the font that should be used. This is not the name of the font file, but the logical font name (internally handled by the fontconfig library). A list of installed fonts can be obtained using the font list dialog (Help -> Font List).
    :type font: string

    :param halign: The horizontal alignment for the text. Possible values are "left", "center" and "right". Default is "left".
    :type halign: string

    :param valign: The vertical alignment for the text. Possible values are "top", "center", "baseline" and "bottom". Default is "baseline".
    :type valign: string

    :param spacing: Factor to increase/decrease the character spacing.  The default value of 1 will result in the normal spacing for the font, giving a value greater than 1 will cause the letters to be spaced further apart.
    :type spacing: number

    :param direction: Direction of the text flow. Possible values are "ltr" (left-to-right), "rtl" (right-to-left), "ttb" (top-to-bottom) and "btt" (bottom-to-top). Default is "ltr".
    :type direction: string

    :param language: The language of the text. Default is "en".
    :type language: string

    :param script: The script of the text. Default is "latin".
    :type script: string

    :param segments: used for subdividing the curved path segments provided by freetype
    :type segments: int
    '''
    def __init__(self, text, size=None, font=None, halign=None, valign=None,
                 spacing=None, direction=None, language=None, script=None,
                 segments=None):
        OpenSCADObject.__init__(self, 'text',
                                {'text': text, 'size': size, 'font': font,
                                 'halign': halign, 'valign': valign,
                                 'spacing': spacing, 'direction': direction,
                                 'language': language, 'script': script,
                                 'segments': segments})


class child(OpenSCADObject):
    def __init__(self, index=None, vector=None, range=None):
        OpenSCADObject.__init__(self, 'child',
                                {'index': index, 'vector': vector,
                                 'range': range})


class children(OpenSCADObject):
    '''
    The child nodes of the module instantiation can be accessed using the
    children() statement within the module. The number of module children
    can be accessed using the $children variable.

    :param index: select one child, at index value. Index start at 0 and should be less than or equal to $children-1.
    :type index: int

    :param vector: select children with index in vector. Index should be between 0 and $children-1.
    :type vector: sequence of int

    :param range: [:] or [::]. select children between to , incremented by (default 1).
    '''
    def __init__(self, index=None, vector=None, range=None):
        OpenSCADObject.__init__(self, 'children',
                                {'index': index, 'vector': vector,
                                 'range': range})


class import_stl(OpenSCADObject):
    def __init__(self, file, origin=(0, 0), layer=None):
        OpenSCADObject.__init__(self, 'import',
                                {'file': file, 'origin': origin,
                                 'layer': layer})


class import_dxf(OpenSCADObject):
    def __init__(self, file, origin=(0, 0), layer=None):
        OpenSCADObject.__init__(self, 'import',
                                {'file': file, 'origin': origin,
                                 'layer': layer})


class import_(OpenSCADObject):
    '''
    Imports a file for use in the current OpenSCAD model. OpenSCAD currently
    supports import of DXF and STL (both ASCII and Binary) files.

    :param file: path to the STL or DXF file.
    :type file: string

    :param convexity: The convexity parameter specifies the maximum number of front sides (back sides) a ray intersecting the object might penetrate. This parameter is only needed for correctly displaying the object in OpenCSG preview mode and has no effect on the polyhedron rendering.
    :type convexity: int
    '''
    def __init__(self, file, origin=(0, 0), layer=None):
        OpenSCADObject.__init__(self, 'import',
                                {'file': file, 'origin': origin,
                                 'layer': layer})


class intersection_for(OpenSCADObject):
    '''
    Iterate over the values in a vector or range and take an
    intersection of the contents.
    '''
    def __init__(self, n):
        OpenSCADObject.__init__(self, 'intersection_for', {'n': n})


class assign(OpenSCADObject):
    def __init__(self):
        OpenSCADObject.__init__(self, 'assign', {})
