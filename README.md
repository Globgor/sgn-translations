# SGN translations

Interface translations and translated user manuals for
[SGN / Breedbase](https://github.com/solgenomics/sgn), with the tools that
check them and build language packs. SGN itself keeps only code.

Languages: Ukrainian (`uk`), Spanish (`es`), Arabic (`ar`). English is in SGN.

**Status:** all translations are machine-generated drafts. They need review by
a native speaker and a breeder before a site relies on them.

## Layout

```text
po/templates/<section>.pot   English messages of one application section
po/<lang>/<section>.po       translations of the same messages
glossary/<lang>.md, .tsv     terminology (draft) and the rules the check enforces
manual/                      translated manual chapters and their build helper
tools/                       extraction, check, build and install tools
docs/                        guides for each job (below)
```

A section is a group of SGN pages, such as `seedlots` or `trial_card`. Each
message is in exactly one section file per language:

1. `common` when SGN loads it on every page (shared context prefix or shared
   source file);
2. otherwise the section that SGN's `locale/workflows.json` gives to the first
   source file (sorted path) that uses it.

All messages with one msgctxt stay together. Old (`#~`) entries stay at the end
of `common.po`. `tools/sections.py` applies this rule every time templates are
regenerated. The section files do not change the browser partitions in packs.

## Translator

Edit `po/<lang>/<section>.po` in [Poedit](https://poedit.com/) or in the GitHub
editor, then open a pull request **here**. SGN is not touched.

- Change only `msgstr`. Keep `%{name}` values, IDs, units and scientific names.
- Fill every plural form. An empty translation is allowed: SGN shows English.
- Mark uncertain text "Needs Work" (fuzzy). SGN shows English for it.

The pull request runs the checks. More: [docs/TRANSLATOR.md](docs/TRANSLATOR.md),
[docs/REVIEW.md](docs/REVIEW.md).

## Add a language

1. Start the catalog from the templates, with the language's real plural rule
   and direction:

   ```sh
   python3 tools/sgn-i18n init --release ~/sgn-translation-v1/release.json --locale fr \
     --direction ltr --plural-forms 'nplurals=2; plural=(n > 1);' --name 'Français' --output /tmp/fr.po
   python3 tools/sgn-i18n split --language fr --po /tmp/fr.po
   ```

   `release.json` comes from a prepared workspace (see Builder); `--sgn PATH`
   instead of `--release` reads an SGN checkout directly.
2. Add the language to `LANGUAGES` in `tools/check_catalogs.py`
   (plural rule, direction, scripts that must not appear).
3. Run the checks (below) and open a pull request.

## Builder

The builder needs an SGN checkout and the [source tools](docs/TOOLS.md).
Regenerate templates and update every language from an SGN commit:

```sh
python3 tools/sgn-i18n update --sgn /path/to/sgn
```

Make ready language packs for that SGN commit:

```sh
python3 tools/sgn-i18n prepare --sgn /path/to/sgn \
  --application-version "$(git -C /path/to/sgn rev-parse HEAD)" --output ~/sgn-translation-v1
cd ~/sgn-translation-v1 && python3 tools/sgn-i18n package --workspace . --output ~/sgn-ready-v1
```

Publish the ready folder for each SGN release, so that only the builder needs
Node, Perl and R. Details: [docs/TRANSLATOR.md](docs/TRANSLATOR.md).

## Site administrator

Install a ready pack: [docs/INSTALL.md](docs/INSTALL.md).
Manual: [docs/MANUAL.md](docs/MANUAL.md).

## Checks

```sh
sudo scripts/install-ci-deps.sh   # Ubuntu 24.04, once
scripts/ci.sh                     # same steps as .github/workflows/check.yml
```

`tools/check_catalogs.py` alone needs only Python 3 and GNU gettext. It checks
structure, not wording: same messages as the template, `%{name}` values, plural
forms, header, `msgfmt --check`, letters of a wrong script, glossary rules.
Tests that read SGN files run when `SGN_CHECKOUT=/path/to/sgn` is set.

## Licence

Code and translations: MIT, the same as SGN ([LICENSE](LICENSE)).
Some country names are adapted from iso-codes (LGPL-2.1-or-later):
[LICENSE.iso-codes](LICENSE.iso-codes), [docs/TRANSLATION_SOURCES.md](docs/TRANSLATION_SOURCES.md).
