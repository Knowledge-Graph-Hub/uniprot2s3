"""Command line interface for uniprot2s3."""

import logging

import click

from uniprot2s3 import __version__
from uniprot2s3.main import run_api

show_status_option = click.option("--show-status/--no-show-status", default=True)

__all__ = [
    "main",
]

logger = logging.getLogger(__name__)


@click.group()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet")
@click.version_option(__version__)
def main(verbose: int, quiet: bool):
    """
    CLI for uniprot2s3.

    :param verbose: Verbosity while running.
    :param quiet: Boolean to be quiet or verbose.
    """
    if verbose >= 2:
        logger.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        logger.setLevel(level=logging.INFO)
    else:
        logger.setLevel(level=logging.WARNING)
    if quiet:
        logger.setLevel(level=logging.ERROR)


@main.command()
@show_status_option
def run(show_status):
    """
    Get data via rest API.

    :param show_status: Flag to show download status or not.
    :return: None
    """
    run_api(show_status)


if __name__ == "__main__":
    main()
