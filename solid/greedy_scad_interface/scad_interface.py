from .scad_variable import ScadVariable, ScadValue

def get_animation_time():
    return ScadValue("$t")

def set_global_fn(_fn):
    ScadVariable("$fn", _fn)

def set_global_fa(_fa):
    ScadVariable("$fa", _fa)

def set_global_fs(_fs):
    ScadVariable("$fs", _fs)

def set_global_viewport_translation(trans):
    ScadVariable("$vpt", trans)

def set_global_viewport_rotation(rot):
    ScadVariable("$vpr", rot)

def set_global_viewport_fov(fov):
    ScadVariable("$vpf", fov)

def set_global_viewport_distance(d):
    ScadVariable("$vpd", d)

def get_scad_header():
    base_str = "\n\n".join(ScadVariable.registered_variables.values())
    return f'{base_str}\n'

