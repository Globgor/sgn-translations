#!/usr/bin/env python3
"""Regenerate po/templates from an SGN checkout with GNU xgettext; update languages.

    python3 tools/templates.py --sgn /path/to/sgn      (make templates SGN=...)

1. Read SGN's locale/sources.txt (the files that contain messages).
2. Run xgettext on them: Perl files as Perl, JavaScript as JavaScript, Mason
   files through tools/mason.py (a Perl view and a JavaScript view).
3. Assign messages to sections (README "Layout"), using SGN's
   locale/workflows.json, and write po/templates/<section>.pot. Each entry
   lists the browser sections that load it ("#. sections: ...").
4. For each language: join its section files, msgmerge with the new template,
   split by section again.

Before anything is written, every filled translation must still have its
message (same msgctxt, msgid and msgid_plural) in the new extraction. If not,
nothing changes and the lost messages are listed: msgmerge would turn them into
obsolete "#~" entries (or a fuzzy singular for a changed plural), and the site
would show English. --allow-obsolete accepts that.
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import mason
import sections

PERL_KEYWORDS = ["-k", "-kp:1c,2", "-knp:1c,2,3", "-ktranslate:2c,3"]
JS_KEYWORDS = ["-k", "-kt:1c,2", "-ktn:1c,2,3", "-kp:1c,2", "-knp:1c,2,3"]
PERL_SUFFIXES = (".pm", ".pl")
JS_SUFFIXES = (".js", ".mjs", ".cjs")
R_SUFFIXES = (".R", ".r")
NAME = re.compile(r"[a-z][a-z0-9_]*")


def registered_sources(root):
    """Return the relative paths listed in locale/sources.txt."""
    paths = [
        line.strip()
        for line in (root / "locale/sources.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    for path in paths:
        if Path(path).is_absolute() or ".." in Path(path).parts:
            raise ValueError("source path must stay inside the SGN checkout: " + path)
    return paths


def xgettext(language, keywords, directory, names, output):
    """Run GNU xgettext on files named relative to directory; fail loudly."""
    listing = output.with_suffix(".files")
    listing.write_text("".join(name + "\n" for name in names), encoding="utf-8")
    run = subprocess.run(
        [
            "xgettext",
            "--language=" + language,
            "--from-code=UTF-8",
            "--no-wrap",
            *keywords,
            "--directory=" + str(directory),
            "--files-from=" + str(listing),
            "--output=" + str(output),
        ],
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    if run.returncode:
        raise ValueError("xgettext failed (" + language + "): " + run.stderr.strip()[:2000])
    sys.stderr.write(run.stderr)  # xgettext warnings name a file and line; show them
    return output


def read_pot(path):
    """Return {(context, source): message} from an xgettext POT."""
    if not path.exists():  # xgettext writes nothing when it finds nothing
        return {}
    _, entries, _ = sections.parse(path.read_text(encoding="utf-8"))
    result = {}
    for context, source, record in entries:
        values = sections.fields(record)
        references = [
            token
            for line in record.splitlines()
            if line.startswith("#: ")
            for token in line[3:].split()
        ]
        result[context, source] = {
            "context": context,
            "source": source,
            "plural": values.get("msgid_plural"),
            "references": references,
        }
    return result


def extract(root):
    """Extract every registered source with xgettext; return sorted messages."""
    groups = {"perl": [], "js": [], "mason": [], "r": []}
    for path in registered_sources(root):
        if mason.is_mason_source(path):
            groups["mason"].append(path)
        elif path.endswith(PERL_SUFFIXES):
            groups["perl"].append(path)
        elif path.endswith(JS_SUFFIXES):
            groups["js"].append(path)
        elif path.endswith(R_SUFFIXES):
            groups["r"].append(path)
        else:
            raise ValueError("unsupported source file type: " + path)
    if groups["r"]:
        print(
            f"templates: warning: {len(groups['r'])} R files in sources.txt are not extracted"
            " (GNU xgettext has no R parser)",
            file=sys.stderr,
        )
    with tempfile.TemporaryDirectory(prefix="sgn-i18n-xgettext-") as temporary:
        work = Path(temporary)
        for view in ("perl", "js"):
            for path in groups["mason"]:
                (work / view / path).parent.mkdir(parents=True, exist_ok=True)
        for path in groups["mason"]:
            try:
                perl, js = mason.views((root / path).read_text(encoding="utf-8"))
            except ValueError as error:
                raise ValueError(path + ": " + str(error)) from error
            (work / "perl" / path).write_text(perl, encoding="utf-8")
            (work / "js" / path).write_text(js, encoding="utf-8")
        outputs = []
        for language, keywords, directory, names, name in (
            ("Perl", PERL_KEYWORDS, root, groups["perl"], "perl.pot"),
            ("JavaScript", JS_KEYWORDS, root, groups["js"], "js.pot"),
            ("Perl", PERL_KEYWORDS, work / "perl", groups["mason"], "mason-perl.pot"),
            ("JavaScript", JS_KEYWORDS, work / "js", groups["mason"], "mason-js.pot"),
        ):
            if names:
                outputs.append(xgettext(language, keywords, directory, names, work / name))
        merged = {}
        for output in outputs:
            for key, message in read_pot(output).items():
                if key not in merged:
                    merged[key] = message
                elif merged[key]["plural"] != message["plural"]:
                    raise ValueError("conflicting plural source: " + str(key[0]))
                else:
                    merged[key]["references"] += message["references"]
    for message in merged.values():
        message["references"] = sorted(set(message["references"]), key=reference_order)
    return [merged[key] for key in sorted(merged)]


def reference_order(reference):
    """Sort file:line references by file, then by line number."""
    path, _, line = reference.rpartition(":")
    return (path, int(line) if line.isdigit() else 0)


# The browser partition rule is unchanged from the reviewed SGN tooling.
# pylint: disable=too-many-branches,too-many-locals
def partition_sources(root, messages):
    """Assign reviewed sources and their authored UI components to workflows."""
    manifest = json.loads((root / "locale/workflows.json").read_text())
    if manifest.get("schema") != 1:
        raise ValueError("unsupported workflow manifest")
    owners = manifest["source_workflows"]
    registered = set(registered_sources(root))
    if set(owners) != registered or any(
        not NAME.fullmatch(group) or group == sections.COMMON for group in owners.values()
    ):
        raise ValueError("workflow assignments must exactly cover registered sources")
    common = set(manifest["common_sources"])
    prefixes = manifest["common_context_prefixes"]
    if not common <= registered or any(not isinstance(p, str) or not p for p in prefixes):
        raise ValueError("invalid shared workflow sources or contexts")
    # Follow authored component/class references, not aggregate webpack imports:
    # globally defining a class does not mean every page invokes that workflow.
    edges = {}
    for path in registered - common:
        text = (root / path).read_text(encoding="utf-8")
        targets = set()
        if path.startswith("mason/"):
            for match in re.finditer(r"<&\|?\s*[\'\"]?([A-Za-z0-9_./-]+\.mas)", text):
                value = match[1]
                target = "mason" + value if value.startswith("/") else str(Path(path).parent / value)
                if target in registered:
                    targets.add(target)
        if Path(path).suffix in (".mas", ".js", ".mjs", ".cjs"):
            for name in re.findall(r"\b(?:CXGN|solGS)(?:\.[A-Za-z][A-Za-z0-9_]*)+", text):
                target = "js/source/legacy/" + name.replace(".", "/") + ".js"
                if target in registered:
                    targets.add(target)
        edges[path] = targets - common
    groups = {group: {p for p, owner in owners.items() if owner == group} for group in sorted(set(owners.values()))}
    for paths in groups.values():
        pending = list(paths - common)
        while pending:
            for target in edges.get(pending.pop(), set()) - paths:
                paths.add(target)
                pending.append(target)

    def file_of(reference):
        return reference.rsplit(":", 1)[0]

    common_contexts = {
        m["context"]
        for m in messages
        if m["context"].startswith(tuple(prefixes)) or any(file_of(ref) in common for ref in m["references"])
    }
    result = {sections.COMMON: [m for m in messages if m["context"] in common_contexts]}
    for group, paths in groups.items():
        contexts = {
            m["context"]
            for m in messages
            if m["context"] not in common_contexts and any(file_of(ref) in paths for ref in m["references"])
        }
        result[group] = [m for m in messages if m["context"] in contexts]
    return result


# pylint: enable=too-many-branches,too-many-locals


def section_templates(root, messages):
    """Return {section: POT text}; entries name the browser sections that load them."""
    manifest_path = root / "locale/workflows.json"
    if not manifest_path.is_file():
        return {sections.COMMON: sections.pot(messages)}
    groups = partition_sources(root, messages)
    loaded_by = {}
    for name, part in groups.items():
        for message in part:
            loaded_by.setdefault((message["context"], message["source"]), []).append(name)
    owned = sections.ownership(messages, groups, json.loads(manifest_path.read_text()))
    return {name: sections.pot(part, loaded_by) for name, part in owned.items()}


def lost_translations(directory, messages):
    """Return the contexts of filled translations that the new extraction lacks."""
    current = {(m["context"], m["source"], m["plural"]) for m in messages}
    lost = []
    for text in sections.read_language(directory).values():
        _, entries, _ = sections.parse(text)
        for context, source, record in entries:
            values = sections.fields(record)
            filled = any(value for key, value in values.items() if key.startswith("msgstr"))
            if filled and (context, source, values.get("msgid_plural")) not in current:
                lost.append(context)
    return sorted(lost)


def update_language(directory, template, owners, names):
    """Merge one language's section files with the full template and split again."""
    with tempfile.TemporaryDirectory(prefix="sgn-i18n-merge-") as temporary:
        source = Path(temporary) / "source.po"
        source.write_text(sections.merge(sections.read_language(directory)), encoding="utf-8")
        merged = Path(temporary) / "merged.po"
        run = subprocess.run(
            ["msgmerge", "--quiet", "--no-wrap", "-o", str(merged), str(source), str(template)],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if run.returncode:
            raise ValueError("msgmerge rejected " + str(directory) + ": " + run.stderr.strip())
        text = merged.read_text(encoding="utf-8")
    sections.write_language(directory, sections.split(text, owners, names))


def main():
    """Extract, write templates and update every language folder."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sgn", type=Path, required=True, help="SGN source checkout")
    parser.add_argument("--catalogs", type=Path, default=sections.CATALOGS, help="default: po/ in this repository")
    parser.add_argument(
        "--allow-obsolete", action="store_true", help="update even if filled translations lose their message"
    )
    args = parser.parse_args()
    root = args.sgn.resolve()
    catalogs = args.catalogs.resolve()
    if not (root / "locale/sources.txt").is_file():
        raise ValueError("--sgn must name an SGN checkout with locale/sources.txt")
    messages = extract(root)
    templates = section_templates(root, messages)
    directories = sections.languages(catalogs)
    lost = {directory.name: lost_translations(directory, messages) for directory in directories}
    if any(lost.values()) and not args.allow_obsolete:
        lines = [
            f"{name}: {len(contexts)} filled translations lose their message, e.g. " + ", ".join(contexts[:5])
            for name, contexts in lost.items()
            if contexts
        ]
        raise ValueError(
            "nothing written; the new extraction lacks messages that have translations.\n"
            + "\n".join(lines)
            + "\nCheck that --sgn is the right checkout (docs/EXTRACTION.md);"
            " to accept the loss, add --allow-obsolete (make templates ALLOW_OBSOLETE=1)."
        )
    sections.write_templates(catalogs, templates)
    owners, names = sections.owners_from_templates(catalogs / sections.TEMPLATES)
    with tempfile.TemporaryDirectory(prefix="sgn-i18n-template-") as temporary:
        template = Path(temporary) / "sgn.pot"
        template.write_text(sections.pot(messages), encoding="utf-8")
        for directory in directories:
            update_language(directory, template, owners, names)
    print(
        f"templates: {len(messages)} messages in {len(templates)} sections;"
        f" languages updated: {' '.join(d.name for d in directories) or 'none'}"
    )
    for name, contexts in lost.items():
        if contexts:
            print(f"templates: {name}: {len(contexts)} translations became obsolete (#~) or fuzzy")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print("templates: " + str(error), file=sys.stderr)
        raise SystemExit(1) from error
