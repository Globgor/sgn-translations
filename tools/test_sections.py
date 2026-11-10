#!/usr/bin/env python3
"""Per-section PO layout: lossless split/merge and the ownership rule."""

import subprocess
import sys
import tempfile
import unittest

# Test names state their contracts.
# pylint: disable=missing-function-docstring
from pathlib import Path

import sections
from catalog import init_po
from extract import pot

TOOLS = Path(__file__).resolve().parent
PLURAL = "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<12 || n%100>14) ? 1 : 2);"


def message(context, source, *references, plural=None):
    return {"context": context, "source": source, "plural": plural, "references": list(references)}


MESSAGES = [
    message("common.save", "Save", "mason/shared.mas:1", "mason/trial.mas:4"),
    message("cross.panel", "Cross", "mason/crosses/panel.mas:2", "mason/trial.mas:9"),
    message("seedlot.count", "%{count} seedlot", "mason/seedlot.mas:3", plural="%{count} seedlots"),
    message("trial.title", "Trial", "mason/trial.mas:1"),
    message("trial.title", "Trial (old)", "mason/trial.mas:7"),
]
MANIFEST = {
    "source_workflows": {
        "mason/shared.mas": "global",
        "mason/trial.mas": "trial_card",
        "mason/crosses/panel.mas": "crosses",
        "mason/seedlot.mas": "seedlots",
    }
}
GROUPS = {
    "common": [MESSAGES[0]],
    # trial_card includes the cross panel through an authored component.
    "trial_card": [MESSAGES[1], MESSAGES[3], MESSAGES[4]],
    "crosses": [MESSAGES[1]],
    "seedlots": [MESSAGES[2]],
    "global": [],
}


class SectionTests(unittest.TestCase):
    """Exercise ownership, split and merge."""

    def catalog(self):
        text = "# Translator notice kept in every section header\n" + init_po(MESSAGES, "uk", "ltr", PLURAL)
        text = text.replace('msgid "Trial"\nmsgstr ""', 'msgid "Trial"\nmsgstr "Дослід"')
        text = text.replace(
            'msgctxt "common.save"\nmsgid "Save"\nmsgstr ""',
            '# reviewer note\n#, fuzzy\nmsgctxt "common.save"\nmsgid "Save"\nmsgstr "Зберегти"',
        )
        return text + '\n#~ msgctxt "gone.away"\n#~ msgid "Old"\n#~ msgstr "Старе"\n'

    def test_ownership_common_first_then_first_source_file_owner(self):
        owned = sections.ownership(MESSAGES, GROUPS, MANIFEST)
        self.assertEqual(
            {name: [m["context"] for m in part] for name, part in owned.items()},
            {
                "common": ["common.save"],
                # first sorted source file mason/crosses/panel.mas belongs to crosses
                "crosses": ["cross.panel"],
                "seedlots": ["seedlot.count"],
                "trial_card": ["trial.title", "trial.title"],
            },
        )
        self.assertNotIn("global", owned)

    def test_ownership_without_manifest_is_common(self):
        self.assertEqual(sections.ownership(MESSAGES, {"common": MESSAGES}, {}), {"common": MESSAGES})

    def test_ownership_must_stay_inside_browser_partitions(self):
        groups = {**GROUPS, "crosses": []}
        with self.assertRaisesRegex(ValueError, "left the browser partition"):
            sections.ownership(MESSAGES, groups, MANIFEST)

    def test_split_then_merge_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            catalogs = Path(directory)
            templates = sections.templates_for(MESSAGES, GROUPS, MANIFEST)
            sections.write_templates(catalogs, templates)
            self.assertEqual(sections.merge(sections.read_templates(catalogs)), pot(MESSAGES))
            owners, names = sections.owners_from_templates(catalogs / "templates")
            text = self.catalog()
            parts = sections.split(text, owners, names)
            self.assertEqual(sorted(parts), ["common", "crosses", "seedlots", "trial_card"])
            self.assertIn("#~ msgid", parts["common"])
            self.assertIn("# reviewer note", parts["common"])
            for part in parts.values():
                self.assertTrue(part.startswith("# Translator notice"))
            sections.write_language(catalogs / "uk", parts)
            self.assertEqual(sections.merge(sections.read_language(catalogs / "uk")), text)
            with self.assertRaisesRegex(ValueError, "already has PO files"):
                sections.write_language(catalogs / "uk", parts)

    def test_merge_accepts_wrapped_lines_and_rejects_conflicts(self):
        owners = {"common.save": "common", "trial.title": "trial_card"}
        text = init_po(MESSAGES[:1] + MESSAGES[3:4], "uk", "ltr", PLURAL)
        parts = sections.split(text, owners, ["common", "trial_card"])
        wrapped = parts["trial_card"].replace('msgid "Trial"', 'msgid ""\n"Tri"\n"al"')
        merged = sections.merge({**parts, "trial_card": wrapped})
        self.assertIn('"Tri"\n"al"', merged)
        with self.assertRaisesRegex(ValueError, "two sections"):
            sections.merge({**parts, "trial_card": parts["common"]})
        changed = parts["trial_card"].replace("Language: uk", "Language: es")
        with self.assertRaisesRegex(ValueError, "Language differs"):
            sections.merge({**parts, "trial_card": changed})
        with self.assertRaisesRegex(ValueError, "no common.po"):
            sections.merge({"trial_card": parts["trial_card"]})
        with self.assertRaisesRegex(ValueError, "no template"):
            sections.split(text, {"common.save": "common"}, ["common"])

    def test_command_line_split_and_merge(self):
        with tempfile.TemporaryDirectory() as directory:
            catalogs = Path(directory) / "po"
            sections.write_templates(catalogs, sections.templates_for(MESSAGES, GROUPS, MANIFEST))
            source = Path(directory) / "uk.po"
            source.write_text(self.catalog(), encoding="utf-8")
            tool = [sys.executable, "-B", str(TOOLS / "sgn-i18n")]
            common = ["--catalogs", str(catalogs), "--language", "uk"]
            run = subprocess.run(tool + ["split", *common, "--po", str(source)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            output = Path(directory) / "merged.po"
            run = subprocess.run(tool + ["merge", *common, "--output", str(output)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(output.read_bytes(), source.read_bytes())
            run = subprocess.run(tool + ["merge", *common, "--output", str(output)], capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("refusing to overwrite", run.stderr)


if __name__ == "__main__":
    unittest.main()
