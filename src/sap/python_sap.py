from operator import itemgetter
from datetime import date
import igraph as ig
import re


class TreeOfScienceSap:

    def __init__(self, graphml_path):
        self.current_year = date.today().year
        self.graph = ig.Graph(directed=True)
        self.graph = self.graph.Read_GraphML(graphml_path)
        self.preprocess_graph()

    def preprocess_graph(self):
        print(f"vcount: {self.graph.vcount()}")
        print(f"ecount: {self.graph.ecount()}")

        self.graph = self.graph.clusters(ig.WEAK).giant()

        self.graph = self.graph.simplify()

        valid_vs = self.graph.vs.select(
            lambda v: v["label"].lower() != "null"
        ).indices

        self.graph = self.graph.subgraph(valid_vs)

        self.build_attributes()

        self.graph.vs["sap"] = 0

    def root(self, count=10):
        # TODO: determine properly the best value of `count`.
        valid_vs = self.graph.vs.select(_outdegree_eq=0).indices

        items = zip(
            valid_vs,
            self.graph.vs[valid_vs].indegree()
        )

        sorted_items = sorted(items, key=itemgetter(1), reverse=True)

        root_indices = list(zip(*sorted_items))[0][:count]

        # Root sap vertices are the indegree.
        for index in root_indices:
            self.graph.vs[index]["sap"] = self.graph.vs[index].indegree()

        return root_indices

    def leaf(self, root_indices, count=60):
        # TODO: determine properly the best value of `count`.

        valid_vs = self.graph.vs.select(_indegree_eq=0).indices

        conections = self.graph.shortest_paths_dijkstra(
            source=valid_vs, target=root_indices
        )

        root_sap = [
            sum([1 for i in j if isinstance(i, int)])
            for j in conections
        ]

        # Leaf sap vertices are the count of connections with root vertices.
        for i, vs_index in enumerate(valid_vs):
            self.graph.vs[vs_index]["sap"] = root_sap[i]

        items = zip(
            self.graph.vs[valid_vs].indices,
            root_sap
        )

        sorted_items = sorted(items, key=itemgetter(1), reverse=True)
        valid_leaves = list(zip(*sorted_items))[0][:count]

        # TODO: determine properly the best value of `min_connections`.
        min_connections = 3
        leaf_indices = []
        # TODO: determine properly the best value of `older_leaf_years`.
        older_leaf_years = 5
        # Filter leaf vertices that are older than most old of
        # leaves less `older_leaf_years` years.
        # Filter leaf vertices that has more of `min_connections`.
        for valid_leaf in valid_leaves:
            # Article published year.
            article_py = int(self.graph.vs[valid_leaf]["PY"])
            has_min_connections = self.graph.vs[valid_leaf]["sap"] > min_connections
            # TODO: compare aticle published year with newest article
            # published year instead current year.
            is_enough_newer = (
                article_py >= self.current_year - older_leaf_years
            )
            if has_min_connections and is_enough_newer:
                leaf_indices.append(valid_leaf)

        return leaf_indices

    def trunk(self, root_indices, leaf_indices, count=10):
        # TODO: determine properly the best value of `count`.
        trunk_indices = []

        def on_find_path(source, target, path):
            for trunk in path:
                # TODO: determine properly the best value of trunk sap.
                self.graph.vs[trunk]["sap"] += (
                    self.graph.vs[leaf]["sap"] + self.graph.vs[root]["sap"]
                )
                if trunk not in trunk_indices:
                    trunk_indices.append(trunk)

        adjlist = self.graph.get_adjlist()
        for root in root_indices:
            for leaf in leaf_indices:
                self.paths(adjlist, leaf, root, on_find_path=on_find_path)

        # Trunk sap are the accumulate of sap of all connected leaves and
        # trunks
        trunk_sap = [self.graph.vs[index]["sap"] for index in trunk_indices]

        items = zip(trunk_indices, trunk_sap)

        sorted_items = sorted(items, key=itemgetter(1), reverse=True)

        try:
            valid_trunk = list(zip(*sorted_items))[0][:count]
        except IndexError:
            valid_trunk = []

        try:
            # The rest of trunk vertices are consider temporarily as leaves
            # candidates.
            leaf_candidates = list(zip(*sorted_items))[0][count:]
        except IndexError:
            leaf_candidates = []

        # TODO: determine properly the best value of `min_connections`.
        min_connections = 3
        # TODO: determine properly the best value of `older_leaf_years`.
        older_leaf_years = 5
        # Filter leaf candidates that are older than 
        index = 0
        for leaf_candidate in leaf_candidates:
            article_py = int(self.graph.vs[leaf_candidate]["PY"])
            has_min_connections = (
                self.graph.vs[leaf_candidate]["sap"] > min_connections
            )
            # TODO: compare aticle published year with newest article
            # published year instead current year.
            is_enough_newer = (
                article_py >= self.current_year - older_leaf_years
            )
            if has_min_connections and is_enough_newer:
                leaf_indices.insert(index, leaf_candidate)
                index += 1

        return valid_trunk

    def paths(self, adjlist, source, target, path=[], on_find_path=None):
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
            self.paths(adjlist, new_source, target, path, on_find_path=on_find_path)
            path.pop()

    def build_attributes(self):
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
            if pattern.match(line) else {
                "AU": None,
                "DI": None,
                "PG": None,
                "PY": None,
                "SO": None,
                "VL": None,
            }
            for line in self.graph.vs["label"]
        ]

        for key in ["AU", "DI", "PG", "PY", "SO", "VL"]:
            self.graph.vs[key] = [
                article[key] for article in classified_labels
            ]

        article_keys = {
            "AU": "Author",
            "DI": "Doi",
            "PG": "Page",
            "PY": "Published year",
            "SO": "Journal",
            "VL": "Volume"
        }

        self.graph.vs["title"] = [
            "<br>".join(
                [
                    "{}: {}".format(
                        article_keys[x], vs[x]
                        if vs[x] is not None else "N/A"
                    )
                    for x in article_keys.keys()
                ]
            )
            for vs in self.graph.vs
        ]

        self.graph.vs["label"] = [
            f'{vs["PY"]}\n{vs["AU"]}'
            for vs in self.graph.vs
        ]
