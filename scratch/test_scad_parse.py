#! /usr/bin/python
# -*- coding: UTF-8 -*-
import os, sys, re
# from pyopenscad import *

sys.path.append('/Users/jonese/Downloads/3D/SCAD/rambo-MCAD-ec568b4/')
# import openscad_utils
module_path = '/Users/jonese/Downloads/3D/SCAD/Libs.scad'

# ===========
# = Parsing =
# ===========
mod_re = (r"\bmodule\s+(", r")\s*\(\s*")
func_re = (r"\bfunction\s+(", r")\s*\(")

def extract_definitions(fpath, name_re=r"\w+", def_re=""):
    regex = name_re.join(def_re)
    matcher = re.compile(regex)
    return (m.group(1) for m in matcher.finditer(fpath.read()))

def extract_mod_names(fpath, name_re=r"\w+"):
    return extract_definitions(fpath, name_re=name_re, def_re=mod_re)

def extract_func_names(fpath, name_re=r"\w+"):
    return extract_definitions(fpath, name_re=name_re, def_re=func_re)

test_str = '''module hex (width=10, height=10,    
 flats= true, center=false){}
    function righty (angle=90) = 1;
    function lefty( avar) = 2;
    module more( a=[something, other]) {}
    module pyramid(side=10, height=-1, square=false, centerHorizontal=true, centerVertical=false){}
'''
def extract_callable_signatures( fpath):
    contents = open(fpath,'r').read()
    contents = test_str
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
    
    
    mod_matches = re.finditer( mod_re, contents)
    
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

sigs =  extract_callable_signatures( '../Libs.scad')
print len(sigs)
for sig in sigs:
    print "%s: \n\targs: %s \n\tkwargs: %s"%(sig['name'], sig['args'], sig['kwargs'])
