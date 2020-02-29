"""Console script for python_sap."""
import sys

import click
from wostools import CollectionLazy

from sap import tos_sap


@click.group()
def main(args=None):
    """
    A little cli for sap.
    """


@main.command("explore")
@click.argument("sources", type=click.File("r"), nargs=-1)
def explore(sources):
    collection = CollectionLazy(*sources)
    tos_sap(collection)
