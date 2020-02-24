import json

from python_sap import TreeOfScienceSap

from jinja2 import Environment, FileSystemLoader

# TODO: avoid to use path in this way, use it dinamically.
BASE_PATH = "src/python_sap/examples/visjs_export"

env = Environment(
    autoescape=False,
    loader=FileSystemLoader(BASE_PATH),
    trim_blocks=False
)

def get_tree_graph(graphml_path):
    tree = TreeOfScienceSap(graphml_path)
    root_indices = tree.root()
    leaf_indices = tree.leaf(root_indices)
    trunk_indices = tree.trunk(root_indices, leaf_indices)

    tree_parts = {
        "leaf": leaf_indices,
        "trunk": trunk_indices,
        "root": root_indices
    }

    def get_color_by_group(group):
        if group == "leaf":
            return "#4CAC33"
        elif group == "trunk":
            return "#824D1E"
        elif group == "root":
            return "#F5A200"

    tree.graph.vs["group"] = None
    tree.graph.vs["color"] = None
    tree.graph.vs["value"] = None

    tree_indices = []

    for key in tree_parts:
        for v_index in tree_parts[key]:
            tree_indices.append(v_index)
            tree.graph.vs[v_index]["group"] = key
            tree.graph.vs[v_index]["color"] = get_color_by_group(key)
            tree.graph.vs[v_index]["value"] = tree.graph.vs[v_index]["sap"]

    tree_graph = tree.graph.subgraph(tree_indices)

    # We shouldn"t use this, because the tree graph must a unique
    # component.
    # tree_graph = tree_graph.clusters(ig.WEAK).giant()
    # TODO: test with some wos searches and make sure that all tree_graph
    # results are full connected graph

    return tree_graph



def graph_to_html(tree_graph, tree_path, graph_template_path):
    tree_graph.vs["id"] = tree_graph.vs.indices

    nodes = [
        vs.attributes()
        for vs in tree_graph.vs
    ]

    edges = [
        {
            "from": es.tuple[0],
            "to": es.tuple[1],
            "arrows":"to"
        }
        for es in tree_graph.es
    ]
    view = env.get_template(graph_template_path)
    html_content = view.render(
        nodes=json.dumps(nodes, indent=2, sort_keys=True),
        edges=json.dumps(edges, indent=2, sort_keys=True)
    )

    with open(tree_path, "w") as html_file:
        html_file.write(html_content)

def run():
    final_tree_file = f"{BASE_PATH}/tree.html"

    tree = get_tree_graph(f"{BASE_PATH}/graph.graphml")
    graph_to_html(tree, final_tree_file, "graph_template.html")
    print(f"Yay! your tree was generated, just see {final_tree_file}")
