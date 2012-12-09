#! /usr/bin/python
# -*- coding: utf-8 -*-
import sys, os

from solid import *


# NOTE: Insert the path to the MCAD (or other SCAD) library here.
use( "/Path/To/MCAD/stepper.scad") #  could also use 'include', but that has side-effects

print scad_render( motor())