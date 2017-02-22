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
        '''
        Provides a copy of this object and all children,
        but doesn't copy self.parent, meaning the new object belongs
        to a different tree
        Initialize an instance of this class with the same params
        that created self, the object being copied.
        '''

        # Python can't handle an '$fn' argument, while openSCAD only wants
        # '$fn'.  Swap back and forth as needed; the final renderer will
        # sort this out.
        if '$fn' in self.params:
            self.params['segments'] = self.params.pop('$fn')

        other = type(self)(**self.params)
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
        return objects.union()(self, x)

    def __sub__(self, x):
        '''
        This makes u = a - b identical to:
        u = difference()(a, b )
        '''
        return objects.difference()(self, x)

    def __mul__(self, x):
        '''
        This makes u = a * b identical to:
        u = intersection()(a, b )
        '''
        return objects.intersection()(self, x)

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

# now that we have the base class defined, we can do a circular import
from . import objects

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
