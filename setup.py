# from distutils.core import setup 
from setuptools import setup, find_packages

setup(name='solidpython',
      version='0.1',
      packages = find_packages(),  
      data_files = [ ('solid/test',['solid/test/run_all_tests.sh'])],   
      install_requires = ['euclid'] ,
      )

