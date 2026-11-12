# Validation record

What was checked when this repository moved to standard GNU gettext
(2026-11-11). Logs stayed outside Git.

## Same output as the #6386 tools

| Check | Result |
|---|---|
| Section files | `po/<lang>/*.po` joined by `tools/sections.py` are byte-identical to `locale/<lang>/LC_MESSAGES/sgn.po` of sgn `7bcd519e17` (uk, es, ar), before the header clean-up. |
| Templates | The `#. sections:` comments are the only change to `po/templates/`: 15,398 lines added, no message, reference or owner changed. |
| Browser JSON | All 87 files of `build/js/` (29 sections x uk, es, ar) are byte-identical to the output of the `7bcd519e17` compiler (`bin/i18n/catalog.py`) without its `sourceRevision` field. |
| Extraction | `make templates` against `7bcd519e17`: see [EXTRACTION.md](EXTRACTION.md#result-against-7bcd519e17). Same result with gettext 1.0 (Fedora) and 0.21 (Ubuntu 24.04). |

## Clean Ubuntu 24.04

Container `ubuntu:24.04` with only `gettext python3 make` installed
(Python 3.12.3, GNU Make 4.3, gettext 0.21):

| Command | Result |
|---|---|
| `make check` on branch `fix/wrong-script-14` | problems: 0; `msgfmt --check` passes for ar, es, uk; 32 tool tests pass (6 skip without `SGN=`) |
| `make` | exit 0; `sgn.mo` uk 2.8 MB, es 2.4 MB, ar 2.6 MB; 90 files; largest JSON `js/uk/trial_card.json` 560 KB (limit 2 MiB) |
| `make check` on `main` | fails only on the 14 Arabic texts in uk/es translations (13 uk, 1 es) |
| `make check SGN=<7bcd519e17>` | the manual tests run; 1 skips (no R) |
| `make templates SGN=<7bcd519e17>` | stops: 3 translations per language would lose their message |

## Breedbase image

`breedbase/breedbase:latest` (Debian 13, gettext 0.23.1, Python 3.13.5,
GNU Make 4.4.1, Node 24) has everything `make` needs.

| Check | Result |
|---|---|
| `make` | exit 0, same file sizes as above |
| libintl-perl 1.35, `gettext_pp` (after `apt-get install libintl-perl`) | `dpgettext` returns the uk text; `dnpgettext` returns the uk plural forms for 1, 2, 5, 11, 21; a fuzzy entry, a changed English text and an unknown key return English; the `.mo` header gives `X-SGN-Language-Name: Українська`, `X-SGN-Direction: ltr` (ar: `rtl`) |
| `static/js/sgn-i18n.js` of the SGN core branch, under Node | accepts all 87 JSON files; `p` and `np` return the uk texts |

## Corrections (re-check 2026-11-12)

- `make` created `build/` with mode 0700 (`tempfile.mkdtemp`). A web server
  that runs as another user (`www-data`) could not read it. `tools/build.py`
  now gives `build/` the mode of the umask; `tools/test_build.py` checks it.
- Image `breedbase/breedbase@sha256:a4cec576...` has neither libintl-perl nor
  this repository; `make check` and `make` work in it (output identical to
  Ubuntu 24.04).
- `make check` now rejects a translation with some msgstr forms empty; before,
  it passed the check and the build silently left it out.

## Not checked

- A running SGN site with these files (the core branch has its own tests).
- Text quality: all translations are machine drafts.
- The manual build with R and the PDF export.
