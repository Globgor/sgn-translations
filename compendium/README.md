# Compendium of machine drafts

`compendium/<lang>.po` holds machine-draft translations of about 13,500
English SGN texts. It is a source of suggestions, not a catalog: `make update`
copies a translation from here into `po/<lang>.po` when SGN starts to use the
same English text. Only exact, non-fuzzy matches are copied (see the README).
`msgfmt` never builds these files into the site.

Every text here is a machine draft. A native speaker must review it before a
site relies on it.

## Fuzzy entries

An English text that had different drafts in different places is one `fuzzy`
entry. Its `msgstr` lists every draft between `#-#-#-#-#` lines. `make update`
does not copy fuzzy entries. To use one, write the chosen translation in
`po/<lang>.po`.

## How the files were made

The drafts came from `po/<lang>/<section>.po` (28 files per language) at
commit `af74ea0` of this repository. There, every message had a symbolic key
as `msgctxt` and `%{name}` placeholders. The conversion ran once, with GNU
gettext 0.23.1 and Perl in the `breedbase/breedbase` image:

```sh
msgcat --no-wrap --no-location po/$lang/*.po | msgattrib --no-wrap --no-obsolete -o $lang.all.po
perl compendium/convert.pl $lang.all.po > $lang-drafts.po
msguniq --no-wrap --sort-output $lang-drafts.po -o compendium/$lang.po
msgfmt --check -o /dev/null compendium/$lang.po
```

`convert.pl`:

- removes the `msgctxt` keys;
- changes `%{name}` to `{name}` in `msgid`, `msgid_plural` and every `msgstr`,
  and marks those entries `perl-brace-format`, so `msgfmt --check` checks the
  placeholders;
- marks the 246 country names that come from iso-codes;
- drops the review notes of the old workflow and the source references (they
  pointed to a prototype branch, not to SGN);
- resolves English texts that occur both with and without a plural form.

## Results

| | uk | es | ar |
|---|---|---|---|
| Keyed messages in | 15,398 | 15,398 | 15,398 |
| Obsolete (`#~`) entries, not taken | 123 | 123 | 123 |
| Entries out (unique English texts) | 13,565 | 13,565 | 13,565 |
| Fuzzy: different drafts of one text | 274 | 248 | 314 |
| Fuzzy already in the drafts | 1 | 1 | 1 |
| `perl-brace-format` entries | 1,608 | 1,608 | 1,608 |
| `msgfmt --check` | passes | passes | passes |

A separate check compared every keyed message with the result: 15,397 of
15,398 per language are present unchanged (apart from `{name}`), either as
the entry itself or as one of the drafts of a fuzzy entry. The one exception
is below. No placeholder differed between an English text and its draft.

One structural collision, the same in all three languages:

- `populations` existed once without a plural (key
  `barcode.helper.populations`, draft left in English: `populations`) and once
  with `msgid_plural "populations"` (key
  `phenotype.root.population_count_suffix`). A PO file cannot hold both.
  The plural entry is kept; the singular one is dropped. Its draft was the
  English text, so no translation is lost.

`msgfmt --check` warns about one text that contains `\r\n`
(`" can't be accessed without a token.\r\n..."`). This is a warning, not an
error; the text is copied as it was.
