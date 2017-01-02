# from distutils.core import setup
from setuptools import setup, find_packages

setup(
    name='solidpython',
    version='0.2.0',
    description='Python interface to the OpenSCAD declarative geometry language',
    author='Evan Jones',
    author_email='evan_t_jones@mac.com',
    url='https://github.com/SolidCode/SolidPython',
    py_modules=['solid'],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
    packages=find_packages(),
    install_requires=['euclid3', 'PyPNG', 'prettytable'],
)
