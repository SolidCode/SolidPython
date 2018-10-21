import numpy as np
import solid
from IPython.display import display
from ipywidgets import HTML, Text, Output, VBox
from traitlets import link, dlink
import math as pymath, os, time, subprocess
from pythreejs import *
from IPython.display import display

OBJ_COLOR = '#f7d62c'
BACKGROUND_COLOR = '#ffffff'

class SolidRenderer:
    '''This class will render an OpenSCAD object within a jupyter notebook.  
    pythreejs must be installed (see directions at https://github.com/jupyter-widgets/pythreejs).
    This class needs to know the path to the openscad command-line tool, and a path of a temp directory.  
    You can set these locations with the OPENSCAD_EXEC and OPENSCAD_TMP_DIR environment variables,
    or you can set the "openscadExec" and openscadTmpDir keyword options in the constructor.
    '''
    def __init__(self, **kw):
        self.openscadExec = 'openscad'
        self.openscadTmpDir = '/tmp'
        if 'OPENSCAD_EXEC' in os.environ: self.openscadExec = os.environ['OPENSCAD_EXEC']
        if 'OPENSCAD_TMP_DIR' in os.environ: self.openscadTmpDir = os.environ['OPENSCAD_TMP_DIR']
        if 'openscadExec' in kw: self.openscadExec = kw['openscadExec']
        if 'openscadTmpDir' in kw: self.openscadTmpDir = kw['openscadTmpDir']
        self.width = kw.get('width', 600)
        self.height = kw.get('height', 600)
        self.drawGrids = kw.get('drawGrids', True)
             
    def _convSTL(self, stlFName):
        fl = open(stlFName)
        faces = []
        vertices = []
        vertStrToIndex = {}
        ind = 0
        for ln in fl:
            if ln.find('outer loop') >= 0:
                curFace = []
            elif ln.find('vertex') >= 0:
                vertStr = ln.split('vertex ')[-1]
                if vertStr not in vertStrToIndex:
                    vertStrToIndex[vertStr] = ind
                    vertices.append([float(x) for x in vertStr.split()])
                    vInd = ind
                    ind += 1
                else:
                    vInd = vertStrToIndex[vertStr]
                curFace.append(vInd)
            elif ln.find('endloop') >= 0:
                faces.append(curFace)

        return vertices, faces

    

    def _getExtents(self, vertices):
        extents = []
        for i in range(3):
            coords = [vertex[i] for vertex in vertices]
            extents.append([min(coords), max(coords)])
        return extents


    def _getGridLines(self, axis1, start, step, N, axis2, start2, end2):
        w = start
        vertices = []
        for i in range(N):
            pt1 = [0, 0, 0]
            pt1[axis1] = start + i * step
            pt1[axis2] = start2
            pt2 = [0, 0, 0]
            pt2[axis1] = start + i * step
            pt2[axis2] = end2
            vertices.append(pt1)
            vertices.append(pt2)
        return vertices
    
    def _getGrids(self, objVertices):
        extents = self._getExtents(objVertices)
        gridVerts = []
        deltas = [extent[1] - extent[0] for extent in extents]
        maxExtent = max(deltas)
        space = 10.0**pymath.floor(pymath.log(maxExtent) / pymath.log(10.0) - 0.5)
        N = int(pymath.floor(maxExtent / space + 2.0))
        gridCols = []
        axisCols = ['#ff3333', '#33ff33', '#3333ff']
        for axis1 in range(3):
            for axis2 in range(3):
                axis3 = [x for x in [0,1,2] if x not in [axis1, axis2]][0]
                if axis1 == axis2: continue
                delta = extents[axis1][1] - extents[axis1][0]
                start = pymath.floor(extents[axis1][0] / space) * space        
                start2 = pymath.floor(extents[axis2][0] / space) * space 
                end2 = start2 + (N - 1) * space
                verts = self._getGridLines(axis1, start, space, N, axis2, start2, end2)
                gridVerts.extend(verts)
                gridCols.extend([axisCols[axis3] for vert in verts])

            
        linesgeom = Geometry(vertices=gridVerts, colors =gridCols)
        lines = LineSegments(geometry=linesgeom, 
                 material=LineDashedMaterial(linewidth=5, dashSize=10, gapSize=10, vertexColors='VertexColors'), 
                 type='LinePieces',
                )
        return lines
    
    def _getTmpFilePrefix(self):
        t = int(time.time() * 1000)
        prefix = '{}/tmp_{}'.format(self.openscadTmpDir, t)
        return prefix

    def render(self, pyScadObj):
        openscadTmpFile = self._getTmpFilePrefix() + '.scad'
        solid.scad_render_to_file(pyScadObj, openscadTmpFile)
        # now run openscad to generate stl:
        stlTmpFile = self._getTmpFilePrefix() + '.stl'
        cmd = [self.openscadExec, '-o', stlTmpFile, openscadTmpFile]
        returncode = subprocess.call(cmd)
        if returncode < 0:
            raise Exception('openscad command line returned code {}'.format(returncode))
            
        self._renderSTL(stlTmpFile)
        
        # clean up the tmp files:
        subprocess.call(['rm', openscadTmpFile])
        subprocess.call(['rm', stlTmpFile])
        
    def _renderSTL(self, stlFile):
        vertices, faces = self._convSTL(stlFile)
        
        # Map the vertex colors into the 'color' slot of the faces
        faces = [f + [None, [OBJ_COLOR for i in f], None] for f in faces]

        # Create the geometry:
        objGeometry = Geometry(vertices=vertices,
            faces=faces, colors = [OBJ_COLOR]*len(vertices))
        # Calculate normals per face, for nice crisp edges:
        objGeometry.exec_three_obj_method('computeFaceNormals')

        # Create a mesh. Note that the material need to be told to use the vertex colors.
        myobjectMesh = Mesh(
            geometry=objGeometry,
            material=MeshLambertMaterial(vertexColors='VertexColors'),
            position=[0, 0, 0],   # Center the cube
        )
        
        grids = self._getGrids(vertices)
        
        nVert = len(vertices)
        center = [sum([vertex[i] for vertex in vertices]) / float(nVert) for i in range(3)]
        extents = self._getExtents(vertices)
        maxDelta = max([extent[1] - extent[0] for extent in extents])
        camPos = [center[i] + 4 * maxDelta for i in range(3)]
        lightPos = [center[i] + (i+3)*maxDelta for i in range(3)]
        # Set up a scene and render it:
        camera = PerspectiveCamera(position=camPos, fov=20,
                                  children=[DirectionalLight(color='#ffffff', position=lightPos, intensity=0.5)])
        camera.up = (0,0,1)

        sceneThings = [myobjectMesh, camera, AmbientLight(color='#888888')]
        if self.drawGrids: sceneThings.append(grids)
        
        scene = Scene(children=sceneThings, background=BACKGROUND_COLOR)

        rendererObj = Renderer(camera=camera, background='#cccc88', background_opacity=0,
                                scene=scene, controls=[OrbitControls(controlling=camera)], width=self.width, 
                                height=self.height)

        display(rendererObj)
        
