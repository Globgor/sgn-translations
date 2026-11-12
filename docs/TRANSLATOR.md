# Translate and review

The translations are standard gettext PO files: `po/<lang>/<section>.po`.
All of them are machine-generated drafts. A native speaker and a breeder must
review the text before a site relies on it.

## Edit a section file

Use [Poedit](https://poedit.com/) on your computer, or the GitHub editor.
SGN and the tools in this repository are not needed for editing.

1. Open `po/<lang>/<section>.po`. Messages shown on every page are in `common.po`.
2. Select a message. The English text is the source; the translation is `msgstr`.
3. Change the translation only. Keep the context key, the English text and the header.
4. Keep `%{name}` values exactly, for example `%{count}` and `%{name}`.
   SGN puts the real value there.
5. Fill every plural form of the language. Ukrainian has 3, Arabic has 6.
6. Mark uncertain text "Needs Work" (fuzzy). The site shows English for it.
7. Save and open a pull request in this repository.

Example: in `Created trial %{name}.` translate the words and keep `%{name}`.
Keep IDs, scientific names, units and file field names unchanged. Write plain
text, not HTML tags or entities such as `&amp;`. In
`file_list.datatable.length_menu` and `odk.table.length`, `%{menu}` must occur
exactly once.

To search all sections of one language at once, join them into a read-only copy
with GNU gettext: `msgcat po/uk/*.po -o /tmp/uk-all.po`. Make the edits in the
section files, not in the copy.

## What the checks require

`make check` runs on every pull request. For each `po/<lang>/<section>.po`:

- the same messages as `po/templates/<section>.pot`: nothing missing, nothing extra;
- the standard header: `Language`, `Plural-Forms` of the language,
  `X-SGN-Direction` (`ltr` or `rtl`), equal in all section files;
- all plural forms of every plural message;
- every filled, non-fuzzy translation keeps the `%{name}` values of its English text;
- `msgfmt --check` accepts the file, and the joined language;
- no letters of a wrong script, for example Arabic letters in Ukrainian;
- no term that `glossary/<lang>.tsv` forbids (only confirmed terms are
  there; a rule can apply to some English texts only; `glossary/uk.md` is
  the draft for the rest).

An empty translation is allowed. The site shows English for it.

## Review

1. Pick one section file, for example `po/uk/seedlots.po`.
2. Read each message next to its SGN page, including error and success messages.
3. Agree on the words for accession, trial, plot, seedlot, cross and trait.
4. Check long text, small screens, Arabic layout and the counts 0, 1, 2, 5 and 21.
5. Correct the text in Poedit. Mark doubtful entries "Needs Work".
6. Open a pull request. Name the reviewer and the section in its description.

## Add a language

The example adds German (`de`). Use the real plural rule and text direction of
the language; do not guess them.

1. Make the section files from the templates with GNU gettext:

   ```sh
   mkdir po/de
   for template in po/templates/*.pot; do
     msginit --no-translator --no-wrap --locale=de --input="$template" \
       --output="po/de/$(basename "$template" .pot).po"
   done
   ```

   `msginit` writes `Language` and the standard `Plural-Forms` of the language.

2. Add the native name and the direction to the header of every file:

   ```sh
   sed -i 's/^"Plural-Forms: .*\\n"$/&\n"X-SGN-Language-Name: Deutsch\\n"\n"X-SGN-Direction: ltr\\n"/' po/de/*.po
   ```

3. Add the language to `LANGUAGES` in `tools/check_catalogs.py`: the
   `Plural-Forms` value that `msginit` wrote, the direction, and the scripts
   that must not appear.
4. Run `make check` and `make`, then open a pull request.

A site turns the language on with `i18n_enabled_locales en,de`.
