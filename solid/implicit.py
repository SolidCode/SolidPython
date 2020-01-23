#! /usr/bin/env python
import solid.objects
from solid.solidpython import scad_render_to_file, scad_render
from solid.solidpython import calling_module, OpenSCADObject, PathStr

from textwrap import dedent
from typing import  Dict, Callable

def _implicitcad_patch_objects():
    """
    Usage: 
    `from solid.implicit import *`, (rather than `from solid import *`)
    from solid.implicit import cube, union, square, 
    All other usage should be like normal SolidPython.

    Monkey-patching for basic compatibility with Christopher Olah's ImplicitCAD
    (https://github.com/colah/ImplicitCAD)
    NOTE that this *only* enables `r` arguments to a number of geometry classes.
    ImplicitCAD has a number of other syntax features that are still unsupported,
    notably functions as arguments to some functions. PRs for that are welcome!
    -ETJ 22 January 2020

    """
    to_add_rad = [ 
        'square', 'polygon', 
        'cube',  'polyhedron', 
        'union', 'intersection', 'difference'
    ] # 'cylinder' excluded; it already has an 'r' arg
        
    cur_mod = calling_module(stack_depth=1)

    for cls_name, cls in solid.objects.__dict__.items():
        if cls_name in to_add_rad:
            args_dict_orig = _method_args_dict(cls.__init__)
            args_str_orig = ', '.join(['self'] + [f'{k} = {v}' for k, v in args_dict_orig.items()])
            args_str = ', '.join([args_str_orig, 'r = 0'])
            super_args_str = ', '.join([f'{k} = {k}' for k in args_dict_orig.keys()])

            cls_str = dedent(f'''
            class {cls_name}(solid.objects.{cls_name}):
                def __init__({args_str}):
                    super().__init__({super_args_str})
                    self.params['r'] = r

            ''')
            exec(cls_str)

            cls = locals()[cls_name]

        # Add the class (original or new subclass) to this module's top level namespace
        setattr(cur_mod, cls_name, cls)

def _method_args_dict(method:Callable) -> Dict:
    var_names = method.__code__.co_varnames
    var_names = tuple((v for v in var_names if v is not 'self'))
    default_vals = method.__defaults__ or [None] # type:ignore

    return dict(zip(var_names, default_vals))

def implicitcad_render(scad_object: OpenSCADObject, file_header: str = '') -> str:
    return scad_render(scad_object, file_header)

def implicitcad_render_to_file(scad_object: OpenSCADObject,
                        filepath: PathStr=None, 
                        out_dir: PathStr=None,
                        file_header: str='', 
                        include_orig_code: bool=True) -> str:
    return scad_render_to_file(scad_object, filepath, out_dir, file_header, 
                                include_orig_code, suffix='.escad')
            


_implicitcad_patch_objects()
