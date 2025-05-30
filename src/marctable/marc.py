"""
This module contains classes to make it easier to work with MARC as an Avram
schema, which is loaded from the marc.json that is alongside this file. The
Avram schema lets marctable know which MARC fields and subfields are allowed,
and whether they should be encoded as lists rather than single values. It also
includes functions used for regenerating the Avram schema by crawling the MARC
specification the Library of Congress website.

For more about Avram see https://format.gbv.de/schema/avram/specification
"""

import json
import pathlib
import re
import sys
import time
from functools import cache
from typing import IO, Generator, List, Optional, Type
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag


class Subfield:
    def __init__(self, code: str, label: str, repeatable: bool = False) -> None:
        self.code = code
        self.label = label
        self.repeatable = repeatable

    @classmethod
    def from_dict(cls: Type["Subfield"], d: dict) -> "Subfield":
        return Subfield(d["code"], d["label"], d["repeatable"])

    def to_dict(self) -> dict:
        return {"code": self.code, "label": self.label, "repeatable": self.repeatable}


class Field:
    def __init__(
        self,
        tag: str,
        label: str,
        subfields: list[Subfield],
        repeatable: bool = False,
        url: Optional[str] = None,
    ) -> None:
        self.tag = tag
        self.label = label
        self.subfields = subfields
        self.repeatable = repeatable
        self.url = url

    def __str__(self) -> str:
        if len(self.subfields) > 0:
            subfields = ": " + (",".join([sf.code for sf in self.subfields]))
        else:
            subfields = ""
        return (
            f"{self.tag} {self.label}: {'R' if self.repeatable else 'NR'} {subfields}"
        )

    @classmethod
    def from_dict(cls: Type["Field"], d: dict) -> "Field":
        return Field(
            tag=d["tag"],
            label=d["label"],
            repeatable=d["repeatable"],
            url=d.get("url"),
            subfields=[Subfield.from_dict(d) for d in d.get("subfields", {}).values()],
        )

    def to_dict(self) -> dict:
        d = {
            "tag": self.tag,
            "label": self.label,
            "repeatable": self.repeatable,
            "url": self.url,
        }

        if self.subfields is not None:
            d["subfields"] = {sf.code: sf.to_dict() for sf in self.subfields}

        return d

    def get_subfield(self, code: str) -> Subfield:
        for sf in self.subfields:
            if sf.code == code:
                return sf
        raise SchemaSubfieldError(f"{code} is not a valid subfield in field {self.tag}")


class MARC:
    def __init__(self) -> None:
        self.fields: List[Field] = []

    @cache
    def get_field(self, tag: str) -> Field:
        for field in self.fields:
            if field.tag == tag:
                return field
        raise SchemaFieldError(f"{tag} is not a defined field tag in Avram schema")

    @cache
    def get_subfield(self, tag: str, code: str) -> Subfield:
        field = self.get_field(tag)
        return field.get_subfield(code)

    @property
    def avram_file(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent / "marc.json"

    @classmethod
    @cache
    def from_avram(cls: Type["MARC"], avram_file: Optional[IO] = None) -> "MARC":
        marc = MARC()

        if avram_file is None:
            avram_file = marc.avram_file.open("r")

        for d in json.load(avram_file)["fields"].values():
            marc.fields.append(Field.from_dict(d))

        return marc

    def to_avram(self, avram_file: Optional[IO] = None) -> None:
        if avram_file is None:
            avram_file = self.avram_file.open("w")

        d = {
            "title": "MARC21 bibliographic format",
            "url": "https://www.loc.gov/marc/bibliographic/",
            "family": "marc",
            "language": "en",
            "fields": {f.tag: f.to_dict() for f in self.fields},
        }
        json.dump(d, avram_file, indent=2)


class SchemaFieldError(Exception):
    pass


class SchemaSubfieldError(Exception):
    pass


def fields() -> Generator[Field, None, None]:
    toc_url = "https://www.loc.gov/marc/bibliographic/"
    toc_doc = _soup(toc_url)
    for group_link in toc_doc.select(".contentslist a"):
        if re.match(r"^\d+", group_link.text):
            group_url = urljoin(toc_url, group_link.attrs["href"])
            group_doc = _soup(group_url)
            for field_link in group_doc.select("a"):
                if field_link.text == "Full":
                    field_url = urljoin(group_url, field_link.attrs["href"])
                    if field := make_field(field_url):
                        yield field


def make_field(url: str) -> Optional[Field]:
    soup = _soup(url)
    h1: Optional[Tag] = soup.select_one("h1")
    if h1 is None:
        raise Exception("Expecting h1 element in {url}")

    h1_text: str = h1.text.strip()
    if m1 := re.match(r"^(\d+) - (.+) \((.+)\)$", h1_text):
        tag, label, repeatable = m1.groups()

        # most pages put the subfield info in a list
        subfields = []
        for el in soup.select("table.subfields li"):
            if m2 := re.match(r"^\$(.) - (.+) \((.+)\)$", el.text):
                subfields.append(Subfield(m2.group(1), m2.group(2), m2.group(3) == "R"))

        # some pages use a different layout, of course
        if len(subfields) == 0:
            for el in soup.select('td[colspan="1"]'):
                for text in el.text.split("$"):
                    text = text.strip()
                    if m2 := re.match(r"^(.) - (.+) \((.+)\)$", text):
                        subfields.append(
                            Subfield(
                                code=m2.group(1),
                                label=m2.group(2),
                                repeatable=m2.group(3) == "R",
                            )
                        )

        return Field(
            tag=tag,
            label=label.strip(),
            repeatable=repeatable == "R",
            url=url,
            subfields=subfields,
        )

    return None


# scrape the loc website for the marc fields
def crawl(n: int = 0, quiet: bool = False, outfile: IO = sys.stdout) -> None:
    marc = MARC()

    # add the leader field manually
    marc.fields.append(
        Field(
            tag="LDR",
            label="Leader",
            subfields=[],
            repeatable=False,
            url="https://www.loc.gov/marc/bibliographic/bdleader.html",
        )
    )

    # discover all the other fields!
    for f in fields():
        marc.fields.append(f)
        if not quiet:
            print(f)
        if n != 0 and len(marc.fields) >= n:
            break
    marc.to_avram(outfile)


# www.loc.gov seems to like reusing the session
http = requests.Session()


def _soup(url: str) -> BeautifulSoup:
    time.sleep(0.5)  # sleeping seems to help too...
    return BeautifulSoup(http.get(url).text, "html.parser")
