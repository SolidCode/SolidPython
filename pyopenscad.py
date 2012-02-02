#! /usr/bin/python
# -*- coding: UTF-8 -*-

#    Simple Python OpenSCAD Code Generator
#    Copyright (C) 2009    Philipp Tiefenbacher <wizards23@gmail.com>
#    Amendments & additions, (C) 2011 Evan Jones <evan_t_jones@mac.com>
#
#   License: LGPL 2.1 or later
#


import os, sys, re
import inspect

openscad_builtins = [
    # 2D primitives
    {'name': 'polygon',         'args': ['points', 'paths'], 'kwargs': []} ,
    {'name': 'circle',          'args': [],         'kwargs': ['r']} ,
    {'name': 'square',          'args': [],         'kwargs': ['size', 'center']} ,
    
    # 3D primitives
    {'name': 'sphere',          'args': [],         'kwargs': ['r']} ,
    {'name': 'cube',            'args': [],         'kwargs': ['size', 'center']} ,
    {'name': 'cylinder',        'args': [],         'kwargs': ['r','h','r1', 'r2', 'center']}  ,
    {'name': 'polyhedron',      'args': ['points', 'triangles' ], 'kwargs': ['convexity']} ,
    
    # Boolean operations
    {'name': 'union',           'args': [],         'kwargs': []} ,
    {'name': 'intersection',    'args': [],         'kwargs': []} ,
    {'name': 'difference',      'args': [],         'kwargs': []} ,
    
    # Transforms
    {'name': 'translate',       'args': [],         'kwargs': ['v']} ,
    {'name': 'scale',           'args': [],         'kwargs': ['v']} ,
    {'name': 'rotate',          'args': [],         'kwargs': ['a', 'v']} ,
    {'name': 'mirror',          'args': ['normal'], 'kwargs': []},
    {'name': 'multmatrix',      'args': ['n'],      'kwargs': []},
    {'name': 'color',           'args': ['c'],      'kwargs': []},
    {'name': 'minkowski',       'args': [],         'kwargs': []}  ,
    {'name': 'render',          'args': [],         'kwargs': ['convexity']}, 
        
    # 2D to 3D transitions
    {'name': 'linear_extrude',  'args': [],         'kwargs': ['height', 'center', 'convexity', 'twist','slices']} ,
    {'name': 'rotate_extrude',  'args': [],         'kwargs': ['convexity']} ,
    {'name': 'dxf_linear_extrude', 'args': ['file'], 'kwargs': ['layer', 'height', 'center', 'convexity', 'twist', 'slices']} ,
    {'name': 'projection',      'args': [],         'kwargs': ['cut']} ,
    
    # Import/export
    {'name': 'import_stl',      'args': ['filename'], 'kwargs': ['convexity']} ,
    
    # Modifiers; These are implemented by calling e.g. 
    #   obj.set_modifier( '*') or 
    #   obj.set_modifier('disable') 
    # on  an existing object.
    # {'name': 'background',      'args': [],         'kwargs': []},     #   %{}
    # {'name': 'debug',           'args': [],         'kwargs': []} ,    #   #{}
    # {'name': 'root',            'args': [],         'kwargs': []} ,    #   !{}
    # {'name': 'disable',         'args': [],         'kwargs': []} ,    #   *{}
    
    {'name': 'intersection_for', 'args': ['n'],     'kwargs': []}  ,    #   e.g.: intersection_for( n=[1..6]){}
    
    # Unneeded
    {'name': 'assign',          'args': [],         'kwargs': []}   # Not really needed for Python.  Also needs a **args argument so it accepts anything
]

# Some functions need custom code in them; put that code here
builtin_literals = {
    'circle': '''class circle( openscad_object):
        def __init__( self, r, segments=None):
            if segments:
                openscad_object.__init__(self, 'circle', {'r': r, '$fn': segments})
            else:
                openscad_object.__init__(self, 'circle', {'r': r, })
    
''',
    'polygon': '''class polygon( openscad_object):
        def __init__( self, points, paths=None):
            if not paths:
                paths = [ range( len( points))]
            openscad_object.__init__( self, 'polygon', {'points':points, 'paths': paths})
'''

}

# ===============
# = Including OpenSCAD code =
# ===============
def use( scad_file_path, use_not_include=True):
    '''
    FIXME:  doctest needed
    '''
    # Opens scad_file_path, parses it for all usable calls, 
    # and adds them to caller's namespace
    
    # TODO: add something along the lines of PYTHONPATH for scad files?
    # That way you could 'use( a_file.scad)' without using an absolute
    # path or having the library in the same directory
    try:
        module = open( scad_file_path)
        contents = module.read()
        module.close()
    except Exception, e:
        raise Exception( "Failed to import SCAD module '%(scad_file_path)s' with error: %(e)s "%vars())
    
    # Once we have a list of all callables and arguments, dynamically
    # add openscad_object subclasses for all callables to the calling module's
    # namespace.
    symbols_dicts = extract_callable_signatures( scad_file_path)
    
    for sd in symbols_dicts:
        class_str = new_openscad_class_str( sd['name'], sd['args'], sd['kwargs'], scad_file_path, use_not_include)
        exec class_str in calling_module().__dict__
    
    return True

def include( scad_file_path):
    return use( scad_file_path, use_not_include=False)


# =========================================
# = Rendering Python code to OpenSCAD code=
# =========================================
def scad_render( scad_object, file_header=''):
    # Find the root of the tree, calling x.parent until there is none
    root = scad_object
    
    # Scan the tree for all instances of 
    # included_openscad_object, storing their strings
    def find_include_strings( obj):
        include_strings = set()
        if isinstance( obj, included_openscad_object):
            include_strings.add( obj.include_string )
        for child in obj.children:
            include_strings.update( find_include_strings( child))
        return include_strings
    
    include_strings = find_include_strings( root)
    
    # and render the string
    includes = ''.join(include_strings) + "\n"
    scad_body = root._render()
    return file_header + includes + scad_body

def scad_render_to_file( scad_object, filepath=None, file_header='', include_orig_code=False):
    rendered_string = scad_render( scad_object, file_header)
    
    calling_file = os.path.abspath( calling_module().__file__) 
    
    if include_orig_code:
        # Once a SCAD file has been created, it's difficult to reconstruct
        # how it got there, since it has no variables, modules, etc.  So, include
        # the Python code that generated the scad code as comments at the end of 
        # the SCAD code
        pyopenscad_str = open(calling_file, 'r').read()
    
        pyopenscad_str = '''
/***********************************************
******      PyOpenSCAD code:       *************
************************************************
 
%(pyopenscad_str)s 
 
***********************************************/
                            
'''%vars()        
        rendered_string += pyopenscad_str
    
    # This write is destructive, and ought to do some checks that the write
    # was successful.
    # If filepath isn't supplied, place a .scad file with the same name
    # as the calling module next to it
    if not filepath:
        filepath = os.path.splitext( calling_file)[0] + '.scad'
    
    f = open( filepath,"w")
    f.write( rendered_string)
    f.close


# =========================
# = Internal Utilities    =
# =========================
class openscad_object( object):
    def __init__(self, name, params):
        self.name = name
        self.params = params
        self.children = []
        self.modifier = ""
        self.parent= None
    
    def set_modifier(self, m):
        # Used to add one of the 4 single-character modifiers: #(debug)  !(root) %(background) or *(disable)
        string_vals = { 'disable':      '*',
                        'debug':        '#',
                        'background':   '%',
                        'root':         '!',
                        '*':'*',
                        '#':'#',
                        '%':'%',
                        '!':'!'}
         
        self.modifier = string_vals.get(m.lower(), '')
        return self
    
    def _render(self):
        '''
        NOTE: In general, you won't want to call this method. For most purposes,
        you really want scad_render(), 
        Calling obj._render won't include necessary 'use' or 'include' statements
        '''        
        s = "\n" + self.modifier + self.name + "("
        first = True
        
        valid_keys = self.params.keys()
        
        # intkeys are the positional parameters
        intkeys = filter(lambda x: type(x)==int, valid_keys)
        intkeys.sort()
        
        # named parameters
        nonintkeys = filter(lambda x: not type(x)==int, valid_keys)
        
        for k in intkeys+nonintkeys:
            v = self.params[k]
            if v == None:
                continue
            
            if not first:
                s += ", "
            first = False
            
            if type(k)==int:
                s += py2openscad(v)
            else:
                s += k + " = " + py2openscad(v)
                
        s += ")"
        if self.children != None and len(self.children) > 0:
            s += " {"
            for child in self.children:
                s += indent(child._render())
            s += "\n}"
        else:
            s += ";"
        return s
    
    def add(self, child):
        '''
        if child is a single object, assume it's an openscad_object and 
        add it to self.children
        
        if child is a list, assume its members are all openscad_objects and
        add them all to self.children
        '''
        if isinstance( child, list) or isinstance( child, tuple):
            [self.add( c) for c in child]
        else:
            self.children.append(child)
            child.set_parent( self)
        return self
    
    def set_parent( self, parent):
        self.parent = parent
    
    def add_param(self, k, v):
        self.params[k] = v
        return self
    
    def copy( self):
        # Provides a copy of this object and all children, 
        # but doesn't copy self.parent, meaning the new object belongs
        # to a different tree
        other = openscad_object( self.name, self.params)
        for c in self.children:
            other.add( c.copy())
        return other
    
    def __call__( self, *args):
        '''
        Adds all objects in args to self.  This enables OpenSCAD-like syntax,
        e.g.:
        union()(
            cube()
            sphere()
        )
        '''
        return self.add(args)
    
    def __add__(self, x):
        '''
        This makes u = a+b identical to:
        union()( a, b )
        '''
        return union()(self, x)
    
    def __sub__(self, x):
        '''
        This makes u = a - b identical to:
        difference()( a, b )
        '''        
        return difference()(self, x)
    
    def __mul__(self, x):
        '''
        This makes u = a * b identical to:
        intersection()( a, b )
        '''        
        return intersection()(self, x)
    

class included_openscad_object( openscad_object):
    '''
    Identical to openscad_object, but each subclass of included_openscad_object
    represents imported scad code, so each instance needs to store the path
    to the scad file it's included from.
    '''
    def __init__( self, name, params, include_file_path, use_not_include=False):
        self.include_file_path = include_file_path
        if use_not_include:
            self.include_string = 'use <%s>\n'%self.include_file_path
        else:
            self.include_string = 'include <%s>\n'%self.include_file_path
        
        openscad_object.__init__( self, name, params)
    


def calling_module():
    '''
    Returns the module *2* back in the frame stack.  That means:
    code in module A calls code in module B, which asks calling_module()
    for module A.
    
    Got that?
    '''
    frm = inspect.stack()[2]
    calling_mod = inspect.getmodule( frm[0])
    return calling_mod

def new_openscad_class_str( class_name, args=[], kwargs=[], include_file_path=None, use_not_include=True):
    args_str = ''
    args_pairs = ''
    
    for arg in args:
        args_str += ', '+arg
        args_pairs += "'%(arg)s':%(arg)s, "%vars()
        
    # kwargs have a default value defined in their SCAD versions.  We don't 
    # care what that default value will be (SCAD will take care of that), just
    # that one is defined.
    for kwarg in kwargs:
        args_str += ', %(kwarg)s=None'%vars()
        args_pairs += "'%(kwarg)s':%(kwarg)s, "%vars()
        
    if include_file_path:
        result = '''class %(class_name)s( included_openscad_object):
        def __init__(self%(args_str)s):
            included_openscad_object.__init__(self, '%(class_name)s', {%(args_pairs)s }, include_file_path='%(include_file_path)s', use_not_include=%(use_not_include)s )
        
'''%vars()
    else:
        result = '''class %(class_name)s( openscad_object):
        def __init__(self%(args_str)s):
            openscad_object.__init__(self, '%(class_name)s', {%(args_pairs)s })
        
'''%vars()
    return result

def py2openscad(o):
    if type(o) == bool:
        return str(o).lower()
    if type(o) == float:
        return "%.10f" % o
    if type(o) == list:
        s = "["
        first = True
        for i in o:
            if not first:
                s +=    ", "
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
def extract_callable_signatures( scad_file_path):
    scad_code_str = open(scad_file_path).read()
    return parse_scad_callables( scad_code_str)

def parse_scad_callables( scad_code_str):
    """
    >>> test_str = '''module hex (width=10, height=10,    
...  flats= true, center=false){}
...     function righty (angle=90) = 1;
...     function lefty( avar) = 2;
...     module more( a=[something, other]) {}
...     module pyramid(side=10, height=-1, square=false, centerHorizontal=true, centerVertical=false){}
... '''
>>> parse_scad_callables( test_str)
[{'args': [], 'name': 'hex', 'kwargs': ['width', 'height', 'flats', 'center']}, {'args': [], 'name': 'righty', 'kwargs': ['angle']}, {'args': ['avar'], 'name': 'lefty', 'kwargs': []}, {'args': [], 'name': 'more', 'kwargs': ['a']}, {'args': [], 'name': 'pyramid', 'kwargs': ['side', 'height', 'square', 'centerHorizontal', 'centerVertical']}]
    """
    callables = []
    
    # Note that this isn't comprehensive; tuples or comments in a module definition
    # will defeat it.  Functions/modules that have been commented out will also be included, 
    # which will cause errors if multiple versions of a callable exist in the file: e.g
    # function a( x, y) = x+y;
    # /*
    # function a( x) = x+3;
    # */
    
    # Current implementation would throw an error if you tried to call a(x, y) since Python would 
    # expect a( x); 
    
    # TODO:  write a pyparsing grammar for OpenSCAD, or, even better, use the yacc parse grammar
    # used by the language itself.  -ETJ 06 Feb 2011
    
    # Also note: this accepts: 'module x(arg) =' and 'function y(arg) {', both of which are incorrect syntax
    mod_re  = r'(?mxs)^\s*(?:module|function)\s+(?P<callable_name>\w+)\s*\((?P<all_args>.*?)\)\s*(?:{|=)'
    
    # This is brittle.  To get a generally applicable expression for all arguments,
    # we'd need a real parser to handle nested-list default args or parenthesized statements.  
    # For the moment, assume a maximum of one square-bracket-delimited list 
    args_re = r'(?mxs)(?P<arg_name>\w+)(?:\s*=\s*(?P<default_val>[\w-]+|\[.*\]))?(?:,|$)'
    
    
    mod_matches = re.finditer( mod_re, scad_code_str)
    
    for m in mod_matches:
        callable_name = m.group('callable_name')
        args = []
        kwargs = []        
        all_args = m.group('all_args')
        if all_args:
            arg_matches = re.finditer( args_re, all_args)
            for am in arg_matches:
                arg_name = am.group('arg_name')
                if am.group('default_val'):
                    kwargs.append( arg_name)
                else:
                    args.append( arg_name)
        
        callables.append( { 'name':callable_name, 'args': args, 'kwargs':kwargs})
        
    return callables


# Dynamically add all builtins to this namespace on import
for sym_dict in openscad_builtins:
    # entries in 'builtin_literals' override the entries in 'openscad_builtins'
    if sym_dict['name'] in builtin_literals:
        class_str = builtin_literals[ sym_dict['name']]
    else:
        class_str = new_openscad_class_str( sym_dict['name'], sym_dict['args'], sym_dict['kwargs'])
    
    exec class_str 
    

