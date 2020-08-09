import json

import igraph as ig

import os

with open(os.path.join(os.path.dirname(__file__), "template.html")) as f:
    TEMPLATE = f.read()


class Widget:
    def __init__(self, graph: ig.Graph):
        self.graph = graph

    def _repr_html_(self):
        nodes = [
            {**vs.attributes(), "title": vs["label"], "label": None, "id": vs.index}
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
