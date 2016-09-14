#! /usr/bin/env python
# -*- coding: utf-8 -*-

#    Simple Python OpenSCAD Code Generator
#    Copyright (C) 2009    Philipp Tiefenbacher <wizards23@gmail.com>
#    Amendments & additions, (C) 2011 Evan Jones <evan_t_jones@mac.com>
#
#   License: LGPL 2.1 or later
#
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
    import inspect
    frm = inspect.stack()[stack_depth]
    calling_mod = inspect.getmodule(frm[0])
    # If calling_mod is None, this is being called from an interactive session.
    # Return that module.  (Note that __main__ doesn't have a __file__ attr,
    # but that's caught elsewhere.)
    if not calling_mod:
        import __main__ as calling_mod
    return calling_mod


# these need to be here for now, so that they can access the functions above
from ._builtins import *
from ._parse import *
from ._includes import *
from ._render import *
