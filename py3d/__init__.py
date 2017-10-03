#!/usr/bin/env python3

"""py3d

Library for reading Arma's .p3d files in their unbinarized (MLOD) form.

https://github.com/KoffeinFlummi/py3d
"""


import struct
import collections


def _read_asciiz(f, encoding="utf-8"):
    pos = f.tell()

    bts = b""
    while b"\0" not in bts:
        bts += f.read(1024)
    bts = bts[:bts.index(b"\0")]

    f.seek(pos + len(bts) + 1)

    return str(bts, encoding=encoding)


class Point:
    def __init__(self, f=None):
        self.coords = (0,0,0)
        self.flags = 0
        self.mass = None
        if f is not None:
            self.read(f)

    def read(self, f):
        self.coords = struct.unpack("fff", f.read(12))
        self.flags = struct.unpack("<L", f.read(4))[0]

    def write(self, f):
        f.write(struct.pack("fff", *self.coords))
        f.write(struct.pack("<L", self.flags))


class Vertex:
    def __init__(self, all_points, all_normals, f=None):
        self.all_points = all_points
        self.all_normals = all_normals
        self.point_index = None
        self.normal_index = None
        self.uv = (0, 0)
        if f is not None:
            self.read(f)

    @property
    def point(self):
        return self.all_points[self.point_index]

    @point.setter
    def point(self, value):
        this.point_index = self.all_points.index(value)

    @property
    def normal(self):
        return self.all_normals[self.normal_index]

    @point.setter
    def normal(self, value):
        this.normal_index = self.all_normals.index(value)

    def read(self, f):
        self.point_index = struct.unpack("<L", f.read(4))[0]
        self.normal_index = struct.unpack("<L", f.read(4))[0]
        self.uv = struct.unpack("ff", f.read(8))

    def write(self, f):
        f.write(struct.pack("<L", self.point_index))
        f.write(struct.pack("<L", self.normal_index))
        f.write(struct.pack("ff", *self.uv))


class Face:
    def __init__(self, all_points, all_normals, f=None):
        self.all_points = all_points
        self.all_normals = all_normals
        self.vertices = []
        self.flags = 0
        self.texture = ""
        self.material = ""
        if f is not None:
            self.read(f)

    def read(self, f):
        num_vertices = struct.unpack("<L", f.read(4))[0]
        assert num_vertices in (3,4)

        self.vertices = [Vertex(self.all_points, self.all_normals, f) for i in range(num_vertices)]

        if num_vertices == 3:
            f.seek(16, 1)

        self.flags = struct.unpack("<L", f.read(4))[0]
        self.texture = _read_asciiz(f)
        self.material = _read_asciiz(f)

    def write(self, f):
        f.write(struct.pack("<L", len(self.vertices)))
        for v in self.vertices:
            v.write(f)
        if len(self.vertices) == 3:
            f.write(b"\0" * 16)
        f.write(struct.pack("<L", self.flags))
        f.write(bytes(self.texture, encoding="utf-8") + b"\0")
        f.write(bytes(self.material, encoding="utf-8") + b"\0")


class Selection:
    def __init__(self, all_points, all_faces, f=None):
        self.all_points = all_points
        self.all_faces = all_faces
        self.points = {}
        self.faces = {}
        if f is not None:
            self.read(f)

    def read(self, f):
        num_bytes = struct.unpack("<L", f.read(4))[0]

        data_points = f.read(len(self.all_points))
        data_faces = f.read(len(self.all_faces))

        self.points = {p: (lambda weight: weight if weight <= 1 else 1 - ((weight - 1) / 255))(data_points[i]) for i, p in enumerate(self.all_points) if data_points[i] > 0}
        self.faces = {fa: (lambda weight: weight if weight <= 1 else 1 - ((weight - 1) / 255))(data_faces[i]) for i, fa in enumerate(self.all_faces) if data_faces[i] > 0}

    def write(self, f):
        f.write(struct.pack("<L", len(self.all_points) + len(self.all_faces)))

        data_points = [(lambda weight: weight if weight in (1,0) else round((1 - weight) * 255) + 1)(self.points[p]) if p in self.points else 0 for p in self.all_points]
        f.write(bytes(data_points))

        data_faces = [(lambda weight: weight if weight in (1,0) else round((1 - weight) * 255) + 1)(self.faces[fa]) if fa in self.faces else 0 for fa in self.all_faces]
        f.write(bytes(data_faces))


class LOD:
    def __init__(self, f=None):
        self.version_major = 28
        self.version_minor = 256
        self.resolution = 1.0
        self.points = []
        self.facenormals = []
        self.faces = []
        self.sharp_edges = []
        self.properties = collections.OrderedDict()
        self.selections = collections.OrderedDict()
        if f is not None:
            self.read(f)

    @property
    def mass(self):
        masses = [x.mass for x in self.points]
        if len([x for x in masses if x is not None]) == 0:
            return None

        return sum(masses)

    @property
    def num_vertices(self):
        return sum([len(x.vertices) for x in self.faces])

    def read(self, f):
        assert f.read(4) == b"P3DM"

        self.version_major = struct.unpack("<L", f.read(4))[0]
        self.version_minor = struct.unpack("<L", f.read(4))[0]

        num_points = struct.unpack("<L", f.read(4))[0]
        num_facenormals = struct.unpack("<L", f.read(4))[0]
        num_faces = struct.unpack("<L", f.read(4))[0]

        f.seek(4, 1)

        self.points.extend([Point(f) for i in range(num_points)])
        self.facenormals.extend([struct.unpack("fff", f.read(12)) for i in range(num_facenormals)])
        self.faces.extend([Face(self.points, self.facenormals, f) for i in range(num_faces)])

        assert f.read(4) == b"TAGG"

        while True:
            f.seek(1, 1)
            taggname = _read_asciiz(f)

            if taggname[0] != "#":
                self.selections[taggname] = Selection(self.points, self.faces, f)
                continue

            num_bytes = struct.unpack("<L", f.read(4))[0]
            data = f.read(num_bytes)

            if taggname == "#EndOfFile#":
                break

            if taggname == "#SharpEdges#": #untested
                self.sharp_edges.extend([struct.unpack("<LL", data[i*8:i*8+8]) for i in range(int(num_bytes / 8))])
                continue

            if taggname == "#Property#": #untested
                assert num_bytes == 128
                k, v = data[:64], data[64:]

                assert b"\0" in k and b"\0" in v
                k, v = k[:k.index(b"\0")], v[:v.index(b"\0")]

                self.properties[str(k, "utf-8")] = str(v, "utf-8")
                continue

            if taggname == "#Mass#":
                assert num_bytes == 4 * num_points
                for i in range(num_points):
                    self.points[i].mass = struct.unpack("f", data[i*4:i*4+4])[0]
                continue

            #if taggname == "#Animation#": #not supported
            #    pass

            #if taggname == "#UVSet#": #ignored, data from lod faces used
            #    pass

        self.resolution = struct.unpack("f", f.read(4))[0]

    def write(self, f):
        f.write(b"P3DM")
        f.write(struct.pack("<L", self.version_major))
        f.write(struct.pack("<L", self.version_minor))

        f.write(struct.pack("<L", len(self.points)))
        f.write(struct.pack("<L", len(self.facenormals)))
        f.write(struct.pack("<L", len(self.faces)))

        f.write(b"\0" * 4)

        for p in self.points:
            p.write(f)
        for fn in self.facenormals:
            f.write(struct.pack("fff", *fn))
        for fa in self.faces:
            fa.write(f)

        f.write(b"TAGG")

        if len(self.sharp_edges) > 0: #untested
            f.write(b"\x01")
            f.write(b"#SharpEdges#\0")
            f.write(struct.pack("<L", len(self.sharp_edges) * 8))
            for se in self.sharp_edges:
                f.write(struct.pack("<LL", *se))

        for k, v in self.selections.items():
            f.write(b"\x01")
            f.write(bytes(k, "utf-8") + b"\0")
            v.write(f)

        for k, v in self.properties.items():
            f.write(b"\x01")
            f.write(b"#Property#\0")
            f.write(struct.pack("<L", 128))
            f.write(struct.pack("64s64s", bytes(k, "utf-8"), bytes(v, "utf-8")))

        if self.mass is not None:
            f.write(b"\x01")
            f.write(b"#Mass#\0")
            f.write(struct.pack("<L", len(self.points) * 4))
            for p in self.points:
                f.write(struct.pack("f", p.mass))

        if len(self.faces) > 0:
            f.write(b"\x01")
            f.write(b"#UVSet#\0")
            f.write(struct.pack("<L", self.num_vertices * 8 + 4))
            f.write(b"\0\0\0\0")
            for fa in self.faces:
                for v in fa.vertices:
                    f.write(struct.pack("ff", *v.uv))

        f.write(b"\x01")
        f.write(b"#EndOfFile#\0")
        f.write(b"\0\0\0\0")

        f.write(struct.pack("f", self.resolution))


class P3D:
    def __init__(self, f=None):
        self.lods = []
        if f is not None:
            self.read(f)

    def read(self, f):
        assert f.read(4) == b"MLOD"

        version = struct.unpack("<L", f.read(4))[0]
        num_lods = struct.unpack("<L", f.read(4))[0]

        self.lods.extend([LOD(f) for i in range(num_lods)])

    def write(self, f):
        f.write(b"MLOD")
        f.write(struct.pack("<L", 257))
        f.write(struct.pack("<L", len(self.lods)))
        for l in self.lods:
            l.write(f)
