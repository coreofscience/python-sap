import os
from xml.etree.ElementTree import TreeBuilder, Element, tostring
from xml.dom.minidom import parse

import igraph as ig
from igraph import VertexSeq


def _sorted_seq(graph: ig.Graph, by: str):
    vertices = graph.vs.select(**{f"{by}_gt": 0})
    order = [
        index
        for index, _ in sorted(
            zip(vertices.indices, vertices[by]),
            key=(lambda item: item[1]),
            reverse=True,
        )
    ]
    return graph.vs[order]


def _ensure_dots(author: str) -> str:
    author = author.replace(".", "")
    first, *rest = author.split(" ")
    author = " ".join([first.title(), *rest])
    return f"{author}."


def _span(builder, name, value):
    if not value:
        return
    builder.start("span", {"class": f"Article-{name}"})
    builder.data(value)
    builder.end("span")


def _formatted_reference(vertex: ig.Vertex):
    attributes = vertex.attributes()
    builder = TreeBuilder()
    builder.start("div", {"class": "Article", "id": attributes.get("label")})

    if attributes.get("authors", []):
        _span(
            builder,
            "authors",
            "; ".join([_ensure_dots(author) for author in vertex["authors"]]),
        )
        builder.data(" ")

    if attributes.get("year"):
        _span(builder, "year", f"({vertex['year']})")
        builder.data(". ")

    if attributes.get("title"):
        _span(builder, "title", vertex["title"])
        builder.data(". ")

    if attributes.get("journal") or attributes.get("volume"):
        journal = attributes.get("journal", "") or ""
        volume = attributes.get("volume", "") or ""
        issue = attributes.get("issue", "") or ""
        page = attributes.get("page", "") or ""

        builder.start("em", {})
        _span(builder, "journal", journal.title())
        if journal and volume:
            builder.data(", ")
            _span(builder, "volume", volume.title())
        builder.end("em")

        if issue:
            _span(builder, "issue", f"({issue})")

        if page:
            builder.data(", ")
            _span(builder, "page", page)

        builder.data(".")

    if attributes.get("doi"):
        builder.data(" ")
        doi = attributes.get("doi")
        url = f"https://dx.doi.org/{doi}"
        builder.start(
            "a",
            {
                "class": "Article-doi",
                "href": url,
                "target": "_blank",
                "rel": "noreferrer",
            },
        )
        builder.data(url)
        builder.end("a")

    builder.end("div")
    return builder.close()


def _formatted_articles(seq: VertexSeq):
    formatted = Element("div", {"class": "Article-collection"})
    for vertex in seq:
        formatted.append(_formatted_reference(vertex))
    return tostring(formatted, encoding="utf-8").decode()


with open(os.path.join(os.path.dirname(__file__), "template.html")) as f:
    TEMPLATE = f.read()


class Widget:
    def __init__(self, graph: ig.Graph):
        self.graph = graph

    def _repr_html_(self):
        html = TEMPLATE[:]
        html = html.replace(
            "<!-- ROOT ARTICLES -->",
            _formatted_articles(_sorted_seq(self.graph, "root")),
        )
        html = html.replace(
            "<!-- TRUNK ARTICLES -->",
            _formatted_articles(_sorted_seq(self.graph, "trunk")),
        )
        html = html.replace(
            "<!-- LEAF ARTICLES -->",
            _formatted_articles(_sorted_seq(self.graph, "leaf")),
        )
        return html


def display(graph):
    return Widget(graph)
