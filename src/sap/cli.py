"""Console script for python_sap."""
import sys

import click

from sap import Sapper, load, CollectionLazy


@click.group()
def main(args=None):
    """
    A little cli for sap.
    """


@main.command("explore")
@click.argument("sources", type=click.File("r"), nargs=-1)
def explore(sources):
    graph = next(load(CollectionLazy(*sources)))
    sap = Sapper()
    graph = sap.root(graph)
    graph = sap.leaf(graph)
    leaves = graph.vs.select(extended_leaf_gt=0)
    click.echo(
        "\n".join(
            [
                str(t)
                for t in sorted(
                    zip(
                        leaves["leaf"],
                        leaves["_connections"],
                        leaves["PY"],
                        [f"https://doi.org/{d}" for d in leaves["DI"]],
                        leaves["name"],
                    ),
                    key=lambda t: t[0],
                )
            ]
        )
    )
