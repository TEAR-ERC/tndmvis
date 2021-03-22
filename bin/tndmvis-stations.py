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


def adjust_points(points, bounding_box):
    """Move points inside of bounding box.

    :param points: vtkPoints
    :param bounding_box: From mesh.GetBounds()
    """
    new_points = vtk.vtkPoints()
    new_points.SetDataTypeToDouble()

    new_point = [0, 0, 0]
    for s in range(points.GetNumberOfPoints()):
        old_point = points.GetPoint(s)
        dist2 = 0.0
        for d in range(3):
            bmin = bounding_box[2 * d]
            bmax = bounding_box[2 * d + 1]
            if old_point[d] > bmax:
                new_point[d] = bmax
            elif old_point[d] < bmin:
                new_point[d] = bmin
            else:
                new_point[d] = old_point[d]
            dist2 += (old_point[d] - new_point[d])**2
        if dist2 > 0.0001**2:
            raise RuntimeError(
                'Station {} lies too far outside of the mesh\'s bounding box {}'
                .format(old_point, bounding_box))

        new_points.InsertNextPoint(new_point)

    return new_points


def resample(pvd_file, points, variable_map, variable_transform):
    steps = pvd.PVDReader(pvd_file)

    data = np.ndarray(
        (len(variable_map) + 1, len(steps), points.GetNumberOfPoints()),
        order='F')

    probe = vtk.vtkProbeFilter()
    probe.SetInputData(points)
    if len(steps) > 0:
        """The probe filter fails silently if the bounding boxes of points and mesh
           do not intersect. We slightly move the points here to make the bounding
           boxes intersect.
        """
        mesh = pv.read(steps[0].file_path)
        new_points = adjust_points(points.GetPoints(), mesh.GetBounds())
        points.SetPoints(new_points)

    cols = ['Time'] + [t for f, t in variable_map]
    identity = lambda x: x
    trans = [
        variable_transform[t] if t in variable_transform else identity
        for f, t in variable_map
    ]

    with util.Progress(len(steps)) as p:
        for no, step in enumerate(steps):
            mesh = pv.read(step.file_path)
            probe.SetSourceData(mesh)
            probe.Update()

            point_data = probe.GetOutput().GetPointData()
            variables = [
                point_data.GetAbstractArray(f) for f, t in variable_map
            ]
            valid_mask = point_data.GetAbstractArray('vtkValidPointMask')
            for s in range(variables[0].GetNumberOfTuples()):
                if valid_mask.GetTuple(s)[0] == 0.0:
                    raise RuntimeError(
                        'VTK could not find cell for station {}'.format(
                            points.GetPoint(s)))
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
                ('state2', 'shear_stress'), ('state4', 'normal_stress'),
                ('state0', 'state')]
variable_transform = {
    'state': lambda x: math.log10(math.exp((x - 0.6) / 0.015) * 0.008 / 1e-6),
    'slip_rate': lambda x: math.log10(abs(x))
}

cols, data = resample(args.pvd, points, variable_map, variable_transform)

writer.write_tecplot(args.output, cols, data, names)
