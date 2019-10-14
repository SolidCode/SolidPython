#! /usr/bin/env python3
import sys
from pathlib import Path

from solid import scad_render_to_file
from solid.objects import import_scad, use


# Import OpenSCAD code and call it from Python code.
# The path given to use() or import_scad() must be absolute or findable in sys.path


def demo_import_scad():
    scad_path = Path(__file__).parent / 'scad_to_include.scad'
    scad_mod = import_scad(scad_path)
    return scad_mod.steps(5)


# The `use()` function mimics the behavior of OpenSCAD's use()`
def demo_scad_use():
    # scad_to_include.scad includes a module called steps()
    scad_path = Path(__file__).parent / 'scad_to_include.scad'
    # `This adds the SCAD module `steps()` to the global namespace
    use(scad_path)

    return steps(5)


if __name__ == '__main__':
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    a = demo_import_scad()
    file_out = scad_render_to_file(a, out_dir=out_dir)
    print(f"{__file__}: SCAD file written to: \n{file_out}")
