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
    sapper = Sapper()
    graph = sapper.root(graph)
    graph = sapper.leaf(graph)
    graph = sapper.sap(graph)
    graph = sapper.trunk(graph)
    trunk = graph.vs.select(trunk_gt=0)
    click.echo(
        "\n".join(
            [
                str(t)
                for t in sorted(
                    zip(
                        trunk["sap"],
                        trunk["_connections"],
                        trunk["trunk"],
                        trunk["leaf"],
                        [f"https://doi.org/{d}" for d in trunk["DI"]],
                        trunk["name"],
                    ),
                    key=lambda t: t[0],
                )
            ]
        )
    )
