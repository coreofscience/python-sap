import json

import igraph as ig

import os

with open(os.path.join(os.path.dirname(__file__), "template.html")) as f:
    TEMPLATE = f.read()


class Widget:
    def __init__(self, graph: ig.Graph):
        self.graph = graph

    def _repr_html_(self):
        return TEMPLATE


def display(graph):
    return Widget(graph)
