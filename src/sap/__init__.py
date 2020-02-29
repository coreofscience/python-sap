"""Top-level package for Python SAP."""

import re
from datetime import date
from itertools import chain
from operator import itemgetter
from typing import Iterator, Optional

import igraph as ig
from wostools import CollectionLazy

__author__ = """Daniel Stiven Valencia Hernadez"""
__email__ = "dsvalenciah@gmail.com"
__version__ = "0.1.0"


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
        yield graph.subgraph(component)


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

    items = zip(valid_root, new_graph.vs[valid_root].indegree())

    sorted_items = sorted(items, key=itemgetter(1), reverse=True)

    valid_root = list(zip(*sorted_items))[0]

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
    connections_count = [sum([1 for i in j if isinstance(i, int)]) for j in conections]

    items = zip(new_graph.vs[potential_leaves].indices, connections_count)

    sorted_items = sorted(items, key=itemgetter(1), reverse=True)
    potential_leaves = list(zip(*sorted_items))[0]

    newer_leaf_year = max(new_graph.vs[potential_leaves]["PY"]) - 5

    for i, potential_leaf in enumerate(potential_leaves):
        publication_year = int(new_graph.vs[potential_leaf]["PY"])
        is_new_enough = publication_year >= newer_leaf_year
        if is_new_enough:
            new_graph.vs[potential_leaf]["leaf"] = connections_count[i]
        new_graph.vs[potential_leaf]["extended_leaf"] = connections_count[i]

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

    def on_find_path(source, target, path):
        for trunk in path:
            # TODO: determine properly the best value of `trunk`.
            new_graph.vs[trunk]["trunk"] += (
                new_graph.vs[leaf]["leaf"] + new_graph.vs[root]["root"]
            )
            if trunk not in trunk_indices:
                trunk_indices.append(trunk)

    adjlist = new_graph.get_adjlist()
    for root in valid_root:
        for leaf in valid_leaves:
            _paths(adjlist, leaf, root, on_find_path=on_find_path)

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
        r"".join(
            [
                "^(?P<AU>[^,]+)?, ",
                "(?P<PY>\d{4})?, ",
                "(?P<SO>[^,]+)?",
                "(, V(?P<VL>\d+))?",
                "(, P(?P<PG>\d+))?",
                "(, DOI (?P<DI>.+))?",
            ]
        )
    )

    classified_labels = [
        pattern.match(line).groupdict()
        if pattern.match(line)
        else {"AU": None, "DI": None, "PG": None, "PY": None, "SO": None, "VL": None,}
        for line in new_graph.vs["name"]
    ]

    # TODO: It's necessary to fix the year number.
    for key in ["AU", "DI", "PG", "PY", "SO", "VL"]:
        new_graph.vs[key] = [
            int(article[key] or 0) if key == "PY" else article[key]
            for article in classified_labels
        ]

    new_graph.vs["label"] = [f'{vs["PY"]}\n{vs["AU"]}' for vs in new_graph.vs]

    return new_graph
