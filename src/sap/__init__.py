"""Top-level package for Python SAP."""

import logging
import re
from datetime import date
from itertools import chain
from operator import itemgetter
from typing import Iterator, List, Optional

import igraph as ig
from wostools import CollectionLazy

__author__ = """Daniel Stiven Valencia Hernadez"""
__email__ = "dsvalenciah@gmail.com"
__version__ = "0.1.1"

MODE_IN = "IN"
MODE_OUT = "OUT"
MODE_WEAK = "WEAK"


logger = logging.getLogger(__name__)


class Sap(object):
    def __init__(
        self,
        max_roots: Optional[int] = 20,
        max_leaves: Optional[int] = 50,
        max_trunk: Optional[int] = 20,
        min_leaf_connections: Optional[int] = 3,
        max_leaf_age: Optional[int] = 5,
        default_clear_graph: bool = True,
    ):
        self.max_roots = max_roots
        self.max_leaves = max_leaves
        self.max_trunk = max_trunk
        self.min_leaf_connections = min_leaf_connections
        self.max_leaf_age = max_leaf_age
        self.default_clear_graph = default_clear_graph

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
            neighbors = [n.index for n in new_graph.vs[index].neighbors(mode=MODE_OUT)]
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
        topological_order = new_graph.topological_sorting(mode=MODE_IN)
        for index in reversed(topological_order):
            neighbors = [n.index for n in new_graph.vs[index].neighbors(mode=MODE_IN)]
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
            neighbors = [n.index for n in new_graph.vs[index].neighbors(mode=MODE_OUT)]
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
            ignored = "\n".join(new_graph.vs.select(PY_eq=None)["name"])
            logging.info(f"Ignoring these nodes for year calculations:\n{ignored}")
            newest_publication_year: int = max(
                filter(None, new_graph.vs[potential_leaves]["PY"])
            )
            earliest_publication_year = newest_publication_year - self.max_leaf_age
            not_leaves_anymore = graph.vs.select(
                PY_ne=None, PY_gt=earliest_publication_year
            )
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
        new_graph = graph.copy()
        try:
            sap_nodes = new_graph.vs.select(root_eq=0, leaf_eq=0, sap_gt=0)
        except AttributeError:
            raise TypeError(
                "The graph needs to have a 'root', 'leaf' and 'sap' attributes"
            )
        if not sap_nodes:
            raise TypeError("The graph needs to have at least some nodes with sap")

        new_graph.vs["trunk"] = 0
        sap_nodes["trunk"] = sap_nodes["sap"]

        if self.max_trunk is not None:
            sorted_leaves = _sorted_nodes(new_graph, "trunk")
            not_leaves_anymore = sorted_leaves[self.max_trunk :]
            new_graph.vs[not_leaves_anymore]["trunk"] = 0

        return new_graph

    def clear(self, graph: ig.Graph) -> ig.Graph:
        """
        Returns a copy of the graph clear of untagged nodes.
        """
        graph = graph.copy()
        graph = graph.subgraph(
            graph.vs.select(lambda v: v["root"] > 0 or v["trunk"] > 0 or v["leaf"] > 0)
        )
        return graph

    def tree(self, graph: ig.Graph, clear: Optional[bool] = None) -> ig.Graph:
        """
        Computes the whole tree.
        """
        graph = graph.copy()
        graph = self.root(graph)
        graph = self.leaf(graph)
        graph = self.sap(graph)
        graph = self.trunk(graph)
        if (clear is not None and clear) or self.default_clear_graph:
            graph = self.clear(graph)
        return graph


def load(collection: CollectionLazy) -> Iterator[ig.Graph]:
    """
    Takes in a collection of bibliographic records and gets out all the
    connected components of their citation graph.

    :param CollectionLazy collection: bibliographic collection
    :return: iterator over the connected components
    """
    vertices = {}
    pair_labels = []
    for article, reference in collection.citation_pairs(
        pair_parser=collection.metadata_pair_parser
    ):
        art_label, vertices[art_label] = article
        ref_label, vertices[ref_label] = reference
        pair_labels.append((art_label, ref_label))

    graph = ig.Graph(directed=True)
    for label, attrs in vertices.items():
        graph.add_vertex(name=label, label=label, **attrs)

    graph.add_edges(pair_labels)
    graph = graph.simplify()
    valid_vs = graph.vs.select(lambda v: v["label"].lower() != "null").indices
    graph = graph.subgraph(valid_vs)
    valid_vs = graph.vs.select(
        lambda v: v.indegree() != 1 or v.outdegree() != 0
    ).indices
    graph = graph.subgraph(valid_vs)
    for component in graph.clusters(MODE_WEAK):
        subgraph = graph.subgraph(component)
        if len(subgraph.vs.select(_indegree_gt=0, _outdegree_gt=0)) > 0:
            yield subgraph


def giant(collection: CollectionLazy) -> ig.Graph:
    """
    Takes in a collection of bibliographic records and gets out the giant pre
    processed connected component.

    :param CollectionLazy collection: bibliographic collection
    :return: connected component graph
    """
    return next(load(collection))


def _sorted_nodes(graph: ig.Graph, by: str, reverse: bool = True) -> List[int]:
    indices = graph.vs.indices
    attribtes = graph.vs[indices][by]
    return [
        index
        for index, _attribute in sorted(
            zip(indices, attribtes), key=lambda item: item[1], reverse=reverse,
        )
    ]
