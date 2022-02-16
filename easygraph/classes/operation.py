import easygraph as eg

__all__ = ["selfloop_edges", "topological_sort"]

def selfloop_edges(G, data=False, default=None):
    if data is True:
        return ((n, n, nbrs[n]) for n, nbrs in G.adj.items() if n in nbrs)
    elif data is not False:
        return (
                (n, n, nbrs[n].get(data, default))
                for n, nbrs in G.adj.items()
                if n in nbrs
            )
    else:
        return ((n, n) for n, nbrs in G.adj.items() if n in nbrs)

def topological_generations(G):
    if not G.is_directed():
        raise AssertionError("Topological sort not defined on undirected graphs.")
    indegree_map = {v: d for v, d in G.in_degree() if d > 0}
    zero_indegree = [v for v, d in G.in_degree() if d == 0]
    while zero_indegree:
        this_generation = zero_indegree
        zero_indegree = []
        for node in this_generation:
            if node not in G:
                raise RuntimeError("Graph changed during iteration")
            for child in G.neighbors(node):
                try:
                    indegree_map[child] -= 1
                except KeyError as err:
                    raise RuntimeError("Graph changed during iteration") from err
                if indegree_map[child] == 0:
                    zero_indegree.append(child)
                    del indegree_map[child]
        yield this_generation

    if indegree_map:
        raise AssertionError(
            "Graph contains a cycle or graph changed during iteration"
        )

def topological_sort(G):
    for generation in eg.topological_generations(G):
        yield from generation