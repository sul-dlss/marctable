import json
from itertools import batched
from typing import (
    BinaryIO,
    Dict,
    Generator,
    List,
    Optional,
    TextIO,
    Tuple,
    Union,
    IO,
    Any,
)

import pandas
import pyarrow
from pandas import DataFrame
from pyarrow.parquet import ParquetWriter
from pymarc import Record, Field, MARCReader

from .marc import MARC

# type alises to shorten annotations
ListOrString = Union[str, List[str]]
Records = List[Record] | MARCReader


def to_csv(
    records: Records,
    csv_output: TextIO,
    rules: list = [],
    batch_size: int = 1000,
    avram_file: Optional[BinaryIO] = None,
) -> None:
    """
    Convert MARC to CSV.
    """
    first_batch = True
    for df in dataframe_iter(
        records, rules=rules, batch_size=batch_size, avram_file=avram_file
    ):
        df.to_csv(csv_output, header=first_batch, index=False)
        first_batch = False


def to_jsonl(
    records: Records,
    jsonl_output: BinaryIO,
    rules: list = [],
    batch_size: int = 1000,
    avram_file: Optional[BinaryIO] = None,
) -> None:
    """
    Convert MARC to JSON Lines (JSONL).
    """
    for records_batch in process_records(
        records, rules=rules, batch_size=batch_size, avram_file=avram_file
    ):
        for record in records_batch:
            jsonl_output.write(json.dumps(record).encode("utf8") + b"\n")


def to_parquet(
    records: Records,
    parquet_output: IO[Any],
    rules: list = [],
    batch_size: int = 1000,
    avram_file: Optional[BinaryIO] = None,
) -> None:
    """
    Convert MARC to Parquet.
    """
    schema = _make_parquet_schema(rules, avram_file)
    writer = ParquetWriter(parquet_output, schema, compression="snappy")
    for records_batch in process_records(
        records, rules=rules, batch_size=batch_size, avram_file=avram_file
    ):
        table = pyarrow.Table.from_pylist(records_batch, schema)
        writer.write_table(table)

    writer.close()


def to_dataframe(
    records: Records,
    rules: list = [],
    batch_size=1000,
    avram_file: Optional[BinaryIO] = None,
) -> DataFrame:
    """
    A convenience function that returns a single DataFrame for all the records.
    WARNING: It will build the entire DataFrame in memory, so be careful!
    """
    return pandas.concat(
        list(dataframe_iter(records, rules, batch_size, avram_file)), axis=0
    )


def dataframe_iter(
    records: Records,
    rules: list = [],
    batch_size: int = 1000,
    avram_file: Optional[BinaryIO] = None,
) -> Generator[DataFrame, None, None]:
    """
    Read the records and generates Panda Data Frames of a given size.
    """
    columns = _columns(_mapping(rules, avram_file))
    for records_batch in process_records(
        records, rules, batch_size, avram_file=avram_file
    ):
        yield DataFrame.from_records(records_batch, columns=columns)


def process_records(
    records: Records,
    rules: list = [],
    batch_size: int = 1000,
    avram_file: Optional[BinaryIO] = None,
) -> Generator[List[Dict], None, None]:
    """
    Iterate through MARCRecords and return a generator of batches of records
    represented as a list of dictionaries, which are constructed with the given rules.
    """
    mapping = _mapping(rules, avram_file)
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
                if subfields is None:
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

                # otherwise only add the subfields that were requested in the mapping
                else:
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

            rows.append(r)

        yield rows


def _stringify_field(field: Field) -> str:
    if field.is_control_field():
        return field.data if field.data is not None else ""
    else:
        return " ".join([sf.value for sf in field.subfields])


def _mapping(rules: list, avram_file: Optional[BinaryIO] = None) -> dict:
    """
    unpack the mapping rules into a dictionary for easy lookup

    >>> _mapping(["245", "260ac"])
    {'245': None, '260': ['a', 'c']}
    """
    marc = MARC.from_avram(avram_file)
    if rules is None or len(rules) == 0:
        rules = [field.tag for field in marc.fields]

    m = {}
    for rule in rules:
        field_tag = rule[0:3]
        if marc.get_field(field_tag) is None:
            raise Exception(f"unknown MARC field in mapping rule: {rule}")

        subfields = set(list(rule[3:]))
        for subfield_code in subfields:
            if marc.get_subfield(field_tag, subfield_code) is None:
                raise Exception(f"unknown MARC subfield in mapping rule: {rule}")

        m[field_tag] = subfields or None

    return m


def _columns(mapping: dict) -> list:
    """
    unpack the mapping to get a list of columns for the table
    """
    cols = []
    for field_tag, subfields in mapping.items():
        if subfields is None:
            cols.append(f"F{field_tag}")
        else:
            for sf in subfields:
                cols.append(f"F{field_tag}{sf}")
    return cols


def _make_pandas_schema(
    rules: list, avram_file: Optional[BinaryIO] = None
) -> Dict[str, str]:
    marc = MARC.from_avram(avram_file)
    mapping = _mapping(rules, avram_file)
    schema = {}
    for field_tag, subfields in mapping.items():
        if subfields is None:
            schema[f"F{field_tag}"] = (
                "object" if marc.get_field(field_tag).repeatable else "str"
            )
        else:
            for sf in subfields:
                schema[f"F{field_tag}{sf}"] = (
                    "object" if marc.get_subfield(field_tag, sf).repeatable else "str"
                )
    return schema


def _make_parquet_schema(
    rules: list, avram_file: Optional[BinaryIO] = None
) -> pyarrow.Schema:
    marc = MARC.from_avram(avram_file)
    mapping = _mapping(rules, avram_file)

    pyarrow_str = pyarrow.string()
    pyarrow_list_of_str = pyarrow.list_(pyarrow.string())

    cols: List[Tuple[str, pyarrow.DataType]] = []
    for field_tag, subfields in mapping.items():
        if subfields is None:
            if marc.get_field(field_tag).repeatable:
                cols.append((f"F{field_tag}", pyarrow_list_of_str))
            else:
                cols.append((f"F{field_tag}", pyarrow_str))
        else:
            for sf_code in subfields:
                sf = marc.get_subfield(field_tag, sf_code)
                if sf is not None and sf.repeatable:
                    cols.append((f"F{field_tag}{sf}", pyarrow_list_of_str))
                else:
                    cols.append((f"F{field_tag}{sf}", pyarrow_str))
    return pyarrow.schema(cols)  # type: ignore[arg-type]
