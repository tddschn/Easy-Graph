from easygraph.utils import nodes_or_number, pairwise
from easygraph.classes import Graph
@nodes_or_number(0)
def empty_graph(n=0, create_using=None, default=Graph):
    if create_using is None:
        G = default()
    elif hasattr(create_using, "_adj"):
        # create_using is a NetworkX style Graph
        create_using.clear()
        G = create_using
    else:
        # try create_using as constructor
        G = create_using()

    n_name, nodes = n
    G.add_nodes_from(nodes)
    return G

@nodes_or_number(0)
def path_graph(n, create_using=None):
    """Returns the Path graph `P_n` of linearly connected nodes.

    Parameters
    ----------
    n : int or iterable
        If an integer, nodes are 0 to n - 1.
        If an iterable of nodes, in the order they appear in the path.
    create_using : NetworkX graph constructor, optional (default=nx.Graph)
       Graph type to create. If graph instance, then cleared before populated.

    """
    n_name, nodes = n
    G = empty_graph(nodes, create_using)
    G.add_edges_from(pairwise(nodes))
    return G
