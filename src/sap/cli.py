"""Console script for python_sap."""
import sys

import click

from sap import Sapper, load, CollectionLazy, sap


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
    graph = sap(graph)
    trunk = graph.vs.select(trunk_gt=0)
    click.echo(
        "\n".join(
            [
                str(t)
                for t in sorted(
                    zip(
                        trunk["sap"],
                        trunk["_connections"],
                        trunk["_found"],
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

    import matplotlib.pyplot as plt

    plt.figure()
    plt.plot(trunk["sap"], trunk["trunk"], "o")
    plt.grid(True)
    plt.savefig("./scratch/sap.pdf")

    plt.figure()
    plt.plot(trunk["_connections"], trunk["_found"], "o")
    plt.plot(trunk["_connections"], trunk["_crosses"], "o")
    plt.grid(True)
    plt.savefig("./scratch/conns.pdf")
