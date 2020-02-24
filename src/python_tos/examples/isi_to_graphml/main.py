from python_tos import IsiToGraph

# TODO: avoid to use path in this way, use it dinamically.
BASE_PATH = "src/python_tos/examples/isi_to_graphml"

def run():
    isi_to_grap = IsiToGraph(f"{BASE_PATH}/isi.txt")
    final_graph_file = f"{BASE_PATH}/graph.graphml"
    isi_to_grap.graph.write(final_graph_file)
    print(f"Yay! your graph file was generated, just double click {final_graph_file}")
