from .solidpython import OpenSCADObject

class OpenSCADConstant(OpenSCADObject):
    def __init__(self, code):
        super().__init__("not valid openscad code !?!?!", {})
        self.code = code

    def __repr__(self):
        return self._render()

    def _render(self, render_holes=42):
        return self.code

class ScadInterface:
    def __init__(self):
        self.header = ''

    def register_customizer_var(self, name, value, options=''):
        self.header += f'{name} = {value}; //{options}\n'

    def set_global_var(self, name, value):
        self.header += f'{name} = {value};\n'

    def get_header_str(self):
        return self.header

    def register_font(self, filename):
        self.header += f'use <{filename}>\n'

    @staticmethod
    def get(name):
        return ScadInterface.inline(name)

    @staticmethod
    def inline(code):
        return scad_inline(code)

def scad_inline(code):
    return OpenSCADConstant(code)

