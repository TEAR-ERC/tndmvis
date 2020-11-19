import os
import xml.etree.ElementTree as etree

class DataSet:
    def __init__(self, time, file_path):
        self.time = time
        self.file_path = file_path

class PVDReader:
    def __init__(self, file_path):
        tree = etree.parse(file_path)
        root = tree.getroot()
        dirname = os.path.dirname(file_path)
        self.data_sets = []

        if root.tag != "VTKFile" or root.get("version").strip() != "0.1":
            raise IOError("Expected VTKFile version 0.1")
        collection = root.find("Collection")
        if not collection:
            return
        for dno, ds in enumerate(collection.findall("DataSet")):
            file_name = ds.get("file")
            if not file_name:
                raise IOError("Expected attribute 'file' in DataSet")
            file_path = os.path.join(dirname, file_name)
            if not os.path.isfile(file_path):
                raise FileNotFoundError("The file {} does not exist".format(file_path))
            time = float(ds.get("timestep"))
            if not time:
                time = dno
            self.data_sets.append(DataSet(time, file_path))

        self.data_sets.sort(key=lambda ds: ds.time)

    def __iter__(self):
        return iter(self.data_sets)

    def __getitem__(self, index):
        return self.data_sets[index]

    def __len__(self):
        return len(self.data_sets)
