import json

import igraph as ig


TEMPLATE = """
<script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<div id="mynetwork" style="height:100vh;"></div>
<style type="text/css">
    #mynetwork {
    width: 100%%;
    height: 100vh;
    border: 1px solid lightgray;
    }
</style>
<script type="text/javascript">
    function openInNewTab(url) {
    var win = window.open(url, '_blank');
    win.focus();
    }

    function draw() {
    var nodes = %(nodes)s;
    var edges = %(edges)s;
    var container = document.getElementById('mynetwork');
    var data = {
        nodes: new vis.DataSet(nodes),
        edges: new vis.DataSet(edges)
    };
    var options = {
        nodes: {
        font: {
            face: 'Tahoma',
            color: 'white'
        }
        },
        edges: {
        width: 0.15,
        smooth: {
            type: 'continuous'
        }
        },
        interaction: {
        tooltipDelay: 200,
        },
        physics: false
    };
    network = new vis.Network(container, data, options);
    network.on('doubleClick', function(params) {
        if (nodes[params.nodes].DI != null){
        openInNewTab("http://dx.doi.org/" + nodes[params.nodes].DI);
        } else {
        window.alert("Unable to open the article, doesn't have DOI");
        }
    });
    }

    draw();
</script>
"""


class Widget(object):
    def __init__(self, graph: ig.Graph):
        self.graph = graph

    @staticmethod
    def node_color(node: ig.Vertex) -> str:
        if node["root"]:
            return "brown"
        if node["leaf"]:
            return "green"
        if node["trunk"]:
            return "yellow"

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
        return TEMPLATE % {"nodes": json.dumps(nodes), "edges": json.dumps(edges)}


def display(graph):
    return Widget(graph)
