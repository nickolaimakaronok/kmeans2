from setuptools import setup, Extension

# Name of the module "mykmeanssp" should be the same as in C
module = Extension("mykmeanssp", sources=['kmeansmodule.c'])

setup(
    name='mykmeanssp',
    version='1.0',
    description='Python C extension for K-means clustering',
    ext_modules=[module]
)