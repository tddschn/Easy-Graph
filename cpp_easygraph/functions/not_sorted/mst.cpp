#include "mst.h"


#include <pybind11/stl.h>

#include <cmath>

#include "../../classes/graph.h"
UnionFind::UnionFind(std::vector<node_t> elements) {
    for (node_t x : elements) {
        parents[x] = x;
        weights[x] = 1;
    }
}
node_t UnionFind::operator[](node_t object) {
    if (!parents.count(object)) {
        parents[object] = object;
        weights[object] = 1;
        return object;
    }

    std::vector<node_t> path;
    path.push_back(object);
    node_t root = parents[object];
    while (root != path.back()) {
        path.push_back(root);
        root = parents[root];
    }
    for (node_t ancestor : path) {
        parents[ancestor] = root;
    }
    return root;
}

void UnionFind::_union(node_t object1, node_t object2) {
    node_t root, r;
    if (weights[object1] < weights[object2]) {
        root = object1, r = object2;
    } else {
        root = object2, r = object1;
    }
    weights[root] += weights[r];
    parents[r] = root;
}
struct mst_Edge {
    double wt;
    node_t start_node, end_node;
    edge_attr_dict_factory edge_attr;
    mst_Edge(double wt, node_t start_node, node_t end_node, edge_attr_dict_factory edge_attr) {
        this->wt = wt;
        this->start_node = start_node;
        this->end_node = end_node;
        this->edge_attr = edge_attr;
    }
};
struct cmp {
    bool operator()(const mst_Edge &node1, const mst_Edge &node2) {
        return node1.wt > node2.wt;
    }
};
py::object cpp_prim_mst_edges(py::object G, py::object minimum, py::object weight, py::object data, py::object ignore_nan) {
    Graph &G_ = G.cast<Graph &>();
    py::list res = py::list();
    node_dict_factory nodes_list = G_.node;
    std::unordered_set<node_t> nodes;
    for (node_dict_factory::iterator iter = nodes_list.begin(); iter != nodes_list.end(); iter++) {
        node_t node_id = iter->first;
        nodes.emplace(node_id);
    }
    int sign = 1;
    if (!minimum.cast<bool>()) {
        sign = -1;
    }
    while (!nodes.empty()) {
        const node_t u = *(nodes.begin());
        nodes.erase(nodes.begin());
        std::priority_queue<mst_Edge, std::vector<mst_Edge>, cmp> frontier;
        std::unordered_map<node_t, bool> visited;
        node_t u_ = u;
        visited.emplace(u_, true);
        adj_attr_dict_factory u_neighbors = G_.adj[u];
        for (adj_attr_dict_factory::iterator i = u_neighbors.begin(); i != u_neighbors.end(); i++) {
            node_t v = i->first;
            edge_attr_dict_factory d = i->second;
            double wt = sign;
            if (d.find(py::cast<std::string>(weight)) != d.end()) {
                wt = d[py::cast<std::string>(weight)] * sign;
            }
            if (isnan(wt)) {
                if (ignore_nan.cast<bool>()) {
                    continue;
                }
                py::dict temp_attr = py::dict();
                for (edge_attr_dict_factory::iterator j = d.begin(); j != d.end(); j++) {
                    temp_attr[py::cast(j->first)] = py::cast(j->second);
                }
                PyErr_Format(PyExc_ValueError, "NaN found as an edge weight. Edge {(%R %R %R)}", (G_.id_to_node.attr("get")(u)).ptr(), G_.id_to_node.attr("get")(v).ptr(), temp_attr.ptr());
                return py::none();
            }
            frontier.push(mst_Edge(wt, u_, v, d));
        }
        while (!frontier.empty()) {
            mst_Edge node = frontier.top();
            frontier.pop();
            double W = node.wt;
            node_t u_id = node.start_node;
            node_t v_id = node.end_node;
            edge_attr_dict_factory d = node.edge_attr;
            if (visited.find(v_id) != visited.end() || nodes.find(v_id) == nodes.end()) {
                continue;
            }
            if (data.cast<bool>()) {
                py::dict temp_attr = py::dict();
                for (edge_attr_dict_factory::iterator j = d.begin(); j != d.end(); j++) {
                    temp_attr[py::cast(j->first)] = py::cast(j->second);
                }
                res.append(py::make_tuple(G_.id_to_node.attr("get")(u_id), G_.id_to_node.attr("get")(v_id), temp_attr));
            } else {
                res.append(py::make_tuple(G_.id_to_node.attr("get")(u_id), G_.id_to_node.attr("get")(v_id)));
            }
            visited.emplace(v_id, true);
            nodes.erase(v_id);
            adj_attr_dict_factory v_neighbors = G_.adj[v_id];
            for (adj_attr_dict_factory::iterator j = v_neighbors.begin(); j != v_neighbors.end(); j++) {
                node_t w = j->first;
                edge_attr_dict_factory d2 = j->second;
                if (visited.find(w) != visited.end()) {
                    continue;
                }
                double new_weight = sign;
                if (d2.find(py::cast<std::string>(weight)) != d2.end()) {
                    new_weight = d2[py::cast<std::string>(weight)] * sign;
                }
                frontier.push(mst_Edge(new_weight, v_id, w, d2));
            }
        }
    }
    return res;
}