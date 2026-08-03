# Morning Scripture source

Every morning story uses one verse from a curated set of single verses from the
Berean Standard Bible. The edition-writing session selects only a catalog
identifier and writes a required, reader-directed connection. It cannot supply,
rewrite, combine, simplify, or paraphrase verse text. A connection guides the
reader's response and may not claim divine approval, condemnation, judgment, or
fulfilled prophecy for the people or event reported.

`bsb-verses.json` is generated from the official Berean Standard Bible text at
<https://bereanbible.com/bsb.txt>. The source file downloaded on 2026-08-03 was
verified with SHA-256
`2ac3af1de52d4e68261cba91d85c320b7eadc6560e830d99e591767b8ff5ca96`.
The BSB text is dedicated to the public domain; the official licensing notice
is at <https://berean.bible/licensing.htm>.

To rebuild after intentionally reviewing a new official source version, update
the pinned digest and verification date in `build_bsb_catalog.py`, then run:

```sh
python3 scripture/build_bsb_catalog.py \
  --source /path/to/verified/bsb.txt \
  --output scripture/bsb-verses.json
```

The catalog excludes verses containing em dashes so exact Scripture text and
DDB's reader-visible punctuation rule can both remain intact.
