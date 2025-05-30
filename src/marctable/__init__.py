from collections.abc import Callable
from typing import IO, Any, BinaryIO, TextIO

import click
from pymarc import MARCReader
from pymarc.marcxml import parse_xml_to_array

from marctable.marc import crawl
from marctable.utils import to_csv, to_jsonl, to_parquet


@click.group()
def cli() -> None:
    pass


def io_params(f: Callable) -> Callable:
    """
    Decorator for specifying input/output arguments.
    """
    f = click.argument("outfile", type=click.File("wb"), default="-")(f)
    f = click.argument("infile", type=click.File("rb"), default="-")(f)
    return f


def rule_params(f: Callable) -> Callable:
    f = click.option(
        "--rule",
        "-r",
        "rules",
        multiple=True,
        help="Specify a rule for extracting, e.g. 245 or 245a or 245ac",
    )(f)
    f = click.option(
        "--batch", "-b", default=1000, help="Batch n records when converting"
    )(f)
    return f


def avram_params(f: Callable) -> Callable:
    """
    Decorator for selecting an avram schema.
    """
    f = click.option(
        "--schema",
        "-s",
        "avram_file",
        type=click.File("rb"),
        help="Specify avram schema file",
    )(f)
    return f


@cli.command()
@io_params
@rule_params
@avram_params
def csv(
    infile: BinaryIO, outfile: TextIO, rules: list, batch: int, avram_file: BinaryIO
) -> None:
    """
    Convert MARC to CSV.
    """
    to_csv(
        _records(infile), outfile, rules=rules, batch_size=batch, avram_file=avram_file
    )


@cli.command()
@io_params
@rule_params
@avram_params
def parquet(
    infile: BinaryIO, outfile: IO[Any], rules: list, batch: int, avram_file: BinaryIO
) -> None:
    """
    Convert MARC to Parquet.
    """
    to_parquet(
        _records(infile), outfile, rules=rules, batch_size=batch, avram_file=avram_file
    )


@cli.command()
@io_params
@rule_params
@avram_params
def jsonl(
    infile: BinaryIO, outfile: BinaryIO, rules: list, batch: int, avram_file: BinaryIO
) -> None:
    """
    Convert MARC to JSON Lines (JSONL)
    """
    to_jsonl(
        _records(infile), outfile, rules=rules, batch_size=batch, avram_file=avram_file
    )


@cli.command()
@click.argument("outfile", type=click.File("w"), default="-")
def avram(outfile: TextIO) -> None:
    """
    Generate an Avram schema (JSON) from the Library of Congress MARC bibliographic web.
    """
    crawl(outfile=outfile)


def main() -> None:
    cli()


def _records(infile: BinaryIO) -> list | MARCReader:
    if infile.name.endswith(".xml"):
        return parse_xml_to_array(infile)
    else:
        return MARCReader(infile)
