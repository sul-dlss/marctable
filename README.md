# marctable

[![Build Status](https://github.com/edsu/marctable/actions/workflows/test.yml/badge.svg)](https://github.com/edsu/marctable/actions/workflows/test.yml)

*marctable* is a Python command line utility that converts MARC bibliographic data (in transmission format or MARCXML) into tabular formats like [CSV] and [Parquet]. It uses the Library of Congress [MARC Bibliographic documentation] expressed as an [Avram] [JSON file] to determine what MARC fields and subfields to include and whether they can repeat or not.

## Install

```
$ pip install marctable
```

or just run it:

```
$ pipx run marctable
```

## Usage

*marctable* provides a subcommand style interface for exporting MARC data.

### CSV

CSV is a commonly used data format. It doesn't represent lists of values with columns very well though. To convert all the MARC fields to CSV:

```
$ marctable csv data.marc data.csv
```

For example, this will generate a CSV with 215 columns, one column for each MARC field. Fields that can repeat will appear as a list:

```csv
FLDR,F001,F003,F005,F006,F007,F008,F010,F013,F015,F016,F017,F018,F020,F022,F023,F024,F025,F026,F027,F028,F030,F031,F032,F033,F034,F035,F036,F037,F038,F040,F041,F042,F043,F044,F045,F046,F047,F048,F050,F051,F052,F055,F060,F061,F066,F070,F071,F072,F074,F080,F082,F083,F084,F085,F086,F088,F100,F110,F111,F130,F210,F222,F240,F242,F243,F245,F246,F247,F250,F251,F254,F255,F256,F257,F258,F260,F263,F264,F270,F300,F306,F307,F310,F321,F334,F335,F336,F337,F338,F340,F341,F342,F343,F344,F345,F346,F347,F348,F351,F352,F353,F355,F357,F361,F362,F363,F365,F366,F370,F377,F380,F381,F382,F383,F384,F385,F386,F387,F388,F490,F500,F501,F502,F504,F505,F506,F507,F508,F510,F511,F513,F514,F515,F516,F518,F520,F521,F522,F524,F525,F526,F530,F532,F533,F534,F535,F536,F538,F540,F541,F542,F544,F545,F546,F547,F550,F552,F555,F556,F561,F562,F563,F565,F567,F580,F581,F583,F584,F585,F586,F588,F600,F610,F611,F630,F647,F648,F650,F651,F653,F654,F655,F656,F657,F658,F662,F688,F700,F710,F711,F720,F730,F740,F751,F752,F753,F754,F758,F788,F800,F810,F811,F830,F850,F852,F856,F857,F880,F881,F882,F883,F884,F885,F886,F887
01729cmm a2200349 a 4500,   00021631 ,DLC,20030624102241.0,,['co |||||||||||'],000110s2000    ohu    f   m        eng  ,   00021631 ,,,,,,['1571170383'],,,,,,,,,,,,,,,,,DLC DLC,,,,,,,,,['TA165'],,,,,,,,,,,,['620.1 13'],,,,,,,,,,,,,,,"Leak testing CD-ROM [computer file] / technical editors, Charles N. Jackson, Jr., Charles N. Sherlock ; editor, Patrick O. Moore.",,,,,,,Computer data and program.,,,"['Columbus, Ohio : American Society for Nondestructive Testing, c2000.']",,,,['1 computer optical disc ; 4 3/4 in.'],,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,['Nondestructive testing handbook. Third edition ; v. 1'],['Title from disc label.'],,,,,,,,,,,,,,,['Theory and application of nondestructive tests for characterization and inspection of industrial materials and components.'],"['Quality control engineers, inspectors.']",,,,,,,,,,,"['System requirements for Windows: i486 or Pentium processor-based PC; 8MB RAM on Windows 95 or 98 (16MB recommended); 16MB RAM on Windows NT (24MB recommended); Microsoft Windows 95, 98, or NT 4.0 with Service Pack 3 or later; CD-ROM drive.', 'System requirements for Macintosh: Apple Power Macintosh ; 4.5MB RAM available to Acrobat Reader (6.5 recommended); Apple System Software 7.1.2 or later; 8MB available hard disk space; CD-ROM drive.']",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,"['Leak detectors.', 'Gas leakage.']",,,,,,,,,,"['Jackson, Charles N.', 'Sherlock, Charles N.', 'Moore, Patrick O.']",['American Society for Nondestructive Testing.'],,,,,,,,,,,,,,['Nondestructive testing handbook (3rd ed. : Electronic resource) ; v. 1.'],,,,,,,,,,,,
01896cmm a2200349 a 4500,   00022451 ,DLC,20140626073245.0,,['co||||'],000114s2000    miu    f   m        eng  ,   00022451 ,,,,,,['0472002759'],,,,,,,,,,,,,,,,,DLC DLC DLC,,,,,,,,,['PR2015'],,,,,,,,,,,,['821 13'],,,,,,"Langland, William, 1330?-1400?",,,,,,,,,"The Piers Plowman electronic archive. Vol. 1, Corpus Christi College, Oxford MS 201 (F) [computer file] / William Langland ; edited by Robert Adams ... [et al.] ; associate editors, M. Gail Duggan and Catherine A Farley.",,,,,,,Computer data and program.,,,"['Ann Arbor : University of Michigan Press, c2000.']",,,,['1 computer optical disc ; 4 3/4 in.'],,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,['Title from disc label.'],,,,,,,,,,,,,,,['Early scribal version of the alpha family of B text of Piers Plowman. Includes sixteen passus and contains about 170 lines not shared with the majority of other B manuscripts. Features SGML and HTML versions of text and images.'],['Middle English scholars.'],,,,,,,,,,,"['System requirements for Windows: 80486 PC; 8MB RAM; Windows 3.1 (Windows 95/98/NT for SGML version); Microsoft Internet Explorer 3.0 or Netscape 3.0; CD-ROM drive.', 'System requirements for HTML version for the Macintosh: Macintosh capable of Internet access; Netscape 3.0 or Internet Explorer 3.0; CD-ROM drive.']",,,,,,,,,,,,,,,,,,,,,,,,"['Langland, William, 1330?-1400? Piers Plowman Criticism, Textual.', 'Langland, William, 1330?-1400? Manuscripts.']",,,,,,"['Christian pilgrims and pilgrimages Poetry.', 'Manuscripts, English (Middle)']",,,,,,,,,,"['Adams, Robert, 1946-']",,,,,,,,,,,,,,,,,,['Publisher description http://www.loc.gov/catdir/enhancements/fy1405/00022451-d.html'],,,,,,,,,
01512cmm a22003138a 4500,   00022452 ,DLC,20040524123949.0,,['co||||'],000119s2000    vau        m f      eng  ,   00022452 ,,,,,,,,,,,,,,,,,,,,,,,DLC DLC,,,,,,,,,['TN153'],,,,,,,,,,,,['553 13'],,,,,,,,,,,,,,,"U.S. Geological Survey mineral databases, MRDS and MAS/MILS [computer file] / [E.J. McFaul ... et al.].",,,,,,,Computer data and program.,,,"['[Reston, Va.] : U.S. Geological Survey, 2000.']",0001,,,['2 computer optical discs ; 4 3/4 in.'],,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,['Title from disc label.'],,,,['disc 1. Minerals information for North America -- disc 2. Minerals information for the world exclusive of North America.'],,,,,,,,,,,"['Contains Mineral Resource Data System (MRDS) and Minerals Availability System/Minerals Industry Location System (MAS/MILS) databases. MRDS database features almost 200 data fields describing metallic and nonmetallic mineral resource, deposits, and commodities. MAS/MILS database includes almost 100 data fields describing mines and mineral processing plants.']",['Geologists.'],,,,,,,,,,,"['System requirements: Pentium I or better; Windows 95, 98, or NT; hard drive; CD-ROM drive.']",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,"['Mines and mineral resources Databases.', 'Mines and mineral resources Directories.']",,,,,,,,,,"['McFaul, E. J.']",['Geological Survey (U.S.)'],,,,,,,,,,,,,,,,,,,,,,,,,,
01278cmm a2200313 a 4500,   00022453 ,DLC,20020304100307.0,,['cj||||'],000119s2000    mau    f   b        eng  ,   00022453 ,,,,,,,,,,,,,,,,,,,,,,,DLC DLC DLC,,,,,,,,,['TK7871.6'],,,,,,,,,,,,['621.382 13'],,,,,,"Kolundžija, Branko M.",,,,,,,,,"WIPL-D [computer file] : electromagnetic modeling of composite metallic and dielectric structures / Branko Kolundzija, Jovan S. Ognjanovic, and Tapan K. Sarkar.",,,,,,,Computer program.,,,"['Boston : Artech House, c2000.']",,,,"[""2 computer disks ; 3 1/2 in. + 1 user's manual.""]",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,['Title from disk label.'],,,,,,,,,,,,,,,"['Provides analysis of metallic and/or dielectric/magnetic structures such as antennas, scatterers, and passive microwave circuits.']",['Engineers.'],,,,,,,,,,,['System requirements: IBM-compatible PC (Pentium preferred); 16MB RAM; Windows 95 or NT; 6MB hard disk space; mouse.'],,,,,,,,,,,,,,,,,,,,,,,,,,,,,,"['Antennas (Electronics) Software.', 'Microwave circuits Software.', 'Electromagnetic waves Software.']",,,,,,,,,,"['Ognjanovic, Jovan S.', 'Sarkar, Tapan (Tapan K.)']",,,,,,,,,,,,,,,,,,,,,,,,,,,
```

If you only want specific field and subfields you can pass in one or more rules. This will extract the `245` subfield `a`, the 650 subfields `a` and `v`, and the entirety of the  `500` fields, all as separate columns:

```
$ marctable csv --rule 245a --rule 650av --rule 500 data.marc data.csv 
```

```csv
F245a,F650a,F650v,F500
Leak testing CD-ROM,Gas leakage.,,['Title from disc label.']
The Piers Plowman electronic archive.,"Manuscripts, English (Middle)",['Poetry.'],['Title from disc label.']
"U.S. Geological Survey mineral databases, MRDS and MAS/MILS",Mines and mineral resources,"['Databases.', 'Directories.']",['Title from disc label.']
WIPL-D,Electromagnetic waves,"['Software.', 'Software.', 'Software.']",['Title from disk label.']
Theodore psalter,"Illumination of books and manuscripts, Byzantine","['Illustrations.', 'Facsimiles.']","['Title from jewel case.', 'Produced from the original text held in the British Library Rare Books collection.']"
NEPA casebook,Environmental law,['Cases.'],['Title from disc label.']
Records and history of the United States Geological Survey,Geological surveys,,['Title from disc label.']
Nursing procedures,Nursing.,,['Title from disc label.']
Nursing pharmacology made incredibly easy!,Nursing.,,['Title from disc label.']
```

### Parquet

You can also write the data as a [Parquet] file, which has advantages in that it can represent lists of elements in columns for repeatable fields and subfields, and it works in data analysis environments.

```
$ marctable parquet data.marc data.parquet
```

or with rules:

```
$ marctable parquet --rules 245a --rule 650a data.marc data.parquet
```

### JSONL

And you can write the table as JSON Lines (JSONL), where each line is a distinct JSON object.

```
$ marctable jsonl data.marc data.jsonl
```

## Regenerate Avram Schema

You can regenerate the [Avram] [JSON file] from the Library of Congress website:

```
$ marctable avram
```

## Library

You can use marctable in your own programs. You need to pass various functions either a list of `pymarc.Record` objects or a generator of `pymarc.Record` objects:

```python
from pymarc import MARCReader
from marctable import to_parquet

# MARCReader will generate Record objects
records = MARCReader(open("records.dat", "rb"))

# convert the records to a Parquet file
to_parquet(records, open("records.parquet", "wb"))
```

There are similar `to_csv()`, `to_jsonl()` and `to_dataframe()` functions as well. Be careful with `to_dataframe()` because unlike the other functions it will load all the records into memory.

## Develop

To help develop *marctable* you will want to:

```
$ git clone https://github.com/sul-dlss-labs/marctable`
$ cd marctable
$ pip3 install uv
$ uv run pytest
```

And then to build and publish a new version:

```
$ uv build
$ uv publish
```

[MARC Bibliographic documentation]: https://www.loc.gov/marc/bibliographic/
[Avram]: https://format.gbv.de/schema/avram/specification
[JSON file]: https://github.com/edsu/marctable/blob/main/marctable/marc.json
[Parquet]: https://en.wikipedia.org/wiki/Apache_Parquet
[CSV]: https://en.wikipedia.org/wiki/Comma-separated_values
