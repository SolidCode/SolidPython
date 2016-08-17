# from distutils.core import setup
from setuptools import setup, find_packages

import os.path


def project_path(*names):
    return os.path.join(os.path.dirname(__file__), *names)

with open(project_path('VERSION')) as f:
    version = f.read().strip()

long_description = []

for rst in ('README.rst', 'CHANGES.rst'):
    with open(project_path(rst)) as f:
        long_description.append(f.read().strip())


setup(
    name='pysolid',
    version=version,
    description="""\
Python interface to the OpenSCAD declarative geometry language

forked from github.com/SolidCode/SolidPython
""",
    author='Maksim Bronsky',
    author_email='maks.bronsky@web.de',
    url='https://github.com/plumps/pysolid',
    py_modules=['solid'],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        """\
License :: OSI Approved :: \
GNU Lesser General Public License v2 or later (LGPLv2+)
""",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
    packages=find_packages(),
    install_requires=['euclid', 'PyPNG'],
)
