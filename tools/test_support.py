"""Small catalogs for the tool tests."""

import sections
from catalog_format import po_quote

UK_PLURAL = "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<12 || n%100>14) ? 1 : 2);"


def message(context, source, *references, plural=None):
    """One extracted message as the tools pass it around."""
    return {"context": context, "source": source, "plural": plural, "references": list(references)}


def language_po(messages, locale="uk", plural_forms=UK_PLURAL, direction="ltr", name="Українська"):
    """Return an untranslated PO catalog with the SGN header fields."""
    nplurals = int(plural_forms.split("nplurals=")[1].split(";")[0])
    header = [
        "Project-Id-Version: SGN",
        "Language: " + locale,
        "MIME-Version: 1.0",
        "Content-Type: text/plain; charset=UTF-8",
        "Content-Transfer-Encoding: 8bit",
        "X-SGN-Language-Name: " + name,
        "Plural-Forms: " + plural_forms,
        "X-SGN-Direction: " + direction,
    ]
    blocks = ['msgid ""\nmsgstr ""\n' + "\n".join(po_quote(line + "\n") for line in header)]
    for item in sorted(messages, key=lambda m: (m["context"], m["source"])):
        lines = ["#: " + " ".join(item["references"])] if item["references"] else []
        lines += ["msgctxt " + po_quote(item["context"]), "msgid " + po_quote(item["source"])]
        if item["plural"]:
            lines.append("msgid_plural " + po_quote(item["plural"]))
            lines += [f'msgstr[{index}] ""' for index in range(nplurals)]
        else:
            lines.append('msgstr ""')
        blocks.append("\n".join(lines))
    return sections.join(blocks[0], blocks[1:])
