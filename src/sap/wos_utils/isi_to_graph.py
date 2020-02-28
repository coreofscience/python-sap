import python_tos.utils as wos_utils

import igraph as ig


class IsiToGraph():

    def __init__(self, isi_file_path):
        self.graph = ig.Graph()
        self.__build_graph(isi_file_path)

    def __build_graph(self, isi_file_path):
        entries = list(
            map(
                wos_utils.parse_entry,
                open(isi_file_path, 'r').read().split('\nER\n\n')
            )
        )[:-1]
        labels = wos_utils.get_label_list(entries)

        duplicates = wos_utils.detect_duplicate_labels(labels)
        unique_labels = list(set(wos_utils.patch_list(labels, duplicates)))
        edge_relations = wos_utils.extract_edge_relations(entries)
        unique_edge_relations = list(set(
            wos_utils.patch_tuple_list(edge_relations, duplicates)
        ))

        identifiers = dict(zip(unique_labels, range(len(unique_labels))))
        self.graph = ig.Graph(
            wos_utils.patch_tuple_list(unique_edge_relations, identifiers),
            directed=True
        )

        self.graph.vs['label'] = unique_labels
        self.graph.vs['betweenness'] = self.graph.betweenness()
