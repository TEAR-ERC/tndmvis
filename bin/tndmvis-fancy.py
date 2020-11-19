#!/usr/bin/env python3

from tndmvis import pvd, util, writer
import argparse
import pyvista as pv
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, ListedColormap


def combine_mesh(pvd_file):
    year = 365 * 24 * 3600.0
    steps = pvd.PVDReader(pvd_file)
    nsteps = len(steps)
    meshes = []
    with util.Progress(nsteps) as p:
        for i in range(nsteps):
            mesh = pv.read(steps[i].file_path)
            mesh.translate((0.0, 0.0, steps[i].time / year))
            meshes.append(mesh)
            p.update(i)
    return pv.MultiBlock(meshes).combine()


def plot(mesh, slip, slip_rate, cmap=None):
    mesh[slip_rate] = np.abs(mesh[slip_rate])
    warped = mesh.warp_by_scalar(scalars=slip, normal=[1, 0, 0])

    plotter = pv.Plotter()
    plotter.add_mesh(warped,
                     scalars=slip_rate,
                     log_scale=True,
                     cmap=cmap,
                     stitle="Slip rate [m/s]",
                     scalar_bar_args={
                         "vertical": True,
                         "color": (0, 0, 0)
                     })

    plotter.camera_position = [(15.0, -21.0, 90.0), (15.0, -21.0, 0.0),
                               (0.0, 1.0, 0.0)]
    plotter.background_color = (1.0, 1.0, 1.0)
    plotter.set_scale(yscale=0.5, zscale=-0.03)

    plotter.show_bounds(xlabel="Displacement [m]",
                        ylabel="Depth [km]",
                        zlabel="Time [yr]",
                        location="outer",
                        color=(0, 0, 0))
    plotter.show(window_size=(1920, 1080))


parser = argparse.ArgumentParser(
    description='Fancy plot of displacement over time')
parser.add_argument('-o',
                    '--output',
                    type=str,
                    help='Output name prefix',
                    default='fancy')
parser.add_argument('-c',
                    '--cmap',
                    type=lambda x: util.is_valid_file(parser, x),
                    help='Colour map file')
parser.add_argument('-v',
                    '--slip_rate',
                    help='Name of slip rate variable',
                    default='state3')
parser.add_argument('-s',
                    '--slip',
                    help='Name of slip variable',
                    default='state1')
parser.add_argument('pvd',
                    help='Fault output PVD file',
                    type=lambda x: util.is_valid_file(parser, x))
args = parser.parse_args()

cmap = None
if args.cmap:
    cmap_data = np.loadtxt(args.cmap)
    cmap = LinearSegmentedColormap('custom_cmap', cmap_data)
    cmap = ListedColormap(cmap_data)

mesh = combine_mesh(args.pvd)
plot(mesh, args.slip, args.v, cmap)
