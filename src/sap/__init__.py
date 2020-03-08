"""Top-level package for Python SAP."""

import re
from datetime import date
from itertools import chain
from operator import itemgetter
from typing import Iterator, Optional, List

import igraph as ig
from wostools import CollectionLazy

__author__ = """Daniel Stiven Valencia Hernadez"""
__email__ = "dsvalenciah@gmail.com"
__version__ = "0.1.0"


def _sorted_nodes(graph: ig.Graph, by: str, reverse: bool = True) -> List[int]:
    indices = graph.vs.indices
    attribtes = graph.vs[indices][by]
    return [
        index
        for index, _attribute in sorted(
            zip(indices, attribtes), key=lambda item: item[1], reverse=reverse,
        )
    ]


class Sapper(object):
    def __init__(
        self,
        max_roots: Optional[int] = 20,
        max_leaves: Optional[int] = 50,
        max_trunk: Optional[int] = 20,
        min_leaf_connections: Optional[int] = 3,
        max_leaf_age: Optional[int] = 5,
    ):
        self.max_roots = max_roots
        self.max_leaves = max_leaves
        self.max_trunk = max_trunk
        self.min_leaf_connections = min_leaf_connections
        self.max_leaf_age = max_leaf_age

    def sap(self, graph: ig.Graph) -> ig.Graph:
        """
        Computes the sap of each node.
        """
        new_graph = graph.copy()
        try:
            valid_root = new_graph.vs.select(root_gt=0)
            valid_leaves = new_graph.vs.select(leaf_gt=0)
        except AttributeError:
            raise TypeError("The graph needs to have a 'root' and a 'leaf' attribute")
        if not valid_root or not valid_leaves:
            raise TypeError("The graph needs to have at least some roots and leafs")

        new_graph.vs["_raw_sap"] = 0
        new_graph.vs["_root_connections"] = 0
        valid_root["_raw_sap"] = valid_root["root"]
        valid_root["_root_connections"] = 1
        topological_order = new_graph.topological_sorting()
        for index in reversed(topological_order):
            neighbors = [n.index for n in new_graph.vs[index].neighbors(mode=ig.OUT)]
            if neighbors:
                new_graph.vs[index]["_raw_sap"] = sum(
                    new_graph.vs[neighbors]["_raw_sap"]
                )
                new_graph.vs[index]["_root_connections"] = sum(
                    new_graph.vs[neighbors]["_root_connections"]
                )

        new_graph.vs["_elaborate_sap"] = 0
        new_graph.vs["_leaf_connections"] = 0
        valid_leaves["_elaborate_sap"] = valid_leaves["leaf"]
        valid_leaves["_leaf_connections"] = 1
        topological_order = new_graph.topological_sorting(mode=ig.IN)
        for index in reversed(topological_order):
            neighbors = [n.index for n in new_graph.vs[index].neighbors(mode=ig.IN)]
            if neighbors:
                new_graph.vs[index]["_elaborate_sap"] = sum(
                    new_graph.vs[neighbors]["_elaborate_sap"]
                )
                new_graph.vs[index]["_leaf_connections"] = sum(
                    new_graph.vs[neighbors]["_leaf_connections"]
                )

        new_graph.vs["sap"] = [
            v["_leaf_connections"] * v["_raw_sap"]
            + v["_root_connections"] * v["_elaborate_sap"]
            for v in new_graph.vs
        ]

        return new_graph

    def root(self, graph: ig.Graph) -> ig.Graph:
        """
        Takes in a connected graph and returns it labeled with a `root` property.

        :return: Labeled graph with the root property.
        """
        new_graph = graph.copy()
        valid_root = new_graph.vs.select(_outdegree_eq=0).indices

        for attr in ("root", "extended_root"):
            new_graph.vs[attr] = 0
            new_graph.vs[valid_root][attr] = new_graph.vs[valid_root].indegree()

        if self.max_roots is not None:
            sorted_roots = _sorted_nodes(new_graph, "root")
            not_roots_anymore = sorted_roots[self.max_roots :]
            new_graph.vs[not_roots_anymore]["root"] = 0

        return new_graph

    def leaf(self, graph: ig.Graph) -> ig.Graph:
        """
        Takes in a connected graph and returns it labeled with a `leaf` property.
        :param graph: Connected and filtered graph to work with.
        :param roots: Max number of roots to consider.
        :param leaves: Max number of leaves to consider.
        :return: Labeled graph with the leaf property.
        """
        new_graph = graph.copy()
        try:
            valid_root = new_graph.vs.select(root_gt=0).indices
        except AttributeError:
            raise TypeError("It's necessary to have some roots")
        if not valid_root:
            raise TypeError("It's necessary to have some roots")

        new_graph.vs["_connections"] = 0
        new_graph.vs[valid_root]["_connections"] = 1
        topological_order = new_graph.topological_sorting()
        for index in reversed(topological_order):
            neighbors = [n.index for n in new_graph.vs[index].neighbors(mode=ig.OUT)]
            if neighbors:
                new_graph.vs[index]["_connections"] = sum(
                    new_graph.vs[neighbors]["_connections"]
                )

        potential_leaves = new_graph.vs.select(_indegree_eq=0).indices
        leaf_connections = new_graph.vs[potential_leaves]["_connections"]

        for attr in ("leaf", "extended_leaf"):
            new_graph.vs[attr] = 0
            new_graph.vs[potential_leaves][attr] = leaf_connections

        if self.min_leaf_connections is not None:
            not_leaves_anymore = new_graph.vs.select(leaf_lt=self.min_leaf_connections)
            not_leaves_anymore["leaf"] = 0

        if self.max_leaf_age is not None:
            newest_publication_year = max(new_graph.vs[potential_leaves]["PY"])
            earliest_publication_year = newest_publication_year - self.max_leaf_age
            not_leaves_anymore = graph.vs.select(PY_gt=earliest_publication_year)
            not_leaves_anymore["leaf"] = 0

        if self.max_leaves is not None:
            sorted_leaves = _sorted_nodes(new_graph, "leaf")
            not_leaves_anymore = sorted_leaves[self.max_leaves :]
            new_graph.vs[not_leaves_anymore]["leaf"] = 0

        return new_graph

    def trunk(self, graph: ig.Graph) -> ig.Graph:
        """
        Tags leaves.
        """
        return graph

    def tree(self, graph: ig.Graph) -> ig.Graph:
        """
        Tags leaves.
        """
        return graph


def tos_sap(collection: CollectionLazy):
    """
    Takes in a connected graph and returns it with `root`, `leave` and `trunk`
    properties.

    This function probably only calls other functions.
    :param graph: Filtered and connected graph to work with.
    :return: Labeled graph with root, trunk and leaves.
    """
    tree_parts = ["root", "leaf", "extended_leaf", "trunk", "potential_leaf"]
    for tree in load(collection):
        print(tree.summary())
        try:
            tree = root(tree)
            tree = leaf(tree)
            tree = sap(tree)
            for part in tree_parts:
                count = len(tree.vs.select(**{f"{part}_gt": 0}))
                print(f"{part}: {count}")
        except BaseException as e:
            print(e)
        print()


def load(collection: CollectionLazy) -> Iterator[ig.Graph]:
    """
    Takes in a list of ISI files (or filenames) and spits out an iterator over their
    connected components.

    This function might be responsible for our filters.
    :param isi_files: List of files.
    :return: Filtered connected components.
    """
    pairs = list(collection.citation_pairs())
    nodes = list(set(chain.from_iterable(pairs)))
    graph = ig.Graph(directed=True)
    graph.add_vertices(nodes)
    graph.add_edges(pairs)
    graph = _build_attributes(graph)
    graph = graph.simplify()
    valid_vs = graph.vs.select(lambda v: v["label"].lower() != "null").indices
    graph = graph.subgraph(valid_vs)
    valid_vs = graph.vs.select(
        lambda v: v.indegree() != 1 or v.outdegree() != 0
    ).indices
    graph = graph.subgraph(valid_vs)
    for component in graph.clusters(ig.WEAK):
        # TODO: maybe we can decide if yield that according to some conditions
        subgraph = graph.subgraph(component)
        if subgraph.vcount() > 1 and subgraph.ecount() > 1:
            yield subgraph


def root(graph: ig.Graph) -> ig.Graph:
    """
    Takes in a connected graph and returns it labeled with a `root` property.
    :param graph: Connected and filtered graph to work with.
    :param cap: Max number of roots to consider.
    :return: Labeled graph with the root property.
    """
    new_graph = graph.copy()
    new_graph.vs["root"] = 0
    valid_root = new_graph.vs.select(_outdegree_eq=0).indices
    new_graph.vs[valid_root]["root"] = new_graph.vs[valid_root].indegree()
    return new_graph


def leaf(graph: ig.Graph) -> ig.Graph:
    """
    Takes in a connected graph and returns it labeled with a `leaf` property.
    :param graph: Connected and filtered graph to work with.
    :param roots: Max number of roots to consider.
    :param leaves: Max number of leaves to consider.
    :return: Labeled graph with the leaf property.
    """
    new_graph = graph.copy()

    try:
        valid_root = new_graph.vs.select(root_gt=0).indices
    except AttributeError:
        raise TypeError("It's necessary to have some roots")

    if not valid_root:
        raise TypeError("It's necessary to have some roots")

    potential_leaves = new_graph.vs.select(_indegree_eq=0).indices

    # Connections between roots and leaves.
    conections = new_graph.shortest_paths_dijkstra(
        source=potential_leaves, target=valid_root
    )

    new_graph.vs["leaf"] = 0
    new_graph.vs["extended_leaf"] = 0

    # Connections count of leaves with roots.
    # TODO: There are two options (select one of them):
    # 1. path count with roots.
    # 2. root conected count (currently this is the used option).
    connection_counts = [
        sum([1 for i in connection_lenghts if isinstance(i, int)])
        for connection_lenghts in conections
    ]

    new_graph.vs["leaf"] = 0
    new_graph.vs["extended_leaf"] = 0
    new_graph.vs[potential_leaves]["leaf"] = connection_counts

    newest_publication_year = max(new_graph.vs[potential_leaves]["PY"])
    earliest_publication_year = newest_publication_year - self.max_leaf_age

    for i, potential_leaf in enumerate(potential_leaves):
        publication_year = int(new_graph.vs[potential_leaf]["PY"])
        is_new_enough = publication_year >= earliest_publication_year
        if is_new_enough:
            new_graph.vs[potential_leaf]["leaf"] = connection_counts[i]
        new_graph.vs[potential_leaf]["extended_leaf"] = connection_counts[i]

    return new_graph


def sap(
    graph: ig.Graph, root_cap: Optional[int] = None, leaf_cap: Optional[int] = None
) -> ig.Graph:
    """
    Takes in a connected and labeled graph and returns it labeled with a `sap`
    property.

    This one requires the properties `leaf` and `root`
    :param graph: Labeled, filtered and connected graph to work with.
    :param roots: Max number of roots to consider.
    :param leaves: Max number of leaves to consider.
    :return: The graph labeled with the sap property.
    """
    new_graph = graph.copy()

    try:
        valid_root = new_graph.vs.select(root_gt=0).indices
    except AttributeError:
        raise TypeError("It's necessary to have some roots")
    if root_cap and root_cap < len(valid_root):
        root_items = zip(valid_root, new_graph.vs[valid_root]["root"])
        sorted_root_indices = sorted(root_items, key=itemgetter(1), reverse=True)
        valid_root = sorted_root_indices[:root_cap]

    try:
        valid_leaves = new_graph.vs.select(leaf_gt=0).indices
    except AttributeError:
        raise TypeError("It's necessary to have some leaves")
    if leaf_cap and leaf_cap < len(valid_leaves):
        root_items = zip(valid_leaves, new_graph.vs[valid_leaves]["leaf"])
        sorted_root_indices = sorted(root_items, key=itemgetter(1), reverse=True)
        valid_leaves = sorted_root_indices[:leaf_cap]

    if not valid_root or not valid_leaves:
        raise TypeError("It's necessary to have some roots and leaves")

    trunk_indices = []
    new_graph.vs["trunk"] = 0
    new_graph.vs["_found"] = 0
    new_graph.vs["_crosses"] = 0

    def on_find_path(source, target, path):
        for trunk in path:
            # TODO: determine properly the best value of `trunk`.
            new_graph.vs[trunk]["trunk"] += (
                new_graph.vs[leaf]["leaf"] + new_graph.vs[root]["root"]
            )
            new_graph.vs[trunk]["_found"] += 1
            if trunk not in trunk_indices:
                trunk_indices.append(trunk)

    adjlist = new_graph.get_adjlist()
    for root in valid_root:
        for leaf in valid_leaves:
            _paths(adjlist, leaf, root, on_find_path=on_find_path)

    for root in valid_root:
        for leaf in valid_leaves:
            paths = new_graph.get_all_simple_paths(leaf, root)
            for path in paths:
                for vertex in path:
                    new_graph.vs[vertex]["_crosses"] += 1

    items = zip(trunk_indices, new_graph.vs[trunk_indices]["trunk"])

    sorted_items = sorted(items, key=itemgetter(1), reverse=True)

    valid_trunk = list(zip(*sorted_items))[0]

    potential_leaves = []
    new_graph.vs["potential_leaf"] = 0

    latest_year = max(new_graph.vs[valid_trunk]["PY"])
    potential_leaves = new_graph.vs.select(trunk_gt=0, PY_gt=latest_year - 5)
    potential_leaves["potential_leaf"] = potential_leaves["trunk"]

    return new_graph


def _paths(adjlist, source, target, path=[], on_find_path=None):
    # TODO: kill me and use `Graph.get_all_simple_paths`.
    if source == target and callable(on_find_path):
        final_path = path.copy()
        # Remove last position because this is the same target vertex.
        # e.g target=55 and path=[22, 31, 55]:
        # We need just the path wituhout include source and target.
        final_path = final_path[:-1]
        if final_path:
            on_find_path(source, target, final_path)
        return
    for new_source in adjlist[source]:
        if new_source in path:
            continue
        path.append(new_source)
        _paths(adjlist, new_source, target, path, on_find_path=on_find_path)
        path.pop()


def _build_attributes(graph: ig.Graph) -> ig.Graph:
    new_graph = graph.copy()
    pattern = re.compile(
        r"""^(?P<AU>[^,]+)?,[ ]         # First author
            (?P<PY>\d{4})?,[ ]          # Publication year
            (?P<SO>[^,]+)?              # Journal
            (,[ ]V(?P<VL>[\w\d-]+))?    # Volume
            (,[ ][Pp](?P<PG>\d+))?      # Start page
            (,[ ]DOI[ ](?P<DI>.+))?     # The all important DOI
            """,
        re.X,
    )

    classified_labels = [
        pattern.match(line).groupdict()
        if pattern.match(line)
        else {"AU": None, "DI": None, "PG": None, "PY": None, "SO": None, "VL": None,}
        for line in new_graph.vs["name"]
    ]

    for key in ["AU", "DI", "PG", "PY", "SO", "VL"]:
        new_graph.vs[key] = [
            int(article[key] or 0) if key == "PY" else article[key]
            for article in classified_labels
        ]

    new_graph.vs["label"] = [f'{vs["PY"]}\n{vs["AU"]}' for vs in new_graph.vs]

    return new_graph
