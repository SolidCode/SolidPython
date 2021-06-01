#! /usr/bin/env python3
import unittest
from unittest.case import expectedFailure
from solid.test.ExpandedTestCase import DiffOutput

from solid import *
from solid.customizer import (CustomizerCheckbox, CustomizerDropdownString, 
    CustomizerSlider, CustomizerDropdownNumber, CustomizerSpinbox, CustomizerTextbox)

class TestCustomizer(DiffOutput):
    def testCustomizerCheckbox(self):
        cb = CustomizerCheckbox('cb', True)
        actual = cube(5, center=cb)
        expected = 'cb = true; cube(center=cb, size=5);'
        self.assertEqualOpenScadObject(expected, actual)

    def testCustomizerSlider(self):
        cs1 = CustomizerSlider('cs1', 0.5)
        actual = cube(cs1)
        expected = 'cs1 = 0.5; // [0:1] cube(size=cs1);'
        self.assertEqualOpenScadObject(expected, actual)

        # Make sure math involving customizer values work
        actual = cube([cs1, 2*cs1, cs1 + cs1])
        expected = 'cs1 = 0.5; // [0:1] cube(size=[cs1, 2*cs1, cs1+cs1]);'
        self.assertEqualOpenScadObject(expected, actual)

        # FIXME: tests for min, max, step

    def testCustomizerDropdownNumber(self):
        cdn = CustomizerDropdownNumber('cdn', 2, [1,2,3])
        actual = cube(cdn)
        expected = 'cdn = 2; // [1,2,3] cube(size=cdn);'
        self.assertEqualOpenScadObject(expected, actual)

        # Make sure math involving customizer values work
        actual = cube(2*cdn)
        expected = 'cdn = 2; // [1,2,3] cube(size=(2*cdn));'
        self.assertEqualOpenScadObject(expected, actual)

        # Make sure labeled dropdowns work
        cdn2 = CustomizerDropdownNumber('cdn2', 2, {2:'a', 3:'b', 4.5:'c'})
        actual = cube(cdn2)
        expected = 'cube(size=cdn2);'
        self.assertEqualOpenScadObject(expected, actual)

        # And math on labeled dropdowns
        actual = cube(2**cdn2)
        expected = 'cube(size=(2**cdn2);'
        self.assertEqualOpenScadObject(expected, actual)

    def testCustomizerSpinbox(self):
        csb = CustomizerSpinbox('csb', 5)
        actual = cube(csb)
        expected = 'csb=5; cube(size=csb);'
        self.assertEqualOpenScadObject(expected, actual)

        actual = cube(1-csb)
        expected = 'csb=5; cube(size=(1-csb));'
        self.assertEqualOpenScadObject(expected, actual)

    def testCustomizerDropdownString(self):
        cds = CustomizerDropdownString('cds', 'foo', ['foo', 'bar', 'baz'])
        actual = text(cds)
        expected = 'cds="foo";//[foo,bar,baz] text(text=cds);'
        self.assertEqualOpenScadObject(expected, actual)

        # Test labeled string options
        cds2 = CustomizerDropdownString('cds2', 'S', {'S':'Small', 'M':'Medium', 'L':'Large'})
        actual = text(cds2)
        expected = 'cds2="S"; // [S:Small,M:Medium,L:Large] text(text=cds2);'
        self.assertEqualOpenScadObject(expected, actual)

    def testCustomizerTextbox(self):
        ctb = CustomizerTextbox('ctb', 'hello')
        actual = text(ctb)
        expected = 'ctb="hello"; text(text=ctb);'
        self.assertEqualOpenScadObject(expected, actual)


if __name__ == '__main__':
    unittest.main()