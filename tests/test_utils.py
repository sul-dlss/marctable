import pathlib

import pandas
from pymarc import MARCReader
from marctable.utils import dataframe_iter, to_csv, to_dataframe, to_parquet


def test_to_dataframe() -> None:
    df = to_dataframe(MARCReader(open("test-data/utf8.marc", "rb")))
    assert len(df.columns) == 215
    assert len(df) == 10612
    assert df.iloc[0]["F008"] == "000110s2000    ohu    f   m        eng  "
    # 245 is not repeatable
    assert (
        df.iloc[0]["F245"]
        == "Leak testing CD-ROM [computer file] / technical editors, Charles N. "
        "Jackson, Jr., Charles N. Sherlock ; editor, Patrick O. Moore."
    )
    # 650 is repeatable
    assert df.iloc[0]["F650"] == ["Leak detectors.", "Gas leakage."]


def test_dataframe_iter() -> None:
    dfs = dataframe_iter(MARCReader(open("test-data/utf8.marc", "rb")), batch_size=1000)
    df = next(dfs)
    assert type(df), pandas.DataFrame
    assert len(df) == 1000


def test_to_csv() -> None:
    to_csv(
        MARCReader(open("test-data/utf8.marc", "rb")),
        open("test-data/utf8.csv", "w"),
        batch_size=1000,
    )
    df = pandas.read_csv("test-data/utf8.csv")
    assert len(df) == 10612
    assert len(df.columns) == 215
    assert (
        df.iloc[0]["F245"]
        == "Leak testing CD-ROM [computer file] / technical editors, Charles N. "
        "Jackson, Jr., Charles N. Sherlock ; editor, Patrick O. Moore."
    )


def test_to_parquet() -> None:
    to_parquet(
        MARCReader(open("test-data/utf8.marc", "rb")),
        open("test-data/utf8.parquet", "wb"),
        batch_size=1000,
    )
    assert pathlib.Path("test-data/utf8.parquet").is_file()
    df = pandas.read_parquet("test-data/utf8.parquet")
    assert len(df) == 10612
    assert len(df.columns) == 215


def test_to_parquet_iter() -> None:
    to_parquet(
        MARCReader(open("test-data/utf8.marc", "rb")),
        open("test-data/utf8.parquet", "wb"),
        batch_size=1000,
    )
    df = pandas.read_parquet("test-data/utf8.parquet")
    assert len(df) == 10612
    assert len(df.columns) == 215


def test_to_parquet_with_rules() -> None:
    to_parquet(
        MARCReader(open("test-data/utf8.marc", "rb")),
        open("test-data/utf8.parquet", "wb"),
        batch_size=1000,
        rules=["001", "245", "650v"],
    )
    assert pathlib.Path("test-data/utf8.parquet").is_file()
    df = pandas.read_parquet("test-data/utf8.parquet")
    assert len(df) == 10612
    assert len(df.columns) == 3
