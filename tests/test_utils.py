import pathlib

import pandas
import pyarrow
from pymarc import MARCReader
from marctable.utils import (
    dataframe_iter,
    to_csv,
    to_dataframe,
    to_parquet,
    Column,
    _mapping,
)


def test_to_dataframe() -> None:
    df = to_dataframe(MARCReader(open("test-data/utf8.marc", "rb")))
    assert len(df.columns) == 216
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
    assert df.iloc[0]["FLDR"] == "01729cmm a2200349 a 4500"


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
    df = pandas.read_csv("test-data/utf8.csv", low_memory=False)
    assert len(df) == 10612
    assert len(df.columns) == 216
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
    assert len(df.columns) == 216


def test_to_parquet_iter() -> None:
    to_parquet(
        MARCReader(open("test-data/utf8.marc", "rb")),
        open("test-data/utf8.parquet", "wb"),
        batch_size=1000,
    )
    df = pandas.read_parquet("test-data/utf8.parquet")
    assert len(df) == 10612
    assert len(df.columns) == 216


def test_to_parquet_with_columns() -> None:
    to_parquet(
        MARCReader(open("test-data/utf8.marc", "rb")),
        open("test-data/utf8.parquet", "wb"),
        batch_size=1000,
        columns=["001", "245", "650v"],
    )
    assert pathlib.Path("test-data/utf8.parquet").is_file()
    df = pandas.read_parquet("test-data/utf8.parquet")
    assert len(df) == 10612
    assert list(df.columns) == ["F001", "F245", "F650v"]


def test_mapping() -> None:
    assert _mapping(["245"], []) == {"245": ["*"]}
    assert _mapping(["245", "650"], []) == {"245": ["*"], "650": ["*"]}
    assert _mapping(["040", "040a"], []) == {"040": ["*", "a"]}
    assert _mapping(["245a", "650ax", "260"], []) == {
        "245": ["a"],
        "650": ["a", "x"],
        "260": ["*"],
    }
    assert len(_mapping([], [])) == 216, (
        "passing in no rules and no col_objects results in the default mapping being returned (all fields)"
    )
    assert _mapping([], [Column("field_count", lambda r: len(r.fields))]) == {}, (
        "passing in no rules but some col_objects results in the empty dictionary being returned"
    )


def test_field_and_subfield(tmp_path) -> None:
    """
    Ensure we can specify both the field as a whole and individual subfields.
    """
    csv_path = tmp_path / "test.csv"
    to_csv(
        MARCReader(open("test-data/utf8.marc", "rb")),
        csv_path.open("w"),
        columns=["040", "040a"],
    )
    df = pandas.read_csv(csv_path)
    assert len(df) == 10612
    assert len(df.columns) == 2


def test_custom_fields_df() -> None:
    df = to_dataframe(
        MARCReader(open("test-data/utf8.marc", "rb")), columns=["245", "650"]
    )
    assert len(df) == 10612
    # should only have two columns in the dataframe
    assert len(df.columns) == 2
    assert df.columns[0] == "F245"
    assert df.columns[1] == "F650"
    assert (
        df.iloc[0]["F245"]
        == "Leak testing CD-ROM [computer file] / technical editors, Charles N. "
        "Jackson, Jr., Charles N. Sherlock ; editor, Patrick O. Moore."
    )
    assert df.iloc[0]["F650"] == ["Leak detectors.", "Gas leakage."]


def test_custom_subfields_df() -> None:
    df = to_dataframe(
        MARCReader(open("test-data/utf8.marc", "rb")), columns=["245a", "260c"]
    )
    assert len(df) == 10612
    assert len(df.columns) == 2
    assert df.columns[0] == "F245a"
    assert df.columns[1] == "F260c"
    # 245a is not repeatable
    assert df.iloc[0]["F245a"] == "Leak testing CD-ROM"
    # 260c is repeatable
    assert df.iloc[0]["F260c"] == ["c2000."]


def test_column_func_mix() -> None:
    df = to_dataframe(
        MARCReader(open("test-data/utf8.marc", "rb")),
        columns=[
            "245a",
            "260c",
            Column("field_count", lambda r: len(r.fields)),
        ],
    )
    assert len(df) == 10612
    assert len(df.columns) == 3
    assert df.columns[0] == "F245a"
    assert df.columns[1] == "F260c"

    # 245a is not repeatable
    assert df.iloc[0]["F245a"] == "Leak testing CD-ROM"

    # 260c is repeatable
    assert df.iloc[0]["F260c"] == ["c2000."]

    # function based column was populated
    assert df.iloc[0]["field_count"] == 27


def test_indicators_df() -> None:
    df = to_dataframe(
        MARCReader(open("test-data/utf8.marc", "rb")),
        columns=["245", "650", "008"],
        indicators=True,
    )
    # control fields (008) get no indicator columns, data fields get two each
    assert list(df.columns) == [
        "F245",
        "F245_ind1",
        "F245_ind2",
        "F650",
        "F650_ind1",
        "F650_ind2",
        "F008",
    ]

    # 245 is not repeatable, so its indicators are scalars
    assert df.iloc[0]["F245_ind1"] == "0"
    assert df.iloc[0]["F245_ind2"] == "0"

    # 650 is repeatable, so its indicators are lists aligned with the values
    assert df.iloc[0]["F650"] == ["Leak detectors.", "Gas leakage."]
    assert df.iloc[0]["F650_ind1"] == [" ", " "]  # blank indicators preserved
    assert df.iloc[0]["F650_ind2"] == ["0", "0"]


def test_indicators_off_by_default() -> None:
    df = to_dataframe(
        MARCReader(open("test-data/utf8.marc", "rb")), columns=["245", "650"]
    )
    assert list(df.columns) == ["F245", "F650"]


def test_indicators_parquet(tmp_path) -> None:
    import pyarrow.parquet as pq

    parquet_path = tmp_path / "indicators.parquet"
    to_parquet(
        MARCReader(open("test-data/utf8.marc", "rb")),
        parquet_path.open("wb"),
        columns=["245", "650", "008"],
        indicators=True,
    )
    schema = pq.read_schema(parquet_path)
    # non-repeatable field indicators are strings
    assert schema.field("F245_ind1").type == pyarrow.string()
    # repeatable field indicators are lists of strings
    assert schema.field("F650_ind1").type == pyarrow.list_(pyarrow.string())
    # control fields have no indicator columns
    assert "F008_ind1" not in schema.names


def test_one_column_func() -> None:
    df = to_dataframe(
        MARCReader(open("test-data/utf8.marc", "rb")),
        columns=[
            Column("field_count", lambda r: len(r.fields)),
        ],
    )
    assert len(df) == 10612
    assert len(df.columns) == 1

    # function based column was populated
    assert df.iloc[0]["field_count"] == 27
