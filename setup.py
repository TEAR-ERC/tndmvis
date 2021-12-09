from distutils.core import setup

setup(name='tndmvis',
      version='0.1.x',
      author='Carsten Uphoff',
      author_email='uphoff@geophysik.uni-muenchen.de',
      packages=['tndmvis'],
      scripts=['bin/tndmvis-stations.py', 'bin/tndmvis-fancy.py', 'bin/tndmvis-merge-vtk.py'],
      url='http://github.com/TEAR-ERC/tndmvis',
      license='LICENSE.md',
      description='tandem visualisation tools',
      long_description=open('README.md').read(),
      install_requires=['matplotlib', 'numpy', 'pyvista', 'vtk'])
