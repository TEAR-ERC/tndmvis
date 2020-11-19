#!/usr/bin/env python3

from tndmvis import pvd, util, writer
import argparse
import math
import numpy as np
import pyvista as pv
import vtk


def load_stations(stations):
    points_reader = vtk.vtkDelimitedTextReader()
    points_reader.SetFileName(stations)
    points_reader.DetectNumericColumnsOn()
    points_reader.SetHaveHeaders(True)

    table_points = vtk.vtkTableToPolyData()
    table_points.SetInputConnection(points_reader.GetOutputPort())
    table_points.SetXColumn('x')
    table_points.SetYColumn('y')
    table_points.SetZColumn('z')
    table_points.Update()

    return table_points.GetOutput()


def station_names(points):
    names = points.GetPointData().GetAbstractArray('name')
    station_names = None
    if names:
        station_names = [
            names.GetValue(i) for i in range(points.GetNumberOfPoints())
        ]
    return station_names


def resample(pvd_file, points, variable_map, variable_transform):
    steps = pvd.PVDReader(pvd_file)

    data = np.ndarray(
        (len(variable_map) + 1, len(steps), points.GetNumberOfPoints()),
        order='F')

    interp = vtk.vtkResampleWithDataSet()
    interp.SetInputData(points)

    cols = ['Time'] + [t for f, t in variable_map]
    identity = lambda x: x
    trans = [
        variable_transform[t] if t in variable_transform else identity
        for f, t in variable_map
    ]

    with util.Progress(len(steps)) as p:
        for no, step in enumerate(steps):
            mesh = pv.read(step.file_path)
            interp.SetSourceData(mesh)
            interp.Update()

            point_data = interp.GetOutput().GetPointData()
            variables = [
                point_data.GetAbstractArray(f) for f, t in variable_map
            ]
            for s in range(variables[0].GetNumberOfTuples()):
                data[0, no, s] = step.time
                for q, var in enumerate(variables):
                    val = var.GetValue(s)
                    data[q + 1, no, s] = trans[q](val)
            p.update(no)
    return cols, data


parser = argparse.ArgumentParser(description='Pick output at stations')
parser.add_argument('-o',
                    '--output',
                    type=str,
                    help='Output name prefix',
                    default='fltst')
parser.add_argument('stations',
                    help='CSV file with stations (name, x, y, z)',
                    type=lambda x: util.is_valid_file(parser, x))
parser.add_argument('pvd',
                    help='Fault output PVD file',
                    type=lambda x: util.is_valid_file(parser, x))
args = parser.parse_args()

points = load_stations(args.stations)
names = station_names(points)

variable_map = [('state1', 'slip'), ('state3', 'slip_rate'),
                ('state2', 'shear_stress'), ('state0', 'state')]
variable_transform = {'state': math.log10, 'slip_rate': lambda x: math.log10(abs(x))}

cols, data = resample(args.pvd, points, variable_map, variable_transform)

writer.write_tecplot(args.output, cols, data, names)
