import json

import igraph as ig
from IPython.core.display import HTML

import os

with open(os.path.join(os.path.dirname(__file__), "template.html")) as f:
    TEMPLATE = f.read()


class Widget(object):
    def __init__(self, graph: ig.Graph):
        self.graph = graph

    @staticmethod
    def node_color(node: ig.Vertex) -> str:
        if node["root"]:
            return "#F5A200"
        if node["leaf"]:
            return "#4CAC33"
        if node["trunk"]:
            return "#824D1E"

    def _repr_html_(self):
        nodes = [
            {
                **vs.attributes(),
                "title": vs["label"],
                "label": None,
                "id": vs.index,
                "color": self.node_color(vs),
            }
            for vs in self.graph.vs
        ]
        edges = [
            {"from": es.tuple[0], "to": es.tuple[1], "arrows": "to"}
            for es in self.graph.es
        ]
        return TEMPLATE.replace('"__NODES__"', json.dumps(nodes)).replace(
            '"__EDGES__"', json.dumps(edges)
        )


def display(graph):
    return Widget(graph)
