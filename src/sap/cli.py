"""Console script for python_sap."""
import logging

import click

from sap import CollectionLazy, Sap, giant, load

logger = logging.getLogger(__name__)


@click.group()
@click.option("--max-roots", "-r", help="Max number of roots", type=int, default=None)
@click.option(
    "--max-trunk", "-t", help="Max number of trunk nodes", type=int, default=None
)
@click.option("--max-leaves", "-l", help="Max number of leaves", type=int, default=None)
@click.option(
    "--max-leaf-age",
    "-a",
    help="Maximum age of a leaf (relative to the newest article)",
    type=int,
    default=None,
)
@click.option(
    "--min-leaf-conns",
    "-c",
    "min_leaf_connections",
    help="Minimum number of connections to the roots required for a leaf",
    type=int,
    default=None,
)
@click.option(
    "--whole-graph",
    "-w",
    help="Don't discard extra nodes when building a tree",
    is_flag=True,
    default=False,
)
@click.option("--verbose", "-v", count=True, help="Show some debug information")
@click.pass_context
def main(ctx, whole_graph, verbose, **kwargs):
    """
    A little cli for sap.

    Trick: pass negative values to the options to make the number unlimited.
    """
    ctx.ensure_object(dict)
    ctx.obj["sapper"] = Sap(
        default_clear_graph=not whole_graph,
        **{
            key: value if value > 0 else None
            for key, value in kwargs.items()
            if value is not None
        },
    )
    if verbose == 1:
        logging.basicConfig(level=logging.ERROR)
    if verbose == 2:
        logging.basicConfig(level=logging.INFO)
    if verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)


@main.command()
@click.argument("sources", type=click.File("r"), nargs=-1)
@click.option("--output", "-o", type=click.File("w"), default="-")
@click.pass_context
def export(ctx, sources, output):
    """
    Creates a tree from a set of files and stores it in graphml format.
    """
    sapper = ctx.obj["sapper"]
    graph = giant(CollectionLazy(*sources))
    graph = sapper.tree(graph)
    graph.write(output, format="graphml")


@main.command()
@click.argument("sources", type=click.File("r"), nargs=-1)
@click.option("--output", "-o", type=click.File("w"), default="-")
@click.pass_context
def describe(ctx, sources, output):
    """
    Describe every graph in a given bibliography collection.
    """
    sapper = ctx.obj["sapper"]
    for graph in load(CollectionLazy(*sources)):
        try:
            graph = sapper.tree(graph)
            click.echo(graph.summary() + "\n")
        except TypeError:
            logger.exception(
                f"There was an error processin the graph\n{graph.summary()}"
            )


@main.command()
@click.argument("sources", type=click.File("r"), nargs=-1)
@click.option("--output", "-o", type=click.File("w"), default="-")
@click.option(
    "--open",
    "_open",
    default=0,
    help="open this many articles on your browser",
    show_default=True,
)
@click.pass_context
def trunk(ctx, sources, output, _open):
    """
    Computes and shows the trunk of the biggest tree on a bibliography collection.
    """
    show("trunk", ctx.obj["sapper"], sources, output, _open)


@main.command()
@click.argument("sources", type=click.File("r"), nargs=-1)
@click.option("--output", "-o", type=click.File("w"), default="-")
@click.option("--open", "_open", is_flag=True, default=False)
@click.option(
    "--open",
    "_open",
    default=0,
    help="open this many articles on your browser",
    show_default=True,
)
@click.pass_context
def leaf(ctx, sources, output, _open):
    """
    Computes and shows the leaf of the biggest tree on a bibliography collection.
    """
    show("leaf", ctx.obj["sapper"], sources, output, _open)


@main.command()
@click.argument("sources", type=click.File("r"), nargs=-1)
@click.option("--output", "-o", type=click.File("w"), default="-")
@click.option(
    "--open",
    "_open",
    default=0,
    help="open this many articles on your browser",
    show_default=True,
)
@click.pass_context
def root(ctx, sources, output, _open):
    """
    Computes and shows the root of the biggest tree on a bibliography collection.
    """
    show("root", ctx.obj["sapper"], sources, output, _open)


def show(part, sapper, sources, output, _open):
    for graph in load(CollectionLazy(*sources)):
        tree = sapper.tree(graph)
        items = sorted(
            [
                (vs[part], vs["name"], vs["DI"])
                for vs in tree.vs.select(**{f"{part}_gt": 0})
            ],
            key=lambda t: t[0],
            reverse=True,
        )
        first, *_ = items
        max_val = first[0]
        for i, (value, name, doi) in enumerate(items):
            output.write(
                " ".join(
                    [
                        f"{value/max_val:.2f}",
                        name,
                        f"https://dx.doi.org/{doi}" if doi else "",
                        "\n",
                    ]
                )
            )
            if i < _open and doi:
                click.launch(f"https://dx.doi.org/{doi}")
