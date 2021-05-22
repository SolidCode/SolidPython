from pathlib import Path
from typing import List, Union
PathStr = Union[Path, str]


def _openscad_library_paths() -> List[Path]:
    """
    Return system-dependent OpenSCAD library paths or paths defined in os.environ['OPENSCADPATH']
    """
    import platform
    import os
    import re

    paths = [Path('.')]

    user_path = os.environ.get('OPENSCADPATH')
    if user_path:
        for s in re.split(r'\s*[;:]\s*', user_path):
            paths.append(Path(s))

    default_paths = {
        'Linux':   Path.home() / '.local/share/OpenSCAD/libraries',
        'Darwin':  Path.home() / 'Documents/OpenSCAD/libraries',
        'Windows': Path('My Documents\OpenSCAD\libraries')
    }

    paths.append(default_paths[platform.system()])
    return paths

def _find_library(library_name: PathStr) -> Path:
    result = Path(library_name)

    if not result.is_absolute():
        paths = _openscad_library_paths()
        for p in paths:
            f = p / result
            # print(f'Checking {f} -> {f.exists()}')
            if f.exists():
                result = f

    return result

