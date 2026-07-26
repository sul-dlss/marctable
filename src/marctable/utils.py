import json
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import batched
from typing import (
    IO,
    Any,
    BinaryIO,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    TextIO,
    Tuple,
    Union,
)

import pandas
import pyarrow
from pandas import DataFrame
from pyarrow.parquet import ParquetWriter
from pymarc import Field, MARCReader, Record

from .marc import MARC

# type aliases to shorten annotations
ListOrString = Union[str, List[str]]
Records = List[Record] | Iterator[Record] | MARCReader


@dataclass
class Column:
    name: str
    fn: Callable[[Record], Any]


ColumnSpec = str | Column


def _split_columns(
    columns: list[ColumnSpec],
) -> tuple[list[str], list[Column]]:
    """Split a columns list into MARC string rules and Column objects."""
    str_rules = [c for c in columns if isinstance(c, str)]
    col_objects = [c for c in columns if isinstance(c, Column)]
    return str_rules, col_objects


def to_csv(
    records: Records,
    csv_output: TextIO,
    columns: list[ColumnSpec] = [],
    batch_size: int = 1000,
    avram_file: Optional[BinaryIO] = None,
    indicators: bool = False,
) -> None:
    """
    Convert MARC to CSV.
    """
    first_batch = True
    for df in dataframe_iter(
        records,
        columns=columns,
        batch_size=batch_size,
        avram_file=avram_file,
        indicators=indicators,
    ):
        df.to_csv(csv_output, header=first_batch, index=False)
        first_batch = False


def to_jsonl(
    records: Records,
    jsonl_output: BinaryIO,
    columns: list[ColumnSpec] = [],
    batch_size: int = 1000,
    avram_file: Optional[BinaryIO] = None,
    indicators: bool = False,
) -> None:
    """
    Convert MARC to JSON Lines (JSONL).
    """
    for records_batch in process_records(
        records,
        columns=columns,
        batch_size=batch_size,
        avram_file=avram_file,
        indicators=indicators,
    ):
        for record in records_batch:
            jsonl_output.write(json.dumps(record).encode("utf8") + b"\n")


def to_parquet(
    records: Records,
    parquet_output: IO[Any],
    columns: list[ColumnSpec] = [],
    batch_size: int = 1000,
    avram_file: Optional[BinaryIO] = None,
    indicators: bool = False,
) -> None:
    """
    Convert MARC to Parquet.
    """
    schema = _make_parquet_schema(columns, avram_file, indicators=indicators)
    writer = ParquetWriter(parquet_output, schema, compression="snappy")
    for records_batch in process_records(
        records,
        columns=columns,
        batch_size=batch_size,
        avram_file=avram_file,
        indicators=indicators,
    ):
        table = pyarrow.Table.from_pylist(records_batch, schema)
        writer.write_table(table)

    writer.close()


def to_dataframe(
    records: Records,
    columns: list[ColumnSpec] = [],
    batch_size: int = 1000,
    avram_file: Optional[BinaryIO] = None,
    indicators: bool = False,
) -> DataFrame:
    """
    A convenience function that returns a single DataFrame for all the records.
    WARNING: It will build the entire DataFrame in memory, so be careful!
    """
    return pandas.concat(
        list(
            dataframe_iter(
                records, columns, batch_size, avram_file, indicators=indicators
            )
        ),
        axis=0,
    )


def dataframe_iter(
    records: Records,
    columns: list[ColumnSpec] = [],
    batch_size: int = 1000,
    avram_file: Optional[BinaryIO] = None,
    indicators: bool = False,
) -> Generator[DataFrame, None, None]:
    """
    Read the records and generates Panda Data Frames of a given size.
    """
    col_names = _columns(columns, avram_file, indicators=indicators)
    for records_batch in process_records(
        records, columns, batch_size, avram_file=avram_file, indicators=indicators
    ):
        yield DataFrame.from_records(records_batch, columns=col_names)


def process_records(
    records: Records,
    columns: list[ColumnSpec] = [],
    batch_size: int = 1000,
    avram_file: Optional[BinaryIO] = None,
    indicators: bool = False,
) -> Generator[List[Dict], None, None]:
    """
    Iterate through MARCRecords and return a generator of batches of records
    represented as a list of dictionaries, which are constructed with the given columns.
    """
    str_rules, col_objects = _split_columns(columns)
    mapping = _mapping(str_rules, col_objects, avram_file)
    marc = MARC.from_avram(avram_file)

    for batch in batched(records, batch_size):
        rows = []
        for record in batch:
            # if pymarc can't make sense of a record it returns None
            if record is None:
                # TODO: log this?
                continue

            r: Dict[str, ListOrString] = {}

            if "LDR" in mapping:
                r["FLDR"] = str(record.leader)

            for field in record.fields:
                if field.tag not in mapping:
                    continue

                subfields = mapping[field.tag]

                # if subfields aren't specified stringify them
                if "*" in subfields:
                    key = f"F{field.tag}"
                    if marc.get_field(field.tag).repeatable:
                        lst = r.get(key, [])
                        assert isinstance(lst, list), (
                            "Repeatable field contains a string instead of a list"
                        )
                        lst.append(_stringify_field(field))
                        r[key] = lst
                    else:
                        s = _stringify_field(field)
                        r[key] = s

                # look for requested subfields
                for sf in field.subfields:
                    if sf.code not in subfields:
                        continue

                    key = f"F{field.tag}{sf.code}"
                    if marc.get_subfield(field.tag, sf.code).repeatable:
                        value: ListOrString = r.get(key, [])
                        assert isinstance(value, list), (
                            "Repeatable field contains a string instead of list"
                        )
                        value.append(sf.value)
                    else:
                        value = sf.value

                    r[key] = value

                # optionally capture the field's indicators, aligned by
                # occurrence order with the field's other values
                if indicators and not field.is_control_field():
                    repeatable = marc.get_field(field.tag).repeatable
                    for n, ind in ((1, field.indicator1), (2, field.indicator2)):
                        key = f"F{field.tag}_ind{n}"
                        if repeatable:
                            lst = r.get(key, [])
                            assert isinstance(lst, list), (
                                "Repeatable field contains a string instead of a list"
                            )
                            lst.append(ind)
                            r[key] = lst
                        else:
                            r[key] = ind

            # now add any function based columns
            for col in col_objects:
                r[col.name] = col.fn(record)

            rows.append(r)

        yield rows


def _stringify_field(field: Field) -> str:
    if field.is_control_field():
        return field.data if field.data is not None else ""
    else:
        return " ".join([sf.value for sf in field.subfields])


def _mapping(
    rules: list, col_objects: list, avram_file: Optional[BinaryIO] = None
) -> dict:
    """
    Unpack the mapping rules into a dictionary for easy lookup. "*" signifies
    that the concatenated subfields are desired.

    >>> _mapping(["245", "260ac"], [])
    {'245': ['*'], '260': ['a', 'c']}

    The full field can be extracted alongside its subfields by using "*" too:

    >>> _mapping(["260", "260ac"], [])
    {'260': ['*', 'a', 'c']}

    The col_objects need to be passed in because when they are in use we don't
    want to return the default mapping for all MARC fields.
    """
    marc = MARC.from_avram(avram_file)

    # if there are no rules AND col_objects is not being used, default to all MARC fields
    if (rules is None or len(rules) == 0) and len(col_objects) == 0:
        rules = [field.tag for field in marc.fields]

    m: dict[str, list[str]] = {}
    for rule in rules:
        field_tag = rule[0:3]
        if marc.get_field(field_tag) is None:
            raise Exception(f"unknown MARC field in mapping rule: {rule}")

        subfields = []

        # if they just want the whole field
        if field_tag == rule:
            subfields.append("*")

        # otherwise they want specific subfields
        else:
            for subfield_code in set(list(rule[3:])):
                if marc.get_subfield(field_tag, subfield_code) is None:
                    raise Exception(
                        f"unknown MARC field/subfield in mapping rule: {rule}"
                    )
                subfields.append(subfield_code)

        # it helps when testing that the values appear in order
        subfields = list(sorted(subfields))

        # look to see if we need to add the rule to an existing one
        # this is important so that ["245", "245a"] works properly.
        if field_tag in m:
            m[field_tag].extend(subfields)
        else:
            m[field_tag] = subfields

    return m


def _columns(
    columns: list[ColumnSpec],
    avram_file: Optional[BinaryIO] = None,
    indicators: bool = False,
) -> list[str]:
    """
    Unpack the columns to get a list of column names for the table.
    """
    marc = MARC.from_avram(avram_file)
    str_rules, col_objects = _split_columns(columns)
    mapping = _mapping(str_rules, col_objects, avram_file)

    cols: list[str] = []
    for field_tag, subfields in mapping.items():
        for sf in subfields:
            if sf == "*":
                cols.append(f"F{field_tag}")
            else:
                cols.append(f"F{field_tag}{sf}")
        if indicators and _has_indicators(marc, field_tag):
            cols.append(f"F{field_tag}_ind1")
            cols.append(f"F{field_tag}_ind2")

    for col in col_objects:
        cols.append(col.name)

    return cols


def _make_parquet_schema(
    columns: list[ColumnSpec],
    avram_file: Optional[BinaryIO] = None,
    indicators: bool = False,
) -> pyarrow.Schema:
    marc = MARC.from_avram(avram_file)
    str_rules, col_objects = _split_columns(columns)
    mapping = _mapping(str_rules, col_objects, avram_file)

    pyarrow_str = pyarrow.string()
    pyarrow_list_of_str = pyarrow.list_(pyarrow.string())

    # construct a pyarrow column schema based on the mapping
    cols: List[Tuple[str, pyarrow.DataType]] = []
    for field_tag, subfields in mapping.items():
        for sf_code in subfields:
            if sf_code == "*":
                if marc.get_field(field_tag).repeatable:
                    cols.append((f"F{field_tag}", pyarrow_list_of_str))
                else:
                    cols.append((f"F{field_tag}", pyarrow_str))
            else:
                sf = marc.get_subfield(field_tag, sf_code)
                if sf is not None and sf.repeatable:
                    cols.append((f"F{field_tag}{sf.code}", pyarrow_list_of_str))
                else:
                    cols.append((f"F{field_tag}{sf.code}", pyarrow_str))

        # indicators mirror the field's repeatability, one column per indicator
        if indicators and _has_indicators(marc, field_tag):
            ind_type = (
                pyarrow_list_of_str
                if marc.get_field(field_tag).repeatable
                else pyarrow_str
            )
            cols.append((f"F{field_tag}_ind1", ind_type))
            cols.append((f"F{field_tag}_ind2", ind_type))

    for col in col_objects:
        cols.append((col.name, pyarrow_str))

    return pyarrow.schema(cols)  # type: ignore[arg-type]


def _has_indicators(marc: MARC, field_tag: str) -> bool:
    """
    Only data fields carry indicators; control fields (00X) and the leader
    (LDR) have no subfields in the Avram schema, so they get no indicator
    columns.
    """
    field = marc.get_field(field_tag)
    return len(field.subfields) > 0
