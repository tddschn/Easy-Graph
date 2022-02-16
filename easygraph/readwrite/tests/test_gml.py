from ast import literal_eval
import codecs
from contextlib import contextmanager
import io
import math
import pytest

import easygraph as eg
from easygraph.readwrite.gml import literal_stringizer, literal_destringizer
import os
import tempfile
from textwrap import dedent

class TestGraph:
    @classmethod
    def setup_class(cls):
        cls.simple_data = """Creator "me"
Version "xx"
graph [
 comment "This is a sample graph"
 directed 1
 IsPlanar 1
 pos  [ x 0 y 1 ]
 node [
   id 1
   label "Node 1"
   pos [ x 1 y 1 ]
 ]
 node [
    id 2
    pos [ x 1 y 2 ]
    label "Node 2"
    ]
  node [
    id 3
    label "Node 3"
    pos [ x 1 y 3 ]
  ]
  edge [
    source 1
    target 2
    label "Edge from node 1 to node 2"
    color [line "blue" thickness 3]

  ]
  edge [
    source 2
    target 3
    label "Edge from node 2 to node 3"
  ]
  edge [
    source 3
    target 1
    label "Edge from node 3 to node 1"
  ]
]
"""

    def test_read_gml(self):
        (fd, fname) = tempfile.mkstemp()
        fh = open(fname, "w")
        fh.write(self.simple_data)
        fh.close()
        Gin = eg.read_gml(fname, label="label")
        G = eg.parse_gml(self.simple_data, label="label")
        print("nodes: ", G.nodes)
        print("edges: ", G.edges)
        assert sorted(G.nodes) == sorted(Gin.nodes)
        assert sorted(G.edges) == sorted(Gin.edges)
        os.close(fd)
        os.unlink(fname)

    def test_label_kwarg(self):
        G = eg.parse_gml(self.simple_data, label="id")
        assert sorted(G.nodes) == [1, 2, 3]
        labels = [G.nodes[n]["label"] for n in sorted(G.nodes)]
        assert labels == ["Node 1", "Node 2", "Node 3"]

        G = eg.parse_gml(self.simple_data, label=None)
        assert sorted(G.nodes) == [1, 2, 3]
        labels = [G.nodes[n]["label"] for n in sorted(G.nodes)]
        assert labels == ["Node 1", "Node 2", "Node 3"]

    def test_quotes(self):
        # https://github.com/networkx/networkx/issues/1061
        # Encoding quotes as HTML entities.
        G = eg.Graph()
        G.add_node(0)
        G.name = "path_graph(1)"
        attr = 'This is "quoted" and this is a copyright: ' + chr(169)
        G.nodes[0]["demo"] = attr
        fobj = tempfile.NamedTemporaryFile()
        eg.write_gml(G, fobj)
        fobj.seek(0)
        # Should be bytes in 2.x and 3.x
        data = fobj.read().strip().decode("ascii")
        print("data: ",data)
        answer = """graph [
  name "path_graph(1)"
  node [
    id 0
    label "0"
    demo "This is &#34;quoted&#34; and this is a copyright: &#169;"
  ]
]"""
        assert data == answer
