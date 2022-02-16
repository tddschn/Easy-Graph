"""Base class for MultiGraph."""
from copy import deepcopy

import easygraph as eg
from easygraph.classes.graph import Graph
from easygraph.classes.coreviews import MultiAdjacencyView
from easygraph.classes.reportviews import MultiEdgeView, MultiDegreeView
from easygraph import NetworkXError
import easygraph.convert as convert
from easygraph.utils.exception import EasyGraphError

__all__ = ["MultiGraph"]

class MultiGraph(Graph):
    edge_key_dict_factory = dict

    def __init__(self, incoming_graph_data=None, multigraph_input=None, **attr):
        self.edge_key_dict_factory = self.edge_key_dict_factory
        if isinstance(incoming_graph_data, dict) and multigraph_input is not False:
            Graph.__init__(self)
            try:
                convert.from_dict_of_dicts(
                    incoming_graph_data, create_using=self, multigraph_input=True
                )
                self.graph.update(attr)
            except Exception as err:
                if multigraph_input is True:
                    raise eg.EasyGraphError(
                        f"converting multigraph_input raised:\n{type(err)}: {err}"
                    )
                Graph.__init__(self, incoming_graph_data, **attr)
        else:
            Graph.__init__(self, incoming_graph_data, **attr)

    def new_edge_key(self, u, v):
        try:
            keydict = self._adj[u][v]
        except KeyError:
            return 0
        key = len(keydict)
        while key in keydict:
            key += 1
        return key

    def add_edge(self, u_for_edge, v_for_edge, **attr):
        u, v = u_for_edge, v_for_edge
        # add nodes
        if u not in self._adj:
            if u is None:
                raise ValueError("None cannot be a node")
            self._adj[u] = self.adjlist_inner_dict_factory()
            self._node[u] = self.node_attr_dict_factory()
        if v not in self._adj:
            if v is None:
                raise ValueError("None cannot be a node")
            self._adj[v] = self.adjlist_inner_dict_factory()
            self._node[v] = self.node_attr_dict_factory()
        if key is None:
            key = self.new_edge_key(u, v)
        if v in self._adj[u]:
            keydict = self._adj[u][v]
            datadict = keydict.get(key, self.edge_attr_dict_factory())
            datadict.update(attr)
            keydict[key] = datadict
        else:
            # selfloops work this way without special treatment
            datadict = self.edge_attr_dict_factory()
            datadict.update(attr)
            keydict = self.edge_key_dict_factory()
            keydict[key] = datadict
            self._adj[u][v] = keydict
            self._adj[v][u] = keydict
        return key

    def add_edges_from(self, ebunch_to_add, **attr):
        for e in ebunch_to_add:
            ne = len(e)
            if ne == 3:
                u, v, dd = e
            elif ne == 2:
                u, v = e
                dd = {}  # doesn't need edge_attr_dict_factory
            else:
                raise EasyGraphError(f"Edge tuple {e} must be a 2-tuple or 3-tuple.")
            if u not in self._node:
                if u is None:
                    raise ValueError("None cannot be a node")
                self._adj[u] = self.adjlist_inner_dict_factory()
                self._node[u] = self.node_attr_dict_factory()
            if v not in self._node:
                if v is None:
                    raise ValueError("None cannot be a node")
                self._adj[v] = self.adjlist_inner_dict_factory()
                self._node[v] = self.node_attr_dict_factory()
            datadict = self._adj[u].get(v, self.edge_attr_dict_factory())
            datadict.update(attr)
            datadict.update(dd)
            self._adj[u][v] = datadict
            self._adj[v][u] = datadict

    def add_edges_from(self, ebunch_to_add, **attr):
        keylist = []
        for e in ebunch_to_add:
            ne = len(e)
            if ne == 4:
                u, v, key, dd = e
            elif ne == 3:
                u, v, dd = e
                key = None
            elif ne == 2:
                u, v = e
                dd = {}
                key = None
            else:
                msg = f"Edge tuple {e} must be a 2-tuple, 3-tuple or 4-tuple."
                raise EasyGraphError(msg)
            ddd = {}
            ddd.update(attr)
            try:
                ddd.update(dd)
            except (TypeError, ValueError):
                if ne != 3:
                    raise
                key = dd  # ne == 3 with 3rd value not dict, must be a key
            key = self.add_edge(u, v, key)
            self[u][v][key].update(ddd)
            keylist.append(key)
        return keylist

    def remove_edge(self, u, v, key=None):
        try:
            d = self._adj[u][v]
        except KeyError as err:
            raise NetworkXError(f"The edge {u}-{v} is not in the graph.") from err
        # remove the edge with specified data
        if key is None:
            d.popitem()
        else:
            try:
                del d[key]
            except KeyError as err:
                msg = f"The edge {u}-{v} with key {key} is not in the graph."
                raise NetworkXError(msg) from err
        if len(d) == 0:
            # remove the key entries if last edge
            del self._adj[u][v]
            if u != v:  # check for selfloop
                del self._adj[v][u]

    def remove_edges_from(self, ebunch):
        for e in ebunch:
            try:
                self.remove_edge(*e[:3])
            except NetworkXError:
                pass

    def has_edge(self, u, v, key=None):
        try:
            if key is None:
                return v in self._adj[u]
            else:
                return key in self._adj[u][v]
        except KeyError:
            return False

    @property
    def edges(self):
        edges = list()
        seen = {}
        for n, nbrs in self._nodes_nbrs():
            for nbr, kd in nbrs.items():
                if nbr not in seen:
                    for k, dd in kd.items():
                        edges.append((n, nbr, k))
            seen[n] = 1
        del seen
        return edges

    def get_edge_data(self, u, v, key=None, default=None):
        try:
            if key is None:
                return self._adj[u][v]
            else:
                return self._adj[u][v][key]
        except KeyError:
            return default

    @property
    def degree(self):
        degree = dict()
        weight = self._weight
        if weight is None:
            for n in self._nodes:
                nbrs = self._succ[n]
                deg = sum(len(keys) for keys in nbrs.values()) + (
                    n in nbrs and len(nbrs[n])
                )
                degree[n] = deg
        else:
            for n in self._nodes:
                nbrs = self._succ[n]
                deg = sum(
                    d.get(weight, 1)
                    for key_dict in nbrs.values()
                    for d in key_dict.values()
                )
                if n in nbrs:
                    deg += sum(d.get(weight, 1) for d in nbrs[n].values())
                degree[n] = deg
   
    def is_multigraph(self):
        return True

    def is_directed(self):
        return False

    def copy(self):
        G = self.__class__()
        G.graph.update(self.graph)
        G.add_nodes_from((n, d.copy()) for n, d in self._node.items())
        G.add_edges_from(
            (u, v, key, datadict.copy())
            for u, nbrs in self._adj.items()
            for v, keydict in nbrs.items()
            for key, datadict in keydict.items()
        )
        return G
    
    def to_directed(self, as_view=False):
        G = eg.MultiDiGraph()
        G.graph.update(deepcopy(self.graph))
        G.add_nodes_from((n, deepcopy(d)) for n, d in self._node.items())
        G.add_edges_from(
            (u, v, key, deepcopy(datadict))
            for u, nbrs in self.adj.items()
            for v, keydict in nbrs.items()
            for key, datadict in keydict.items()
        )
        return G
    

