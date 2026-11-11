# SGN translations

Interface translations for [SGN / Breedbase](https://github.com/solgenomics/sgn)
as standard GNU gettext files, and translated user manuals. SGN keeps only code.

Languages: Ukrainian (`uk`), Spanish (`es`), Arabic (`ar`). English is in SGN.

**Status:** all translations are machine-generated drafts. No native speaker
has reviewed them yet. Review them before a site relies on them.

## Layout

```text
po/templates/<section>.pot   English messages of one SGN section (generated)
po/<lang>/<section>.po       translations of the same messages
glossary/                    terminology draft and the rules the check enforces
manual/                      translated manual chapters (built with R, optional)
tools/                       build, check and template scripts (Python 3)
build/                       made by `make`; read by SGN; not in Git
```

A section is a group of SGN pages, such as `seedlots` or `trial_card`. Every
message is in exactly one section file per language. Messages that SGN shows
on every page are in `common`.

## Site administrator

SGN reads `build/` of this repository. The default place is
`../sgn-translations/build`, next to the SGN checkout.

If your Breedbase Docker image contains this repository, the files are already
built. Add two lines to `sgn_local.conf` and restart SGN:

```text
i18n_enabled           1
i18n_enabled_locales   en,uk
```

Manual install on Debian or Ubuntu:

```sh
sudo apt-get install gettext libintl-perl make
git clone https://github.com/Globgor/sgn-translations.git   # next to the sgn folder
cd sgn-translations
make
```

Then add the two lines above and restart SGN. If the files are in another
place, also set `i18n_dir /absolute/path/to/sgn-translations/build`.
After `git pull`, run `make` again and restart SGN.

## Translator

1. Open `po/<lang>/<section>.po` in [Poedit](https://poedit.com/) or in the
   GitHub editor.
2. Change only the translation (`msgstr`). Keep `%{name}` values exactly.
3. Fill every plural form. Mark uncertain text "Needs Work" (fuzzy).
4. Open a pull request in this repository. The checks run on it.

A translation that is empty, fuzzy, has a broken `%{name}` value or misses a
plural form is left out of the build. The site shows English for it.

`make check` requires: the same messages as the template, the standard header
of the language, all plural forms, kept `%{name}` values, `msgfmt --check`, no
letters of a wrong script (for example Arabic in Ukrainian), and the glossary
rules. Details, review and a new language: [docs/TRANSLATOR.md](docs/TRANSLATOR.md).

## Developer and release

Needs GNU gettext, Python 3 and make.

```sh
make templates SGN=/path/to/sgn   # xgettext -> po/templates, msgmerge every language
git diff --stat                   # review what changed
make check                        # all checks and tool tests
make                              # build/ for SGN
git add po && git commit
```

`make templates` stops without writing if translated messages would be lost,
for example with an SGN checkout that marks fewer files. Read
[docs/EXTRACTION.md](docs/EXTRACTION.md) before the first run.
`make clean` removes `build/`. The manual: [docs/MANUAL.md](docs/MANUAL.md).

## Licence

Code and translations: MIT, the same as SGN ([LICENSE](LICENSE)).
Some country names are adapted from iso-codes (LGPL-2.1-or-later):
[LICENSE.iso-codes](LICENSE.iso-codes), [docs/TRANSLATION_SOURCES.md](docs/TRANSLATION_SOURCES.md).
