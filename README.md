# SGN translations

Translations of the [SGN / Breedbase](https://github.com/solgenomics/sgn) web
interface as standard GNU gettext files, and translated user manuals.
Languages: Ukrainian (`uk`), Spanish (`es`), Arabic (`ar`). The English text
in SGN is the source.

**Status:** all translations are machine drafts. No native speaker has
reviewed them yet. Review them before a site relies on them.

## Layout

```text
po/sgn.pot             English texts that SGN marks for translation (made by make pot)
po/<lang>.po           translations of these texts (text domain "sgn")
po/EXCLUDE             SGN templates that make pot skips, each with the reason
compendium/<lang>.po   machine drafts of about 13,500 texts; source for make update
locale/                made by make; SGN reads it; not in Git
glossary/uk.md         Ukrainian terminology
manual/                translated user manual (docs/MANUAL.md)
tools/mason2perl.pl    Mason templates to Perl, so that xgettext can read them
tests/                 make test
```

`po/<lang>.po` holds only texts that SGN uses. It grows when SGN marks more
texts with `__()`. The drafts wait in `compendium/` until then
([compendium/README.md](compendium/README.md)).

## Translator

1. Open `po/<lang>.po` in [Poedit](https://poedit.com/), Weblate or the
   GitHub editor.
2. Change only the translation (`msgstr`). Keep `{name}` values exactly.
   Fill every plural form.
3. A translation marked fuzzy ("Needs work") does not appear on the site.
   Remove the mark when the translation is right.
4. Run `make check`, or open a pull request: the check runs on it.

Ukrainian terms: [glossary/uk.md](glossary/uk.md). For example, Upload is
«завантажити» and Download is «вивантажити».

## Site administrator

Needs GNU gettext and make. SGN needs `libintl-perl` and the system locale of
each language (the Breedbase image has all locales).

1. Put this repository next to the SGN checkout, as `sgn-translations`.
2. Run `make`. It writes `locale/<lang>/LC_MESSAGES/sgn.mo`, readable by
   all users (SGN runs as `www-data`).
3. In `sgn_local.conf`, enable the languages:

   ```text
   i18n_languages   uk,es
   ```

   For another place of `locale/`, also set
   `i18n_locale_dir /path/to/sgn-translations/locale`.
4. Restart SGN.

After `git pull`, run `make` and restart SGN again: SGN reads the catalogs only
when it starts. `make` replaces a catalog by rename, so a running SGN is safe.
To turn translation off, remove `i18n_languages` and restart.

On Debian or Ubuntu: `sudo apt-get install gettext make libintl-perl`.

## Developer

Needs GNU gettext, make, and Perl with HTML::Mason and Locale::TextDomain.
On Debian or Ubuntu:

```sh
sudo apt-get install gettext make libhtml-mason-perl libintl-perl
```

After SGN gets new or changed texts:

```sh
make pot update SGN=/path/to/sgn   # po/sgn.pot from SGN, then every po/<lang>.po
git diff                           # review what changed
make check test                    # catalogs and tool tests
```

- `make pot` reads `__()`, `__x()`, `__n()`, `__nx()`, `__p()`, `__px()` and the
  other functions of Locale::TextDomain in `lib/**/*.pm`, `cgi-bin/**/*.pl` and
  every Mason template in `mason/`. The keyword list comes from
  `Locale::TextDomain->options`. A template that does not compile, or is not
  UTF-8, stops `make pot`, unless `po/EXCLUDE` lists it with a reason.
- `make update` copies a translation from `compendium/<lang>.po` only for the
  same English text and context, and never from a fuzzy entry. A text with
  context (`__p`) gets no translation from the compendium: translate it by hand.
- A text that SGN no longer uses stays in `po/<lang>.po` as an obsolete `#~`
  entry. The site ignores it, and `make update` restores it if the text comes
  back.

The same in the Breedbase image, which already has gettext and HTML::Mason
(files that the container writes belong to root):

```sh
docker run --rm -v "$PWD":/w -v /path/to/sgn:/sgn:ro --entrypoint bash \
  breedbase/breedbase:latest -c \
  'apt-get update && apt-get install -y libintl-perl && cd /w && make pot update test SGN=/sgn'
```

## License

MIT ([LICENSE](LICENSE)). Country names marked `iso-codes` come from the
iso-codes project under LGPL-2.1-or-later:
[docs/TRANSLATION_SOURCES.md](docs/TRANSLATION_SOURCES.md),
[LICENSE.iso-codes](LICENSE.iso-codes).
