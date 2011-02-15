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
    {'name': 'cylinder',        'args': [],         'kwargs': ['r','h']}  ,
    {'name': 'polyhedron',      'args': ['points', 'triangles' ], 'kwargs': ['convexity']} ,
    
    # Boolean operations
    {'name': 'union',           'args': [],         'kwargs': []} ,
    {'name': 'intersection',    'args': [],         'kwargs': []} ,
    {'name': 'difference',      'args': [],         'kwargs': []} ,
    
    # Transforms
    {'name': 'translate',       'args': [],         'kwargs': ['v']} ,
    {'name': 'scale',           'args': [],         'kwargs': ['s']} ,
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
        raise( "Failed to import SCAD module '%(scad_file_path)s' with error: %(e)s "%vars())
        
    # Once we have a list of all callables and arguments, dynamically
    # add openscad_object subclasses for all callables to the calling module's
    # namespace.
    symbols_dicts = extract_callable_signatures( scad_file_path)
    frm = inspect.stack()[1]
    calling_module = inspect.getmodule(frm[0])    
    
    for sd in symbols_dicts:
        class_str = new_openscad_class_str( sd['name'], sd['args'], sd['kwargs'], scad_file_path, use_not_include)
        exec class_str in calling_module.__dict__
    
    return True

def include( scad_file_path):
    return use( scad_file_path, use_not_include=False)


# =========================================
# = Rendering Python code to OpenSCAD code=
# =========================================
def scad_render( scad_object):
    # FIXME: If all this explanation is needed, why not just make o.render() private
    # so people aren't tempted to use it?
    
    # NOTE:  scad_render renders an entire TREE of objects, not just scad_object.
    # This is necessary to enable include/use behavior and lets you just render what you've
    # done without having to keep track of the root of your SCAD tree.  
    # If you want to render JUST one object's scad, call scad_obj.render()
    # e.g.:
    # You've defined some geometry in Python:
    #   t = union()
    #   r = rect( 10)
    #   c = circle( 20)
    #   t.add(r)
    #   t.add(c)
    
    #   # Render the whole scene:
    #   whole_scene_scad = scad_render(c)
    #   # ONLY the circle's scad code
    #   just_circle = c.render()
    
    # Also note that o.render() will only work 100% for  SCAD-native objects you've defined.
    # For scad code you've use()d or include()d, you'll have to call scad_render( o)
    # to get the correct include messages back in the rendered scad code. 
    
    
    # Find the root of the tree, calling x.parent until there is none
    root = scad_object
    while root.parent:
        root = root.parent
    
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
    scad_body = root.render()
    return includes + scad_body

def scad_render_to_file( scad_object, filepath):
    rendered_string = scad_render( scad_object)
    # This write is destructive, and ought to do some checks that the write
    # was successful.
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
        self.special_vars = {}
    
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
    
    def render(self):
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
                s += indent(child.render())
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
            
            # self.children.extend( child)
            # [c.set_parent(self) for c in child]
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
    class_str = new_openscad_class_str( sym_dict['name'], sym_dict['args'], sym_dict['kwargs'])
    exec class_str 

       

