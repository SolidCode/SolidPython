import solid
import os
import tempfile
import platform
from IPython.display import display
from ipywidgets import HTML, Text, Output, VBox
from traitlets import link, dlink
import math as pymath
import os
import time
import subprocess
from pythreejs import *
from IPython.display import display, SVG


OBJ_COLOR = '#f7d62c'
BACKGROUND_COLOR = '#ffffff'


class JupyterRenderer:
    '''This class will render an OpenSCAD object within a jupyter notebook.
    The 'pythreejs' module must be installed (see directions a
    https://github.com/jupyter-widgets/pythreejs).

    This class needs to know the path to the openscad command-line tool.
    You can set the path with the OPENSCAD_EXEC environment variable, or with the 'openscad_exec'
    keyword in the constructor.  If these are omitted, the class makes an attempt at
    finding the executable itself.
    other keyword arguments: 'width', 'height', and 'draw_grids' (True/False)
    Primarily this class is used to render a SolidPython object in a Jupyter window, but it
    also provides a method, render_to_stl_file(obj, fname), which creates an STL file
    directly, allowing one to bypass OpenSCAD altogether, if the end goal is the creation of an
    STL file.
    '''
    def __init__(self, **kw):
        self.openscad_exec = None
        self.openscad_tmp_dir = None
        if 'OPENSCAD_EXEC' in os.environ: self.openscad_exec = os.environ['OPENSCAD_EXEC']
        if 'OPENSCAD_TMP_DIR' in os.environ: self.openscad_tmp_dir = os.environ['OPENSCAD_TMP_DIR']
        if 'openscad_exec' in kw: self.openscad_exec = kw['openscad_exec']
        if self.openscad_exec is None:
            self._try_detect_openscad_exec()
        if self.openscad_exec is None:
            raise Exception('openscad exec not found!')
        self.width = kw.get('width', 600)
        self.height = kw.get('height', 600)
        self.draw_grids = kw.get('draw_grids', True)

    def _try_executable(self, executable_path):
        if os.path.isfile(executable_path):
            self.openscad_exec = executable_path

    def _try_detect_openscad_exec(self):
        self.openscad_exec = None
        platfm = platform.system()
        if platfm == 'Linux':
            self._try_executable('/usr/bin/openscad')
            if self.openscad_exec is None:
                self._try_executable('/usr/local/bin/openscad')
        elif platfm == 'Darwin':
            self._try_executable('/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD')
        elif platfm == 'Windows':
            self._try_executable(os.path.join(
                    os.environ.get('Programfiles(x86)','C:'),
                    'OpenSCAD\\openscad.exe'))

    def _conv_stl(self, stl_file_name):
        fl = open(stl_file_name)
        faces = []
        vertices = []
        vert_str_to_index = {}
        ind = 0
        for ln in fl:
            if ln.find('outer loop') >= 0:
                cur_face = []
            elif ln.find('vertex') >= 0:
                vert_str = ln.split('vertex ')[-1]
                if vert_str not in vert_str_to_index:
                    vert_str_to_index[vert_str] = ind
                    vertices.append([float(x) for x in vert_str.split()])
                    v_ind = ind
                    ind += 1
                else:
                    v_ind = vert_str_to_index[vert_str]
                cur_face.append(v_ind)
            elif ln.find('endloop') >= 0:
                faces.append(cur_face)

        return vertices, faces

    def _get_extents(self, vertices):
        extents = []
        for i in range(3):
            coords = [vertex[i] for vertex in vertices]
            extents.append([min(coords), max(coords)])
        return extents

    def _get_grid_lines(self, axis1, start, step, N, axis2, start2, end2):
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

    def _get_grids(self, obj_vertices):
        extents = self._get_extents(obj_vertices)
        grid_verts = []
        deltas = [extent[1] - extent[0] for extent in extents]
        max_extent = max(deltas)
        space1 = 10.0**pymath.floor(pymath.log(max_extent) / pymath.log(10.0) - 0.5)
        space2 = 2 * 10.0**pymath.floor(pymath.log(max_extent / 2.0) / pymath.log(10.0) - 0.5)
        space = space2
        if max_extent / space2 < 7: space = space1
        N = int(pymath.floor(max_extent / space + 2.0))
        grid_cols = []
        axis_cols = ['#ff3333', '#33ff33', '#3333ff']
        for axis1 in range(3):
            for axis2 in range(3):
                axis3 = [x for x in [0,1,2] if x not in [axis1, axis2]][0]
                if axis1 == axis2: continue
                delta = extents[axis1][1] - extents[axis1][0]
                start = pymath.floor(extents[axis1][0] / space) * space
                start2 = pymath.floor(extents[axis2][0] / space) * space
                end2 = start2 + (N - 1) * space
                verts = self._get_grid_lines(axis1, start, space, N, axis2,
                                             start2, end2)
                grid_verts.extend(verts)
                grid_cols.extend([axis_cols[axis3] for vert in verts])


        lines_geom = Geometry(vertices=grid_verts, colors =grid_cols)
        lines = LineSegments(geometry=lines_geom,
                 material=LineBasicMaterial(linewidth=5, transparent=True,
                 opacity=0.5, dashSize=10,
                 gapSize=10, vertexColors='VertexColors'),
                 type='LinePieces')

        return lines, space

    def render_to_stl_file(self, py_scad_obj, fl_name, **kw):
        scad_prepend = ''        
        if 'dollar_sign_vars' in kw:
            for var_name, value in kw['dollar_sign_vars'].items():
                scad_prepend += '${}={};\n'.format(var_name, value)
        else:
            if not kw.get('rough', False):
                scad_prepend += '$fn=120;\n'

        scad_tmp_file = os.path.join(self.tmp_dir, 'tmp.scad')
        try:
            of = open(scad_tmp_file, 'w')
            of.write(scad_prepend)
            of.write(solid.scad_render(py_scad_obj))
            of.close()

            # now run openscad to generate stl:
            cmd = [self.openscad_exec, '-o', fl_name, scad_tmp_file]
            return_code = subprocess.call(cmd)
            if return_code < 0:
                raise Exception('openscad command line returned code {}'.format(return_code))
        except Exception as e:
            raise e
        finally:
            if os.path.isfile(scad_tmp_file):
                os.remove(scad_tmp_file)        

    def render(self, py_scad_obj, **kw):
        if self.openscad_tmp_dir is not None:
            self.tmp_dir = self.openscad_tmp_dir
        else:
            self.tmp_dir = tempfile.mkdtemp()
        self.saved_umask = os.umask(0o077)

        stl_tmp_file = os.path.join(self.tmp_dir, 'tmp.stl')
        
        try:
            kw['rough'] = True
            self.render_to_stl_file(py_scad_obj, stl_tmp_file, **kw)
            self._render_stl(stl_tmp_file)
        except Exception as e:
            raise e
        finally:
            if os.path.isfile(stl_tmp_file):
                os.remove(stl_tmp_file)
            if self.openscad_tmp_dir is not None:
                os.rmdir(self.tmp_dir)

    def _render_stl(self, stl_file):
        vertices, faces = self._conv_stl(stl_file)

        # Map the vertex colors into the 'color' slot of the faces
        faces = [f + [None, [OBJ_COLOR for i in f], None] for f in faces]

        # Create the geometry:
        obj_geometry = Geometry(vertices=vertices,
            faces=faces, colors = [OBJ_COLOR]*len(vertices))
        # Calculate normals per face, for nice crisp edges:
        obj_geometry.exec_three_obj_method('computeFaceNormals')

        # Create a mesh. Note that the material need to be told to use the vertex colors.
        my_object_mesh = Mesh(
            geometry=obj_geometry,
            material=MeshLambertMaterial(vertexColors='VertexColors'),
            position=[0, 0, 0],   # Center the cube
        )

        n_vert = len(vertices)
        center = [sum([vertex[i] for vertex in vertices]) / float(n_vert)
                  for i in range(3)]
        extents = self._get_extents(vertices)
        max_delta = max([extent[1] - extent[0] for extent in extents])
        camPos = [center[i] + 4 * max_delta for i in range(3)]
        light_pos = [center[i] + (i+3)*max_delta for i in range(3)]

        # Set up a scene and render it:
        camera = PerspectiveCamera(position=camPos, fov=20,
                                   children=[DirectionalLight(color='#ffffff',
                                   position=light_pos, intensity=0.5)])
        camera.up = (0,0,1)

        scene_things = [my_object_mesh, camera, AmbientLight(color='#888888')]
        if self.draw_grids:
            grids, space = self._get_grids(vertices)
            scene_things.append(grids)

        scene = Scene(children=scene_things, background=BACKGROUND_COLOR)

        renderer_obj = Renderer(camera=camera, background='#cccc88',
            background_opacity=0, scene=scene,
            controls=[OrbitControls(controlling=camera)],
            width=self.width,
            height=self.height)

        display_things = [renderer_obj]
        if self.draw_grids:
            s = """
<svg width="{}" height="30">
<rect width="20" height="20" x="{}" y="0" style="fill:none;stroke-width:1;stroke:rgb(0,255,0)" />
    <text x="{}" y="15">={:.1f}</text>
  Sorry, your browser does not support inline SVG.
</svg>""".format(self.width, self.width//2, self.width//2+25, space)
            display_things.append(HTML(s))

        display(*display_things)

