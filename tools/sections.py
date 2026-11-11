"""Keep each language as one PO file per application section, losslessly.

Layout (relative to the catalog folder, normally ``po/`` in this repository):

    templates/<section>.pot   English messages of one section
    <language>/<section>.po   translations of the same messages

Ownership rule, used whenever templates are regenerated:

1. A message context goes to ``common`` when the browser ``common`` partition
   contains it (shared context prefix, or used in a shared source file).
2. Otherwise it goes to the section that ``locale/workflows.json`` in the SGN
   checkout assigns to the first source file (sorted path) that uses it.

All messages with the same msgctxt stay in one section. Every message is in
exactly one section file per language. Obsolete (``#~``) records are kept at
the end of ``common.po``. The browser sections that load a message can be more
than its owner; templates list them in a ``#. sections:`` comment.

GNU gettext joins files (msgcat) but has no tool that splits one catalog by
such a rule, so split() and merge() are here.
"""

import ast
import re
from pathlib import Path

from catalog_format import po_quote

REPOSITORY = Path(__file__).resolve().parents[1]
CATALOGS = REPOSITORY / "po"
TEMPLATES = "templates"
COMMON = "common"
SECTION = re.compile(r"[a-z][a-z0-9_]*")
FIELD = re.compile(r'^(msgctxt|msgid|msgid_plural|msgstr(?:\[[0-9]+\])?) (".*")$')
# Header fields that define the language; they must agree in every section file.
LANGUAGE_FIELDS = ("Language", "Plural-Forms", "X-SGN-Direction", "X-SGN-Language-Name")


def pot(messages, loaded_by=None):
    """Serialize a deterministic English template (sorted by context, source).

    loaded_by maps (context, source) to the browser sections that load the
    message; it is written as an extracted comment that build.py reads.
    """
    lines = [
        "# SGN internationalization source catalog. Generated; do not edit.",
        'msgid ""',
        'msgstr ""',
        '"Project-Id-Version: SGN i18n prototype 1\\n"',
        '"MIME-Version: 1.0\\n"',
        '"Content-Type: text/plain; charset=UTF-8\\n"',
        '"Content-Transfer-Encoding: 8bit\\n"',
        "",
    ]
    for message in messages:
        if loaded_by is not None:
            lines.append("#. sections: " + " ".join(sorted(loaded_by[message["context"], message["source"]])))
        lines.append("#: " + " ".join(sorted(set(message["references"]))))
        lines += ["msgctxt " + po_quote(message["context"]), "msgid " + po_quote(message["source"])]
        if message["plural"]:
            lines += ["msgid_plural " + po_quote(message["plural"]), 'msgstr[0] ""', 'msgstr[1] ""']
        else:
            lines.append('msgstr ""')
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def loaded_by_from_templates(directory):
    """Read {(context, source): [browser sections]} from the templates' comments."""
    result = {}
    for path in sorted(directory.glob("*.pot")):
        _, entries, _ = parse(path.read_text(encoding="utf-8"))
        for context, source, record in entries:
            names = [
                line[len("#. sections: ") :].split()
                for line in record.splitlines()
                if line.startswith("#. sections: ")
            ]
            result[context, source] = names[0] if names else [path.stem]
    return result


def records(text):
    """Split PO text into blank-line separated records without changing them."""
    # Trailing blank lines (as some gettext writers leave) are not a record.
    parts = text.rstrip("\n").split("\n\n")
    if any(not part.strip("\n") for part in parts):
        raise ValueError("PO text has an empty record (more than one blank line)")
    return parts


def fields(record):
    """Decode msgctxt/msgid/msgid_plural/msgstr fields of one active record."""
    result = {}
    active = None
    for line in record.splitlines():
        match = FIELD.match(line)
        if match:
            active = match[1]
            if active in result:
                raise ValueError("repeated " + active + " in record: " + record[:200])
            result[active] = ast.literal_eval(match[2])
        elif active and line.startswith('"'):
            result[active] += ast.literal_eval(line)
        elif line.startswith("#") or not line:
            active = None
        else:
            raise ValueError("unexpected PO line: " + line[:200])
    return result


def kind(record):
    """Return header, message or obsolete for one record."""
    lines = [line for line in record.splitlines() if line]
    if all(line.startswith("#") for line in lines) and any(line.startswith("#~") for line in lines):
        return "obsolete"
    values = fields(record)
    if "msgid" not in values:
        raise ValueError("PO record without msgid: " + record[:200])
    if values["msgid"] == "" and "msgctxt" not in values:
        return "header"
    return "message"


def parse(text):
    """Return (header record, [(context, source, record)], [obsolete records])."""
    header = None
    messages = []
    obsolete = []
    for index, record in enumerate(records(text)):
        sort = kind(record)
        if sort == "header":
            if index or header is not None:
                raise ValueError("PO header must be the first record")
            header = record
        elif sort == "obsolete":
            obsolete.append(record)
        else:
            values = fields(record)
            messages.append((values.get("msgctxt"), values["msgid"], record))
    if header is None:
        raise ValueError("PO text has no header record")
    seen = set()
    for context, source, _ in messages:
        if (context, source) in seen:
            raise ValueError("duplicate message: " + str(context))
        seen.add((context, source))
    return header, messages, obsolete


def header_fields(header):
    """Read 'Name: value' lines of the PO header msgstr."""
    text = fields(header).get("msgstr", "")
    result = {}
    for line in text.splitlines():
        if ":" in line:
            name, value = line.split(":", 1)
            result[name.strip()] = value.strip()
    return result


def join(header, blocks):
    """Serialize records exactly as gettext writes them: one blank line between."""
    return "\n\n".join([header, *blocks]) + "\n"


def owners_from_templates(directory):
    """Map each msgctxt to the template (section) that owns it."""
    owners = {}
    paths = sorted(directory.glob("*.pot"))
    if not paths:
        raise ValueError("no section templates in " + str(directory))
    for path in paths:
        section = path.stem
        if not SECTION.fullmatch(section):
            raise ValueError("invalid section file name: " + path.name)
        _, messages, _ = parse(path.read_text(encoding="utf-8"))
        for context, _, _ in messages:
            if owners.setdefault(context, section) != section:
                raise ValueError("msgctxt in two templates: " + str(context))
    if COMMON not in {path.stem for path in paths}:
        raise ValueError("templates must include common.pot")
    return owners, [path.stem for path in paths]


def split(text, owners, sections):
    """Return {section: PO text} for one language; every section gets a file."""
    header, messages, obsolete = parse(text)
    result = {section: [] for section in sections}
    for context, _, record in messages:
        if context not in owners:
            raise ValueError("message is in no template; run make templates: " + str(context))
        result[owners[context]].append(record)
    result[COMMON].extend(obsolete)
    return {section: join(header, blocks) for section, blocks in result.items()}


def merge(texts):
    """Join {section: PO text} of one language into one catalog in template order."""
    if COMMON not in texts:
        raise ValueError("language has no common.po")
    parsed = {section: parse(text) for section, text in texts.items()}
    header = parsed[COMMON][0]
    language = {name: header_fields(header).get(name) for name in LANGUAGE_FIELDS}
    messages = []
    obsolete = list(parsed[COMMON][2])
    seen = {}
    for section in sorted(parsed):
        section_header, section_messages, section_obsolete = parsed[section]
        values = header_fields(section_header)
        for name in LANGUAGE_FIELDS:
            if values.get(name) != language[name]:
                raise ValueError(section + ".po header " + name + " differs from common.po")
        for context, source, record in section_messages:
            if (context, source) in seen:
                raise ValueError("message in two sections (" + seen[context, source] + ", " + section + "): " + context)
            seen[context, source] = section
            messages.append((context, source, record))
        if section != COMMON:
            obsolete.extend(section_obsolete)
    messages.sort(key=lambda item: (item[0], item[1]))
    return join(header, [record for _, _, record in messages] + obsolete)


def read_language(directory):
    """Read all section files of one language folder."""
    paths = sorted(directory.glob("*.po"))
    if not paths:
        raise ValueError("no section PO files in " + str(directory))
    for path in paths:
        if not SECTION.fullmatch(path.stem):
            raise ValueError("invalid section file name: " + str(path))
    return {path.stem: path.read_text(encoding="utf-8") for path in paths}


def languages(catalogs):
    """Return language folders under the catalog folder (everything but templates)."""
    return sorted(
        path for path in catalogs.iterdir() if path.is_dir() and path.name != TEMPLATES and not path.name.startswith(".")
    )


def ownership(messages, groups, manifest):
    """Assign every message to exactly one section by the documented rule."""
    if set(groups) == {COMMON}:
        return {COMMON: list(messages)}
    files = manifest["source_workflows"]
    common = {m["context"] for m in groups[COMMON]}
    first = {}
    for message in messages:
        if message["context"] in common:
            continue
        for reference in message["references"]:
            path = reference.rsplit(":", 1)[0]
            if message["context"] not in first or path < first[message["context"]]:
                first[message["context"]] = path
    result = {COMMON: []}
    members = {name: {m["context"] for m in part} for name, part in groups.items()}
    for message in messages:
        context = message["context"]
        section = COMMON if context in common else files[first[context]]
        if context not in members.get(section, ()):
            raise ValueError("ownership left the browser partition: " + context)
        result.setdefault(section, []).append(message)
    return {name: result[name] for name in sorted(result)}


def write_templates(catalogs, templates):
    """Replace the stored templates with the given set."""
    directory = catalogs / TEMPLATES
    directory.mkdir(parents=True, exist_ok=True)
    for path in directory.glob("*.pot"):
        if path.stem not in templates:
            path.unlink()
    for name, text in templates.items():
        (directory / (name + ".pot")).write_text(text, encoding="utf-8")


def write_language(directory, texts):
    """Write {section: PO text}; drop section files that no longer exist."""
    directory.mkdir(parents=True, exist_ok=True)
    for path in directory.glob("*.po"):
        if path.stem not in texts:
            path.unlink()
    for name, text in texts.items():
        (directory / (name + ".po")).write_text(text, encoding="utf-8")
