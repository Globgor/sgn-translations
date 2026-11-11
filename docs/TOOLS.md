# Source tools

Only the release builder needs these tools. A translator needs only Poedit or
the GitHub editor. A ready-pack operator needs Linux/POSIX and Python 3.9 or
newer. See [who runs each step](TRANSLATOR.md).

The tools read SGN; they never write into it. Every command that reads SGN
source takes `--sgn /path/to/sgn` (the old name `--root` still works). From the
SGN checkout they read:

- `locale/sources.txt`: the source files that contain messages;
- `locale/workflows.json`: the page group (section) of each source file;
- the listed source files themselves.

The catalogs come from `po/` in this repository (`--catalogs DIR` for another
folder). Build output goes to `build/` here unless `--output` is given.
Relative output paths are relative to the current folder.

## Requirements

- Python 3.9 or newer and GNU gettext (`msgfmt`, `msgcat`, `msgmerge`).
- Perl with PPI 1.272 or newer and JSON::PP.
- Node with Acorn 8.18.0. Install the pinned dependency in this repository:

  ```sh
  npm ci --prefix tools --ignore-scripts
  ```

- For marked R files, a tested R/jsonlite pair: 4.5.0/2.0.0 or 4.5.1/1.8.7.
  Use a separate build environment if the scientific application uses another R.

On Ubuntu 24.04, `sudo scripts/install-ci-deps.sh` installs all of them.

## Commands

| Command | Needs SGN | What it does |
| --- | --- | --- |
| `extract --sgn PATH` | yes | Write `po/templates/<section>.pot`. |
| `update --sgn PATH` | yes | `extract`, then merge and re-split every language. |
| `freeze --sgn PATH --application-version V --output FILE` | yes | Write a release snapshot (`release.json` + `.pot`). |
| `prepare --sgn PATH --application-version V --output DIR` | yes | Make a translator workspace from `po/`. |
| `prepare --release FILE --po FILE --output DIR` | no | Same, from a frozen release. |
| `package --workspace DIR --output DIR` | no | Make ready packs from a workspace. |
| `build [--sgn PATH \| --release FILE]` | optional | Compile JSON catalogs (checks that templates are current). |
| `init`, `review` | optional | Start a language; export a review batch. |
| `split`, `merge` | no | Section files to one PO and back, losslessly. |
| `check` | no | Structure checks of all catalogs. |
| `create`, `validate`, `install`, `activate`, `rollback`, `doctor` | no | Operator pack commands. |

Run `python3 tools/sgn-i18n COMMAND --help` for options.

## Tests

```sh
scripts/ci.sh
SGN_CHECKOUT=/path/to/sgn scripts/ci.sh   # also the tests that read SGN files
```

Without `SGN_CHECKOUT`, 10 tests are skipped and say so: the manual chapter
checks (need SGN's English chapters), the marked-call counts in
`js/source/legacy/CXGN/Trial.js` and `lib/SGN/Controller/AJAX/User.pm`, the
Mason special components and `t/unit/SGN/i18n-fixtures.json`.

Supported source files are Perl, standard JavaScript, marked R, Mason `.mas`
and reviewed `autohandler`/`dhandler` files. JSX, TypeScript and other binding
patterns need an explicit adapter. Parser errors stop the build; they do not
produce an empty catalog.

Custom helper commands use JSON argument arrays, without a shell:
`SGN_I18N_PERL_COMMAND`, `SGN_I18N_JAVASCRIPT_COMMAND`,
`SGN_I18N_R_EXTRACT_COMMAND`, `SGN_I18N_R_DISCOVERY_COMMAND`.

## Release automation

Use `prepare` once per release to make the editor folder, then `package` after
saved translations are reviewed. The files in `po/` remain unchanged.
The installer can use `install --activate`; locale and hash come from the checked
manifest. Plain install still stages without selecting anything.

`doctor` is read-only: it checks selected/rollback file checksums without running
migration recovery. Its optional site check sends HEAD requests to the existing
runtime/bootstrap endpoints, without executing JavaScript or following redirects.
It reports requested/effective parent languages separately. Local user checks
are not proof of the SGN process's access, and language-response headers do not
prove an exact remote package or all application workflows.

Keep format rules in `catalog_format.py`, building in `catalog.py`, the section
layout in `sections.py`, checks in `check_catalogs.py` and installing in
`pack.py`.
