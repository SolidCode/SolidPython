#! /usr/bin/env python
import unittest
import re

from solid.screw_thread import default_thread_section, thread
from solid.solidpython import scad_render
from solid.test.ExpandedTestCase import DiffOutput

SEGMENTS = 4

class TestScrewThread(DiffOutput):
    def setUp(self):
        self.tooth_height = 10
        self.tooth_depth = 5
        self.outline = default_thread_section(tooth_height=self.tooth_height, tooth_depth=self.tooth_depth)

    def assertEqualNoWhitespace(self, a, b):
        remove_whitespace = lambda s: re.subn(r'[\s\n]','', s)[0]
        self.assertEqual(remove_whitespace(a), remove_whitespace(b))

    def test_thread(self):
        actual_obj = thread(outline_pts=self.outline,
                            inner_rad=20,
                            pitch=self.tooth_height,
                            length=0.75 * self.tooth_height,
                            segments_per_rot=SEGMENTS,
                            neck_in_degrees=45,
                            neck_out_degrees=45)

        actual = scad_render(actual_obj)
        expected = '''intersection(){
            polyhedron(
                convexity=2,
                faces=[[0,1,3],[1,4,3],[1,2,4],[2,5,4],[0,5,2],[0,3,5],[3,4,6],[4,7,6],[4,5,7],[5,8,7],[3,8,5],[3,6,8],[6,7,9],[7,10,9],[7,8,10],[8,11,10],[6,11,8],[6,9,11],[0,2,1],[9,10,11]],
                points=[[14.9900000000,0.0000000000,-5.0000000000],[19.9900000000,0.0000000000,0.0000000000],[14.9900000000,0.0000000000,5.0000000000],[0.0000000000,20.0000000000,-2.5000000000],[0.0000000000,25.0000000000,2.5000000000],[0.0000000000,20.0000000000,7.5000000000],[-20.0000000000,0.0000000000,0.0000000000],[-25.0000000000,0.0000000000,5.0000000000],[-20.0000000000,0.0000000000,10.0000000000],[-0.0000000000,-14.9900000000,2.5000000000],[-0.0000000000,-19.9900000000,7.5000000000],[-0.0000000000,-14.9900000000,12.5000000000]]
            );
            difference(){
                cylinder($fn=4,h=7.5000000000,r1=25.0100000000,r2=25.0100000000);
                cylinder($fn=4,h=7.5000000000,r1=20,r2=20);
            }
        }'''
        self.assertEqualNoWhitespace(expected, actual)

    def test_thread_internal(self):
        actual_obj = thread(outline_pts=self.outline,
                            inner_rad=20,
                            pitch=2 * self.tooth_height,
                            length=2 * self.tooth_height,
                            segments_per_rot=SEGMENTS,
                            neck_in_degrees=45,
                            neck_out_degrees=45,
                            external=False)
        actual = scad_render(actual_obj)
        expected = '''intersection() {
            polyhedron(
                convexity=2,
                faces = [[0, 1, 3], [1, 4, 3], [1, 2, 4], [2, 5, 4], [0, 5, 2], [0, 3, 5], [3, 4, 6], [4, 7, 6], [4, 5, 7], [5, 8, 7], [3, 8, 5], [3, 6, 8], [6, 7, 9], [7, 10, 9], [7, 8, 10], [8, 11, 10], [6, 11, 8], [6, 9, 11], [9, 10, 12], [10, 13, 12], [10, 11, 13], [11, 14, 13], [9, 14, 11], [9, 12, 14], [0, 2, 1], [12, 13, 14]], 
                points = [[25.0100000000, 0.0000000000, 5.0000000000], [20.0100000000, 0.0000000000, 0.0000000000], [25.0100000000, 0.0000000000, -5.0000000000], [0.0000000000, 20.0000000000, 10.0000000000], [0.0000000000, 15.0000000000, 5.0000000000], [0.0000000000, 20.0000000000, 0.0000000000], [-20.0000000000, 0.0000000000, 15.0000000000], [-15.0000000000, 0.0000000000, 10.0000000000], [-20.0000000000, 0.0000000000, 5.0000000000], [-0.0000000000, -20.0000000000, 20.0000000000], [-0.0000000000, -15.0000000000, 15.0000000000], [-0.0000000000, -20.0000000000, 10.0000000000], [25.0100000000, -0.0000000000, 25.0000000000], [20.0100000000, -0.0000000000, 20.0000000000], [25.0100000000, -0.0000000000, 15.0000000000]]
            );
            cylinder($fn = 4, h = 20, r1 = 20, r2 = 20);
        }'''
        self.assertEqualNoWhitespace(expected, actual)

    def test_conical_thread_external(self):
        actual_obj = thread(outline_pts=self.outline,
                            inner_rad=20,
                            rad_2 = 40,
                            pitch=self.tooth_height,
                            length=0.75 * self.tooth_height,
                            segments_per_rot=SEGMENTS,
                            neck_in_degrees=45,
                            neck_out_degrees=45,
                            external=True)
        actual = scad_render(actual_obj)
        expected = '''intersection(){
            polyhedron(convexity=2,
                faces=[[0,1,3],[1,4,3],[1,2,4],[2,5,4],[0,5,2],[0,3,5],[3,4,6],[4,7,6],[4,5,7],[5,8,7],[3,8,5],[3,6,8],[6,7,9],[7,10,9],[7,8,10],[8,11,10],[6,11,8],[6,9,11],[0,2,1],[9,10,11]],
                points=[[5.9450623365,0.0000000000,-1.7556172079],[12.3823254323,0.0000000000,-4.6816458878],[15.3083541122,0.0000000000,1.7556172079],[0.0000000000,21.9850207788,0.7443827921],[0.0000000000,28.4222838746,-2.1816458878],[0.0000000000,31.3483125545,4.2556172079],[-28.6516874455,0.0000000000,3.2443827921],[-35.0889505413,0.0000000000,0.3183541122],[-38.0149792212,0.0000000000,6.7556172079],[-0.0000000000,-25.9450623365,5.7443827921],[-0.0000000000,-32.3823254323,2.8183541122],[-0.0000000000,-35.3083541122,9.2556172079]]
            );
            difference(){
                cylinder($fn=4,h=7.5000000000,r1=29.3732917757,r2=49.3732917757);
                cylinder($fn=4,h=7.5000000000,r1=20,r2=40);
            }
        }'''
        self.assertEqualNoWhitespace(expected, actual)

    def test_conical_thread_internal(self):
        actual_obj = thread(outline_pts=self.outline,
                            inner_rad=20,
                            rad_2 = 40,
                            pitch=self.tooth_height,
                            length=0.75 * self.tooth_height,
                            segments_per_rot=SEGMENTS,
                            neck_in_degrees=45,
                            neck_out_degrees=45,
                            external=False)
        actual = scad_render(actual_obj)
        expected = '''intersection(){
            polyhedron(
                convexity=2,
                faces=[[0,1,3],[1,4,3],[1,2,4],[2,5,4],[0,5,2],[0,3,5],[3,4,6],[4,7,6],[4,5,7],[5,8,7],[3,8,5],[3,6,8],[6,7,9],[7,10,9],[7,8,10],[8,11,10],[6,11,8],[6,9,11],[0,2,1],[9,10,11]],
                points=[[34.0549376635,0.0000000000,1.7556172079],[27.6176745677,0.0000000000,4.6816458878],[24.6916458878,0.0000000000,-1.7556172079],[0.0000000000,31.3483125545,4.2556172079],[0.0000000000,24.9110494587,7.1816458878],[0.0000000000,21.9850207788,0.7443827921],[-38.0149792212,0.0000000000,6.7556172079],[-31.5777161254,0.0000000000,9.6816458878],[-28.6516874455,0.0000000000,3.2443827921],[-0.0000000000,-54.0549376635,9.2556172079],[-0.0000000000,-47.6176745677,12.1816458878],[-0.0000000000,-44.6916458878,5.7443827921]]
            );
            cylinder($fn=4,h=7.5000000000,r1=20,r2=40);
        }'''
        self.assertEqualNoWhitespace(expected, actual)

    def test_default_thread_section(self):
        expected = [[0, -5], [5, 0], [0, 5]]
        actual = default_thread_section(tooth_height=10, tooth_depth=5)
        self.assertEqual(expected, actual)

    def test_neck_in_out_degrees(self):
        # Non-specified neck_in_degrees and neck_out_degrees would crash prior
        # to the fix for https://github.com/SolidCode/SolidPython/issues/92
        actual_obj = thread(outline_pts=self.outline,
                            inner_rad=20,
                            pitch=self.tooth_height,
                            length=0.75 * self.tooth_height,
                            segments_per_rot=SEGMENTS,
                            neck_in_degrees=45,
                            neck_out_degrees=0)
        actual = scad_render(actual_obj)
        expected = '''intersection(){
            polyhedron(
                convexity=2,
                faces=[[0,1,3],[1,4,3],[1,2,4],[2,5,4],[0,5,2],[0,3,5],[3,4,6],[4,7,6],[4,5,7],[5,8,7],[3,8,5],[3,6,8],[6,7,9],[7,10,9],[7,8,10],[8,11,10],[6,11,8],[6,9,11],[0,2,1],[9,10,11]],
                points=[[14.9900000000,0.0000000000,-5.0000000000],[19.9900000000,0.0000000000,0.0000000000],[14.9900000000,0.0000000000,5.0000000000],[0.0000000000,20.0000000000,-2.5000000000],[0.0000000000,25.0000000000,2.5000000000],[0.0000000000,20.0000000000,7.5000000000],[-20.0000000000,0.0000000000,0.0000000000],[-25.0000000000,0.0000000000,5.0000000000],[-20.0000000000,0.0000000000,10.0000000000],[-0.0000000000,-20.0000000000,2.5000000000],[-0.0000000000,-25.0000000000,7.5000000000],[-0.0000000000,-20.0000000000,12.5000000000]]
            );
            difference(){
                cylinder($fn=4,h=7.5000000000,r1=25.0100000000,r2=25.0100000000);
                cylinder($fn=4,h=7.5000000000,r1=20,r2=20);
            }
        }'''
        self.assertEqualNoWhitespace(expected, actual)


if __name__ == '__main__':
    unittest.main()
