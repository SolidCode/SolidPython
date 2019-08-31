#! /usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from pathlib import Path

from solid import *

# Import OpenSCAD code and call it from Python code.
# The path given to use() or import_scad() must be absolute or findable in sys.path

def demo_import_scad():
    scad_path = Path(__file__).parent / 'scad_to_include.scad'
    scad_mod = import_scad(scad_path)
    a = scad_mod.steps(5)
    return a

# The `use()` function mimics the bahavior of OpenSCAD's use()`
def demo_scad_use():
    # scad_to_include.scad includes a module called steps()
    scad_path = Path(__file__).parent / 'scad_to_include.scad'
    # `This adds the SCAD module `steps()` to the global namespace
    use(scad_path)  

    a = steps(5)
    return a

if __name__ == '__main__':
    this_file = Path(__file__)
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else this_file.parent
    file_out = out_dir / this_file.with_suffix('.scad').name
    a = demo_import_scad()

    print(f"{__file__}: SCAD file written to: \n{file_out}")

    scad_render_to_file(a, file_out)
