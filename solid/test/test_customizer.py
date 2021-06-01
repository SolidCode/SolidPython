#! /usr/bin/env python3
import unittest


from solid import *
from solid.test.solidpython_testcase import SolidPythonTestCase
from solid.customizer import (CustomizerCheckbox, CustomizerDropdownString, 
    CustomizerSlider, CustomizerDropdownNumber, CustomizerSpinbox, CustomizerTextbox,
    CompoundFloat)

class TestCompoundFloat(SolidPythonTestCase):
    def setUp(self):
        self.cf = CompoundFloat(4.0)
        self.slider = CustomizerSlider('slider', 3)

    def testSingleFloat(self):
        a = CompoundFloat(4.0)
        expected = '(4.0)'
        actual = str(a)
        self.assertEqual(expected, actual)
    
    def testSingleInt(self):
        # NOTE CompoundFloat(4.0) has a different string value than CompoundFloat(4)
        # Is this OK?        
        a = CompoundFloat(4)
        expected = '(4)'
        actual = str(a)
        self.assertEqual(expected, actual)

    def testSimpleAdd(self):
        b = CompoundFloat(self.cf, float.__add__, 2.0)
        expected = '((4.0) + 2.0)'
        actual = str(b)
        self.assertEqual(expected, actual)

    def testInfixAdd(self):
        # Confirm that infix operators work with CompoundFloats
        c = self.cf + 3
        expected = '((4.0) + 3)'
        actual = str(c)
        self.assertEqual(expected, actual)

    def testInfixCommutative(self):
        # confirm that infix operators are commutative & stay CompoundFloats
        d = 3 + self.cf
        expected = '((4.0) + 3)'
        actual = str(d)
        self.assertEqual(expected, actual)

    def testCustomizerSubclasses(self):
        # Confirm that CompoundFloat play nicely with Customizer subclasses
        e = CompoundFloat(self.slider, float.__add__, self.cf)
        expected = '(slider + (4.0))'
        actual = str(e)
        self.assertEqual(expected, actual)

    def testCustomizerInfix(self):
        # Confirm that infix operators work with Customizer subclasses
        f = self.slider + 3
        expected = '(slider + 3)'
        actual = str(f)
        self.assertEqual(expected, actual)

    def testUnaryNegative(self):
        # Confirm unary operations work
        g = -self.cf
        expected = '(-1.0 * (4.0))'
        actual = str(g)
        self.assertEqual(expected, actual)

    def testUnaryPositive(self):
        h = +self.cf
        expected = '(4.0)'
        actual = str(h)
        self.assertEqual(expected, actual)

        # Confirm non-commutative operations work
    def testRsub(self):
        i = 1 - self.cf
        expected = '(1.0 - (4.0))'
        actual = str(i)
        self.assertEqual(expected, actual)    

        j = 1 - self.slider
        actual = str(j)
        expected = '(1.0 - slider)'
        self.assertEqual(expected, actual)    

    def testDiv(self):
        j = self.cf/2
        expected = '((4.0) / 2)'
        actual = str(j)
        self.assertEqual(expected, actual)        

        k = self.slider / 2
        expected = '(slider / 2)'
        actual = str(k)
        self.assertEqual(expected, actual)

    def testRdiv(self):
        k = 2 / self.cf
        expected = '(2.0 / (4.0))'
        actual = str(k)
        self.assertEqual(expected, actual)

        l = 2 / self.slider
        expected = '(2.0 / slider)'
        actual = str(l)
        self.assertEqual(expected, actual)


class TestCustomizer(SolidPythonTestCase):
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
        expected = 'cs1 = 0.5; // [0:1] cube(size=[cs1, (cs1*2), (cs1+cs1)]);'
        self.assertEqualOpenScadObject(expected, actual)

        # FIXME: tests for min, max, step

    def testCustomizerDropdownNumber(self):
        cdn = CustomizerDropdownNumber('cdn', 2, [1,2,3])
        actual = cube(cdn)
        expected = 'cdn = 2; // [1,2,3] cube(size=cdn);'
        self.assertEqualOpenScadObject(expected, actual)

        # Make sure math involving customizer values work
        actual = cube(2*cdn)
        expected = 'cdn = 2; // [1,2,3] cube(size=(cdn*2));'
        self.assertEqualOpenScadObject(expected, actual)

        # Make sure labeled dropdowns work
        cdn2 = CustomizerDropdownNumber('cdn2', 2, {2:'a', 3:'b', 4.5:'c'})
        actual = cube(cdn2)
        expected = 'cdn2 = 2; //[2:a,3:b,4.5:c] cube(size=cdn2);'
        self.assertEqualOpenScadObject(expected, actual)

        # And math on labeled dropdowns
        actual = cube(2 * cdn2)
        expected = 'cdn2 = 2; //[2:a,3:b,4.5:c] cube(size=(cdn2*2));'
        self.assertEqualOpenScadObject(expected, actual)

    def testCustomizerSpinbox(self):
        csb = CustomizerSpinbox('csb', 5)
        actual = cube(csb)
        expected = 'csb=5; cube(size=csb);'
        self.assertEqualOpenScadObject(expected, actual)

        # NOTE: we do negative numbers & subtraction in ugly fashion.
        # This lets us do subtraction & division in terms of addition and 
        # multiplication, which are commutative. Maybe there's a more graceful way?
        actual = cube(1-csb)
        expected = 'csb=5; cube(size=(1.0-csb));'
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
