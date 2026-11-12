#!/usr/bin/env python3
"""Check the structure of every catalog file. A missing translation is allowed.

Checks, for each po/<language>/<section>.po:

- the file has exactly the messages of po/templates/<section>.pot
  (same msgctxt, msgid and msgid_plural; nothing missing, nothing extra);
- the header names the language and its standard plural rule and direction,
  and these fields agree in every section file of the language;
- every plural message has all msgstr[i] forms of the language, all filled
  when any one is filled;
- each filled translation keeps the %{name} values of its English source;
- `msgfmt --check` accepts the file;
- no letters from a script that does not belong to the language;
- no forbidden term from glossary/<language>.tsv.
"""

import argparse
import collections
import re
import subprocess
import sys
from pathlib import Path

import sections
from catalog_format import placeholders, validate_control_placeholders
from plural import parse_plural

# Standard gettext/CLDR plural rules and text direction of each language.
# To add a language, add a line here and a po/<language>/ folder.
LANGUAGES = {
    "uk": {
        "plural": "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<12 || n%100>14) ? 1 : 2);",
        "direction": "ltr",
        "forbidden_scripts": ("Arabic",),
    },
    "es": {
        "plural": "nplurals=2; plural=(n != 1);",
        "direction": "ltr",
        "forbidden_scripts": ("Arabic", "Cyrillic"),
    },
    "ar": {
        "plural": (
            "nplurals=6; plural=(n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3"
            " : n%100>=11 && n%100<=99 ? 4 : 5);"
        ),
        "direction": "rtl",
        "forbidden_scripts": ("Cyrillic",),
    },
}
SCRIPTS = {
    "Arabic": re.compile("[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]"),
    "Cyrillic": re.compile("[Ѐ-ԯᲀ-᲏ⷠ-ⷿꙀ-ꚟ]"),
}
GLOSSARY = sections.REPOSITORY / "glossary"


class Problems:
    """Collect problems; print them grouped by file."""

    def __init__(self):
        self.items = []

    def add(self, where, text):
        """Record one problem."""
        self.items.append(str(where) + ": " + text)


def read_glossary(path):
    """Read 'forbidden<TAB>preferred[<TAB>note[<TAB>English regex]]' rules.

    '#' starts a comment line. With the fourth column the rule applies only to
    messages whose English text (msgid, a newline, msgid_plural) matches that
    Python regular expression.
    """
    rules = []
    if not path.is_file():
        return rules
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        columns = line.split("\t")
        if len(columns) < 2 or not columns[0].strip() or not columns[1].strip():
            raise ValueError(f"{path}:{number}: expected forbidden<TAB>preferred")
        english = None
        if len(columns) > 3 and columns[3].strip():
            try:
                english = re.compile(columns[3].strip())
            except re.error as error:
                raise ValueError(f"{path}:{number}: bad English regex: {error}") from error
        rules.append((columns[0].strip(), columns[1].strip(), english))
    return rules


def entries(text):
    """Yield (identity, values, fuzzy) for the active messages of PO text."""
    _, messages, _ = sections.parse(text)
    for _, _, record in messages:
        values = sections.fields(record)
        fuzzy = any(line.startswith("#,") and "fuzzy" in line for line in record.splitlines())
        yield (values.get("msgctxt"), values["msgid"], values.get("msgid_plural")), values, fuzzy


def forms_of(values):
    """Return the msgstr forms of one message in index order."""
    if "msgstr" in values:
        return [values["msgstr"]]
    indexed = sorted((int(key[7:-1]), text) for key, text in values.items() if key.startswith("msgstr["))
    return [text for _, text in indexed]


def run_msgfmt(path, problems):
    """Let GNU gettext check syntax, format strings and header."""
    run = subprocess.run(
        ["msgfmt", "--check", "-o", "/dev/null", str(path)], capture_output=True, text=True, timeout=60, check=False
    )
    if run.returncode:
        problems.add(path, "msgfmt --check failed: " + run.stderr.strip()[:500])


# One explicit pass over every rule keeps the report in file order.
# pylint: disable=too-many-locals,too-many-branches,too-many-statements
def check_language(directory, templates, glossary_dir, problems, stats):
    """Check one language folder against the templates."""
    language = directory.name
    rule = LANGUAGES.get(language)
    if rule is None:
        problems.add(directory, "unknown language; add it to LANGUAGES in tools/check_catalogs.py")
        return
    nplurals = parse_plural(rule["plural"])["nplurals"]
    glossary = read_glossary(glossary_dir / (language + ".tsv"))
    files = {path.stem: path for path in sorted(directory.glob("*.po"))}
    for name in sorted(set(templates) - set(files)):
        problems.add(directory, "missing section file " + name + ".po")
    for name in sorted(set(files) - set(templates)):
        problems.add(files[name], "section has no template po/templates/" + name + ".pot")
    first_header = None
    for name, path in files.items():
        if name not in templates:
            continue
        text = path.read_text(encoding="utf-8")
        try:
            header, _, _ = sections.parse(text)
            found = list(entries(text))
        except (ValueError, SyntaxError) as error:
            problems.add(path, "cannot read: " + str(error))
            continue
        values = sections.header_fields(header)
        if values.get("Language") != language:
            problems.add(path, "header Language is " + repr(values.get("Language")) + ", expected " + language)
        if values.get("Plural-Forms") != rule["plural"]:
            problems.add(path, "header Plural-Forms differs from the standard rule: " + rule["plural"])
        if values.get("X-SGN-Direction") != rule["direction"]:
            problems.add(path, "header X-SGN-Direction must be " + rule["direction"])
        language_fields = {key: values.get(key) for key in sections.LANGUAGE_FIELDS}
        if first_header is None:
            first_header = language_fields
        elif language_fields != first_header:
            problems.add(path, "header language fields differ from the other section files")
        run_msgfmt(path, problems)
        identities = {identity for identity, _, _ in found}
        for identity in sorted(templates[name] - identities, key=str):
            problems.add(path, "missing message " + str(identity[0]))
        for identity in sorted(identities - templates[name], key=str):
            problems.add(path, "message not in template " + str(identity[0]))
        for (context, source, plural), fields, fuzzy in found:
            forms = forms_of(fields)
            stats[language]["messages"] += 1
            where = f"{path} [{context}]"
            if plural is not None and len(forms) != nplurals:
                problems.add(where, f"plural message has {len(forms)} msgstr forms, expected {nplurals}")
            if plural is None and "msgstr" not in fields:
                problems.add(where, "singular message must use msgstr, not msgstr[i]")
            filled = [form for form in forms if form]
            if not filled:
                stats[language]["empty"] += 1
                continue
            if not all(form.strip() for form in forms):
                # build.py leaves such a translation out; say so before it merges.
                problems.add(where, "every msgstr form must be filled (the build drops a partly empty translation)")
            if fuzzy:
                stats[language]["fuzzy"] += 1
            else:
                stats[language]["translated"] += 1
            for form in filled:
                for script in rule["forbidden_scripts"]:
                    if SCRIPTS[script].search(form):
                        problems.add(where, script + " letters in a " + language + " translation")
                lowered = form.casefold()
                for forbidden, preferred, english in glossary:
                    if english is not None and not english.search(source + "\n" + (plural or "")):
                        continue
                    if forbidden.casefold() in lowered:
                        problems.add(where, f"glossary: use «{preferred}» instead of «{forbidden}»")
            if fuzzy:
                # Needs Work: the build uses English, so its values are not checked.
                continue
            try:
                expected = placeholders(source)
                if plural is not None and placeholders(plural) != expected:
                    problems.add(where, "English singular and plural use different %{name} values")
                for form in filled:
                    if placeholders(form) != expected:
                        problems.add(where, "translation must keep %{name} values " + str(sorted(expected)))
                validate_control_placeholders(context, source, filled)
            except ValueError as error:
                problems.add(where, str(error))


def count_terms(catalogs, language, patterns):
    """Count filled translations whose text matches each pattern."""
    counts = collections.Counter()
    for path in sorted((catalogs / language).glob("*.po")):
        for _, fields, _ in entries(path.read_text(encoding="utf-8")):
            text = " ".join(forms_of(fields))
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    counts[pattern] += 1
    return {pattern: counts[pattern] for pattern in patterns}


def main():
    """Check all catalogs; exit 1 when any problem is found."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--catalogs", type=Path, default=sections.CATALOGS, help="default: po/ in this repository")
    parser.add_argument("--glossary", type=Path, default=GLOSSARY, help="glossary folder (default: glossary/ here)")
    parser.add_argument("--language", action="append", help="check only this language (repeatable)")
    parser.add_argument(
        "--count",
        action="append",
        default=[],
        metavar="REGEX",
        help="also count translations that match REGEX (for terminology decisions)",
    )
    args = parser.parse_args()
    catalogs = args.catalogs.resolve()
    problems = Problems()
    stats = collections.defaultdict(collections.Counter)
    try:
        _, names = sections.owners_from_templates(catalogs / sections.TEMPLATES)
    except (ValueError, SyntaxError) as error:
        print("templates: " + str(error), file=sys.stderr)
        return 1
    templates = {name: set() for name in names}
    for name in names:
        for identity, _, _ in entries((catalogs / sections.TEMPLATES / (name + ".pot")).read_text(encoding="utf-8")):
            templates[name].add(identity)
    directories = sections.languages(catalogs)
    if args.language:
        directories = [d for d in directories if d.name in args.language]
    if not directories:
        problems.add(catalogs, "no language folders")
    for directory in directories:
        check_language(directory, templates, args.glossary, problems, stats)
    for directory in directories:
        line = {"language": directory.name, **stats[directory.name]}
        if args.count:
            line["count"] = count_terms(catalogs, directory.name, args.count)
        print(line)
    print(
        f"templates: {len(names)} sections, {sum(len(v) for v in templates.values())} messages;"
        f" problems: {len(problems.items)}"
    )
    for item in problems.items[:500]:
        print("FAIL " + item)
    if len(problems.items) > 500:
        print(f"... and {len(problems.items) - 500} more")
    return 1 if problems.items else 0


if __name__ == "__main__":
    raise SystemExit(main())
