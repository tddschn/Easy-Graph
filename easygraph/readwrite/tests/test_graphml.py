import pytest
import easygraph as eg
from easygraph.utils import nodes_equal, edges_equal
from easygraph.readwrite.graphml import GraphMLWriter
import io
import tempfile
import os

class BaseGraphML:
    @classmethod
    def setup_class(cls):
        cls.simple_directed_data = """<?xml version="1.0" encoding="UTF-8"?>
<!-- This file was written by the JAVA GraphML Library.-->
<graphml xmlns="http://graphml.graphdrawing.org/xmlns"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns
         http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
  <graph id="G" edgedefault="directed">
    <node id="n0"/>
    <node id="n1"/>
    <node id="n2"/>
    <node id="n3"/>
    <node id="n4"/>
    <node id="n5"/>
    <node id="n6"/>
    <node id="n7"/>
    <node id="n8"/>
    <node id="n9"/>
    <node id="n10"/>
    <edge id="foo" source="n0" target="n2"/>
    <edge source="n1" target="n2"/>
    <edge source="n2" target="n3"/>
    <edge source="n3" target="n5"/>
    <edge source="n3" target="n4"/>
    <edge source="n4" target="n6"/>
    <edge source="n6" target="n5"/>
    <edge source="n5" target="n7"/>
    <edge source="n6" target="n8"/>
    <edge source="n8" target="n7"/>
    <edge source="n8" target="n9"/>
  </graph>
</graphml>"""
        cls.simple_directed_graph = eg.DiGraph()
        cls.simple_directed_graph.add_node("n10")
        cls.simple_directed_graph.add_edge("n0", "n2", id="foo")
        cls.simple_directed_graph.add_edge("n0", "n2")
        cls.simple_directed_graph.add_edges_from(
            [
                ("n1", "n2"),
                ("n2", "n3"),
                ("n3", "n5"),
                ("n3", "n4"),
                ("n4", "n6"),
                ("n6", "n5"),
                ("n5", "n7"),
                ("n6", "n8"),
                ("n8", "n7"),
                ("n8", "n9"),
            ]
        )
        cls.simple_directed_fh = io.BytesIO(cls.simple_directed_data.encode("UTF-8"))

        cls.attribute_data = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns
        http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
  <key id="d0" for="node" attr.name="color" attr.type="string">
    <default>yellow</default>
  </key>
  <key id="d1" for="edge" attr.name="weight" attr.type="double"/>
  <graph id="G" edgedefault="directed">
    <node id="n0">
      <data key="d0">green</data>
    </node>
    <node id="n1"/>
    <node id="n2">
      <data key="d0">blue</data>
    </node>
    <node id="n3">
      <data key="d0">red</data>
    </node>
    <node id="n4"/>
    <node id="n5">
      <data key="d0">turquoise</data>
    </node>
    <edge id="e0" source="n0" target="n2">
      <data key="d1">1.0</data>
    </edge>
    <edge id="e1" source="n0" target="n1">
      <data key="d1">1.0</data>
    </edge>
    <edge id="e2" source="n1" target="n3">
      <data key="d1">2.0</data>
    </edge>
    <edge id="e3" source="n3" target="n2"/>
    <edge id="e4" source="n2" target="n4"/>
    <edge id="e5" source="n3" target="n5"/>
    <edge id="e6" source="n5" target="n4">
      <data key="d1">1.1</data>
    </edge>
  </graph>
</graphml>
"""
        cls.attribute_graph = eg.DiGraph(id="G")
        cls.attribute_graph.graph["node_default"] = {"color": "yellow"}
        cls.attribute_graph.add_node("n0", color="green")
        cls.attribute_graph.add_node("n2", color="blue")
        cls.attribute_graph.add_node("n3", color="red")
        cls.attribute_graph.add_node("n4")
        cls.attribute_graph.add_node("n5", color="turquoise")
        cls.attribute_graph.add_edge("n0", "n2", id="e0", weight=1.0)
        cls.attribute_graph.add_edge("n0", "n1", id="e1", weight=1.0)
        cls.attribute_graph.add_edge("n1", "n3", id="e2", weight=2.0)
        cls.attribute_graph.add_edge("n3", "n2", id="e3")
        cls.attribute_graph.add_edge("n2", "n4", id="e4")
        cls.attribute_graph.add_edge("n3", "n5", id="e5")
        cls.attribute_graph.add_edge("n5", "n4", id="e6", weight=1.1)
        cls.attribute_fh = io.BytesIO(cls.attribute_data.encode("UTF-8"))

        cls.node_attribute_default_data = """<?xml version="1.0" encoding="UTF-8"?>
        <graphml xmlns="http://graphml.graphdrawing.org/xmlns"
              xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
              xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns
                http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
          <key id="d0" for="node" attr.name="boolean_attribute" attr.type="boolean"><default>false</default></key>
          <key id="d1" for="node" attr.name="int_attribute" attr.type="int"><default>0</default></key>
          <key id="d2" for="node" attr.name="long_attribute" attr.type="long"><default>0</default></key>
          <key id="d3" for="node" attr.name="float_attribute" attr.type="float"><default>0.0</default></key>
          <key id="d4" for="node" attr.name="double_attribute" attr.type="double"><default>0.0</default></key>
          <key id="d5" for="node" attr.name="string_attribute" attr.type="string"><default>Foo</default></key>
          <graph id="G" edgedefault="directed">
            <node id="n0"/>
            <node id="n1"/>
            <edge id="e0" source="n0" target="n1"/>
          </graph>
        </graphml>
        """
        cls.node_attribute_default_graph = eg.DiGraph(id="G")
        cls.node_attribute_default_graph.graph["node_default"] = {
            "boolean_attribute": False,
            "int_attribute": 0,
            "long_attribute": 0,
            "float_attribute": 0.0,
            "double_attribute": 0.0,
            "string_attribute": "Foo",
        }
        cls.node_attribute_default_graph.add_node("n0")
        cls.node_attribute_default_graph.add_node("n1")
        cls.node_attribute_default_graph.add_edge("n0", "n1", id="e0")
        cls.node_attribute_default_fh = io.BytesIO(
            cls.node_attribute_default_data.encode("UTF-8")
        )

        cls.attribute_named_key_ids_data = """<?xml version='1.0' encoding='utf-8'?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns
         http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
  <key id="edge_prop" for="edge" attr.name="edge_prop" attr.type="string"/>
  <key id="prop2" for="node" attr.name="prop2" attr.type="string"/>
  <key id="prop1" for="node" attr.name="prop1" attr.type="string"/>
  <graph edgedefault="directed">
    <node id="0">
      <data key="prop1">val1</data>
      <data key="prop2">val2</data>
    </node>
    <node id="1">
      <data key="prop1">val_one</data>
      <data key="prop2">val2</data>
    </node>
    <edge source="0" target="1">
      <data key="edge_prop">edge_value</data>
    </edge>
  </graph>
</graphml>
"""
        cls.attribute_named_key_ids_graph = eg.DiGraph()
        cls.attribute_named_key_ids_graph.add_node("0", prop1="val1", prop2="val2")
        cls.attribute_named_key_ids_graph.add_node("1", prop1="val_one", prop2="val2")
        cls.attribute_named_key_ids_graph.add_edge("0", "1", edge_prop="edge_value")
        fh = io.BytesIO(cls.attribute_named_key_ids_data.encode("UTF-8"))
        cls.attribute_named_key_ids_fh = fh

        cls.attribute_numeric_type_data = """<?xml version='1.0' encoding='utf-8'?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns
         http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
  <key attr.name="weight" attr.type="double" for="node" id="d1" />
  <key attr.name="weight" attr.type="double" for="edge" id="d0" />
  <graph edgedefault="directed">
    <node id="n0">
      <data key="d1">1</data>
    </node>
    <node id="n1">
      <data key="d1">2.0</data>
    </node>
    <edge source="n0" target="n1">
      <data key="d0">1</data>
    </edge>
    <edge source="n1" target="n0">
      <data key="d0">k</data>
    </edge>
    <edge source="n1" target="n1">
      <data key="d0">1.0</data>
    </edge>
  </graph>
</graphml>
"""
        cls.attribute_numeric_type_graph = eg.DiGraph()
        cls.attribute_numeric_type_graph.add_node("n0", weight=1)
        cls.attribute_numeric_type_graph.add_node("n1", weight=2.0)
        cls.attribute_numeric_type_graph.add_edge("n0", "n1", weight=1)
        cls.attribute_numeric_type_graph.add_edge("n1", "n1", weight=1.0)
        fh = io.BytesIO(cls.attribute_numeric_type_data.encode("UTF-8"))
        cls.attribute_numeric_type_fh = fh

        cls.simple_undirected_data = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns
         http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
  <graph id="G">
    <node id="n0"/>
    <node id="n1"/>
    <node id="n2"/>
    <node id="n10"/>
    <edge id="foo" source="n0" target="n2"/>
    <edge source="n1" target="n2"/>
    <edge source="n2" target="n3"/>
  </graph>
</graphml>"""
        #    <edge source="n8" target="n10" directed="false"/>
        cls.simple_undirected_graph = eg.Graph()
        cls.simple_undirected_graph.add_node("n10")
        cls.simple_undirected_graph.add_edge("n0", "n2", id="foo")
        cls.simple_undirected_graph.add_edges_from([("n1", "n2"), ("n2", "n3")])
        fh = io.BytesIO(cls.simple_undirected_data.encode("UTF-8"))
        cls.simple_undirected_fh = fh

class TestReadGraphML(BaseGraphML):
    def test_read_simple_directed_graphml(self):
        G = self.simple_directed_graph
        H = eg.read_graphml(self.simple_directed_fh)
        assert sorted(G.nodes()) == sorted(H.nodes())
        assert sorted(G.edges()) == sorted(H.edges())
        assert sorted(G.edges(data=True)) == sorted(H.edges(data=True))
        self.simple_directed_fh.seek(0)

        PG = eg.parse_graphml(self.simple_directed_data)
        assert sorted(G.nodes()) == sorted(PG.nodes())
        assert sorted(G.edges()) == sorted(PG.edges())
        assert sorted(G.edges(data=True)) == sorted(PG.edges(data=True))

    def test_read_simple_undirected_graphml(self):
        G = self.simple_undirected_graph
        H = eg.read_graphml(self.simple_undirected_fh)
        assert nodes_equal(G.nodes(), H.nodes())
        assert edges_equal(G.edges(), H.edges())
        self.simple_undirected_fh.seek(0)

        PG = eg.parse_graphml(self.simple_undirected_data)
        assert nodes_equal(G.nodes(), PG.nodes())
        assert edges_equal(G.edges(), PG.edges())

    def test_read_attribute_graphml(self):
        G = self.attribute_graph
        H = eg.read_graphml(self.attribute_fh)
        assert nodes_equal(G.nodes(True), sorted(H.nodes(data=True)))
        ge = sorted(G.edges(data=True))
        he = sorted(H.edges(data=True))
        for a, b in zip(ge, he):
            assert a == b
        self.attribute_fh.seek(0)

        PG = eg.parse_graphml(self.attribute_data)
        assert sorted(G.nodes(True)) == sorted(PG.nodes(data=True))
        ge = sorted(G.edges(data=True))
        he = sorted(PG.edges(data=True))
        for a, b in zip(ge, he):
            assert a == b

    def test_node_default_attribute_graphml(self):
        G = self.node_attribute_default_graph
        H = eg.read_graphml(self.node_attribute_default_fh)
        assert G.graph["node_default"] == H.graph["node_default"]

class TestWriteGraphML(BaseGraphML):
    writer = staticmethod(eg.write_graphml_lxml)

    @classmethod
    def setup_class(cls):
        BaseGraphML.setup_class()
        _ = pytest.importorskip("lxml.etree")

    def test_write_interface(self):
        try:
            import lxml.etree

            assert eg.write_graphml == eg.write_graphml_lxml
        except ImportError:
            assert eg.write_graphml == eg.write_graphml_xml

    def test_write_read_simple_directed_graphml(self):
        G = self.simple_directed_graph
        G.graph["hi"] = "there"
        fh = io.BytesIO()
        self.writer(G, fh)
        fh.seek(0)
        H = eg.read_graphml(fh)
        assert sorted(G.nodes()) == sorted(H.nodes())
        assert sorted(G.edges()) == sorted(H.edges())
        assert sorted(G.edges(data=True)) == sorted(H.edges(data=True))
        self.simple_directed_fh.seek(0)

    def test_GraphMLWriter_add_graphs(self):
        gmlw = GraphMLWriter()
        G = self.simple_directed_graph
        H = G.copy()
        gmlw.add_graphs([G, H])

    def test_write_read_simple_no_prettyprint(self):
        G = self.simple_directed_graph
        G.graph["hi"] = "there"
        G.graph["id"] = "1"
        fh = io.BytesIO()
        self.writer(G, fh, prettyprint=False)
        fh.seek(0)
        H = eg.read_graphml(fh)
        assert sorted(G.nodes()) == sorted(H.nodes())
        assert sorted(G.edges()) == sorted(H.edges())
        assert sorted(G.edges(data=True)) == sorted(H.edges(data=True))
        self.simple_directed_fh.seek(0)