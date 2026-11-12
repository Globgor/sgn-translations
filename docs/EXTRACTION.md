# Templates from SGN (make templates)

`make templates SGN=/path/to/sgn` makes `po/templates/` from an SGN checkout
and updates every language:

1. Read SGN's `locale/sources.txt` (the files with interface messages) and
   `locale/workflows.json` (the section of each file).
2. Run GNU `xgettext` on Perl (`.pm`, `.pl`) and JavaScript (`.js`) files.
   Keywords: Perl `p:1c,2`, `np:1c,2,3`, `translate:2c,3`; JavaScript `t:1c,2`,
   `tn:1c,2,3`, `p:1c,2`, `np:1c,2,3`.
3. Mason files (`.mas`, `autohandler`, `dhandler`) go through
   `tools/mason.py` first. It writes a Perl view and a JavaScript view of each
   file with the same line numbers; `xgettext` reads the views.
4. Write `po/templates/<section>.pot`. The comment `#. sections:` names the
   browser sections that load the message.
5. For each language: join the section files, `msgmerge` with the new
   template, split by section again.

Review the result with `git diff`, run `make check`, then commit.

## Which SGN checkout

Use the SGN branch whose `locale/sources.txt` lists all marked files.
Upstream SGN at first marks only the site frame: 12 files, 111 messages, one
section. The full templates (15,398 messages in 28 sections) come from the
branch of solgenomics/sgn PR #6386 (commit `7bcd519e17`) until the section
pull requests are merged upstream. Do not run `make templates` against upstream
SGN before that: the other 15,287 translated messages would leave the
templates.

## Guard against lost translations

Before it writes anything, `make templates` checks that every filled
translation still has its message (same context, English text and plural) in
the new extraction. If not, it writes nothing and lists the messages per
language. Against upstream SGN with 12 files it stops with
`15287 filled translations lose their message` for each language.

`make templates SGN=... ALLOW_OBSOLETE=1` accepts the loss. Then standard
`msgmerge` does this, checked on a copy of `po/`:

- A message that is gone becomes an obsolete `#~` entry at the end of
  `common.po`. The text stays in the file; the build does not use it.
- When the message comes back, `msgmerge` restores the obsolete translation
  unchanged. A run against upstream SGN (12 files) followed by a run against
  `7bcd519e17` gave the same files as a direct run against `7bcd519e17`.
- A message whose English text changed gets the old translation as a fuzzy
  guess. The site shows English until a translator confirms it.
- A new message can also get a fuzzy guess from a similar message, which is
  often wrong. Read every new fuzzy entry before you confirm it.
- A plural message that becomes singular keeps only its first form, as fuzzy.
- A section that has no messages any more loses its file.

## Result against 7bcd519e17

The committed templates hold the message list of PR #6386 (made by its own
extractor): 15,398 messages, 15,393 contexts (5 contexts have two English
texts). `make templates` against `7bcd519e17` finds 15,396 of them;
15,395 match exactly. It stops on the 3 messages below, so the committed
templates stay as they are. No translation is lost.

| Group | Count | Cause | Fix |
|---|---|---|---|
| Not found | 2 | JavaScript passes the English text in parentheses: `SGN.i18n.p("solgs.browser.job_submission_failed", ("Error occurred ..."))` in `js/source/legacy/solGS/solGS.js:412` and `solgs.browser.predicted_output_check_error` in `js/source/legacy/solGS/listTypeSelectionPopulation.js:392`. `xgettext` reads string literals only. | In SGN: remove the parentheses. |
| Plural lost | 1 | `cgi-bin/phenome/trait.pl:101` gives the plural in an option hash: `translate($i18n, "phenotype.root.population_count_suffix", "populations", undef, {plural => [...]})`. `xgettext` keywords cannot read a hash, so it extracts a singular message. | In SGN: use the plural call (`np` / `tn`) with the plural text as an argument. |
| New | 2 | `SGN::I18N::translate($c)->p(...)` in `lib/SGN/Controller/Image.pm:24` and `:57` (`community.image.image_not_found`, `community.image.no_image_file_uploaded`). The #6386 extractor did not see them; `xgettext` does. | None needed in SGN. `msgmerge` adds them as fuzzy guesses from similar messages (uk: «Дослід не знайдено.» for "Image not found."); the site shows English until a translator rewrites and confirms them. |
| Line numbers | 3 | Multi-line `np(...)` calls in `js/source/legacy/CXGN/List.js`: `xgettext` gives the line of the English text, one line after the call. | None needed. |
| R files | 31 files, 0 messages | `sources.txt` lists 31 R files; GNU `xgettext` has no R parser. None of them has interface messages now, so nothing is missing. `make templates` prints a warning. | If R messages are added later, they need another route (R's own `tools::xgettext2pot`). |

After the first two fixes in SGN, `make templates` against that branch gives
the committed messages plus the 2 new ones, and needs no `ALLOW_OBSOLETE`.

An earlier prototype missed 335 messages: the 2 JavaScript messages above and
333 in Mason files (54 of them in `mason/dataset/publish.mas`). The current
`tools/mason.py` finds all 333. Switching off one of its rules alone loses:
103 messages for component calls `<& /path.mas, args &>` (`xgettext` reads the
path as a Perl regex), 14 for hash keys such as `$ARGS{q}` (read as a `q{...}`
string), 6 for Mason code inside `<script>`. The groups overlap.

`xgettext` also warns about e-mail addresses, URLs and a `\r` in some messages,
and about markup at `mason/site/footer/body.mas:92`. These are warnings; no
message is missing because of them.
