#!/usr/bin/env python3

from tndmvis import pvd, util
import argparse
import re
import os
import vtk

parser = argparse.ArgumentParser()
parser.add_argument('pvd', type=str, help='Path to PVD file')
parser.add_argument('prefix', type=str, help='Output directory')
args = parser.parse_args()

with open(args.pvd) as f:
    inp = f.read()
    out = inp.replace('.pvtu', '.vtu')
    with open(os.path.join(args.prefix, os.path.basename(args.pvd)), 'w') as o:
        o.write(out)

steps = pvd.PVDReader(args.pvd)
nsteps = len(steps)

with util.Progress(nsteps) as p:
    for i, v in enumerate(steps):
        reader = vtk.vtkXMLPUnstructuredGridReader()
        reader.SetFileName(v.file_path)
        reader.Update()

        name = os.path.basename(v.file_path)
        name = name.replace('.pvtu', '.vtu')

        writer = vtk.vtkXMLUnstructuredGridWriter()
        writer.SetFileName(os.path.join(args.prefix, name))
        writer.SetInputData(reader.GetOutput())
        writer.Write()
        p.update(i)
