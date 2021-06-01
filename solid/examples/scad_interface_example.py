from solid import *

scad = ScadInterface()

scad.set_global_var("$fn", 6)

scad.register_customizer_var("cyl_pos", "[1, 2, 3]")

cube_pos = scad.get("cyl_pos")

c = translate(cube_pos) (
        cylinder(r=scad.inline("$t * 3"), h=scad.inline("$t * 10"))
    )

scad_render_to_file(c, scad_interface=scad)
