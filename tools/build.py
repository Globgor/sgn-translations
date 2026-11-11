#!/usr/bin/env python3
"""Build what SGN reads: one gettext .mo per language and browser JSON per section.

    python3 tools/build.py            (make)

For each po/<lang>/ folder:

- build/LocaleData/<lang>/LC_MESSAGES/sgn.mo: msgcat of the section files,
  then msgfmt --check (domain sgn, msgctxt = key, msgid = English);
- build/js/<lang>/<section>.json: the messages each browser section loads
  ("#. sections:" in the templates), in the SGN catalog JSON schema 1.

Empty and fuzzy (Needs Work) translations are left out and counted. Broken
ones (a missing plural form, a lost %{name} value, a message that is not in
the templates) are left out with one warning each. A site shows English for
every message that is left out.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import sections
from catalog_format import (
    API,
    LOCALE,
    MAX_BYTES,
    SCHEMA,
    json_bytes,
    placeholders,
    validate_control_placeholders,
    validate_language_name,
)
from plural import parse_plural

BUILD = sections.REPOSITORY / "build"


def template_messages(catalogs):
    """Return (messages, {(context, source): [browser sections]}) from the templates."""
    directory = catalogs / sections.TEMPLATES
    loaded_by = sections.loaded_by_from_templates(directory)
    messages = []
    for path in sorted(directory.glob("*.pot")):
        _, entries, _ = sections.parse(path.read_text(encoding="utf-8"))
        for context, source, record in entries:
            messages.append({"context": context, "source": source, "plural": sections.fields(record).get("msgid_plural")})
    messages.sort(key=lambda m: (m["context"], m["source"]))
    return messages, loaded_by


def joined_language(directory, destination):
    """msgcat the section files of one language (common first) into one PO."""
    paths = sorted(directory.glob("*.po"), key=lambda p: (p.stem != sections.COMMON, p.stem))
    if not paths:
        raise ValueError("no PO files in " + str(directory))
    run = subprocess.run(
        ["msgcat", "--use-first", "--no-wrap", "-o", str(destination), *map(str, paths)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if run.returncode:
        raise ValueError("msgcat rejected " + str(directory) + ": " + run.stderr.strip())
    return destination.read_text(encoding="utf-8")


def forms_of(values):
    """Return msgstr forms in index order."""
    if "msgstr" in values:
        return [values["msgstr"]]
    return [text for _, text in sorted((int(k[7:-1]), v) for k, v in values.items() if k.startswith("msgstr["))]


def usable(context, source, values, fuzzy, expected, nplurals):
    """Return the forms of a usable translation, or (None, reason)."""
    plural = values.get("msgid_plural")
    forms = forms_of(values)
    if (context, source, plural) not in expected:
        return None, "not in the templates (run make templates)"
    if not any(form.strip() for form in forms):
        return None, "empty"
    if fuzzy:
        return None, "fuzzy"
    if len(forms) != (nplurals if plural else 1) or not all(form.strip() for form in forms):
        return None, "missing plural forms"
    try:
        variables = placeholders(source)
        if plural is not None and placeholders(plural) != variables:
            return None, "English singular and plural use different %{name} values"
        if any(placeholders(form) != variables for form in forms):
            return None, "translation does not keep the %{name} values " + str(sorted(variables))
        validate_control_placeholders(context, source, forms)
    except ValueError as error:
        return None, str(error)
    return forms, None


# One pass per language keeps the warnings in file order.
# pylint: disable=too-many-locals
def build_language(directory, messages, loaded_by, output, warn):
    """Write the .mo and the browser JSON files of one language."""
    with tempfile.TemporaryDirectory(prefix="sgn-i18n-build-") as temporary:
        text = joined_language(directory, Path(temporary) / "joined.po")
        header, entries, _ = sections.parse(text)
        info = sections.header_fields(header)
        locale = info.get("Language", "")
        if not LOCALE.fullmatch(locale) or locale == "en" or locale != directory.name:
            raise ValueError(str(directory) + ": header Language must be the folder name, not English")
        direction = info.get("X-SGN-Direction", "")
        if direction not in ("ltr", "rtl"):
            raise ValueError(str(directory) + ": X-SGN-Direction must be ltr or rtl")
        rule = parse_plural(info.get("Plural-Forms", ""))
        expected = {(m["context"], m["source"], m["plural"]) for m in messages}
        kept, accepted, skipped = [], {}, {"empty": 0, "fuzzy": 0, "broken": 0}
        for context, source, record in entries:
            values = sections.fields(record)
            fuzzy = any(line.startswith("#,") and "fuzzy" in line for line in record.splitlines())
            forms, reason = usable(context, source, values, fuzzy, expected, rule["nplurals"])
            if reason in ("empty", "fuzzy"):
                skipped[reason] += 1
                continue
            if reason:
                skipped["broken"] += 1
                warn(f"{locale}: {context}: left out, {reason}")
                continue
            kept.append(record)
            accepted[context, source] = {"plural": values.get("msgid_plural"), "forms": forms}
        filtered = Path(temporary) / "usable.po"
        filtered.write_text(sections.join(header, kept), encoding="utf-8")
        mo = output / "LocaleData" / locale / "LC_MESSAGES" / "sgn.mo"
        mo.parent.mkdir(parents=True, exist_ok=True)
        run = subprocess.run(
            ["msgfmt", "--check", "-o", str(mo), str(filtered)], capture_output=True, text=True, timeout=120, check=False
        )
        if run.returncode:
            raise ValueError("msgfmt --check rejected " + locale + ": " + run.stderr.strip())
    base = {
        "schema": SCHEMA,
        "api": API,
        "locale": locale,
        "direction": direction,
        "nplurals": rule["nplurals"],
        "pluralForms": rule.get("normalized", info.get("Plural-Forms")),
        "pluralAst": rule["ast"],
    }
    if "X-SGN-Language-Name" in info:
        base["languageName"] = validate_language_name(info["X-SGN-Language-Name"])
    parts = {}
    for message in messages:
        key = (message["context"], message["source"])
        for name in loaded_by[key]:
            part = parts.setdefault(name, {})
            if key in accepted:
                part[message["context"] + "\x04" + message["source"]] = accepted[key]
    target = output / "js" / locale
    target.mkdir(parents=True, exist_ok=True)
    for name, part in sorted(parts.items()):
        data = json_bytes({**base, "messages": part})
        if len(data) > MAX_BYTES:
            raise ValueError(f"{locale}/{name}.json exceeds {MAX_BYTES} bytes")
        (target / (name + ".json")).write_bytes(data)
    return {"locale": locale, "translated": len(accepted), "total": len(messages), "sections": len(parts), **skipped}


# pylint: enable=too-many-locals


def main():
    """Build all languages into a fresh output folder."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--catalogs", type=Path, default=sections.CATALOGS, help="default: po/ in this repository")
    parser.add_argument("--output", type=Path, default=BUILD, help="default: build/ in this repository")
    args = parser.parse_args()
    catalogs = args.catalogs.resolve()
    messages, loaded_by = template_messages(catalogs)
    stage = Path(tempfile.mkdtemp(prefix=".build-", dir=args.output.resolve().parent))

    def warn(text):
        print("warning: " + text, file=sys.stderr)

    try:
        results = [build_language(d, messages, loaded_by, stage, warn) for d in sections.languages(catalogs)]
        if args.output.exists():
            shutil.rmtree(args.output)
        stage.rename(args.output)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    for result in results:
        print(
            f"{result['locale']}: {result['translated']} of {result['total']} messages translated"
            f" (left out: {result['empty']} empty, {result['fuzzy']} fuzzy, {result['broken']} broken),"
            f" {result['sections']} browser sections"
        )
    print(f"build: {args.output}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print("build: " + str(error), file=sys.stderr)
        raise SystemExit(1) from error
