"""Console script for python_sap."""
import sys
import click

import python_sap.examples as examples

PACKAGE_EXAMPLES = {
    "visj_export": examples.visj_export
}

@click.group()
def main(args=None):
    """
    A little cli for wos tools.
    """

@main.command("run-example")
@click.argument('name')
def run_example(name):
    example = PACKAGE_EXAMPLES.get(name)
    if callable(example):
        example()
    else:
        click.echo("script name not allowed", err=True)
