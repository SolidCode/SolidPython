#! /usr/bin/python
# -*- coding: utf-8 -*-
import sys, os

from solid import *

# Import OpenSCAD code and call it from Python code.
# Note that the path given to use() (or include())
# must either be absolute or relative to the directory
# this python file is run from.
use( "./scad_to_include.scad") #  could also use 'include', but that has side-effects

print scad_render( steps(5))