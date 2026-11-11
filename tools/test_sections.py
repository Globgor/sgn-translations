"""Per-section PO layout: lossless split/merge and the ownership rule."""

import tempfile
import unittest

# Test names state their contracts.
# pylint: disable=missing-function-docstring
from pathlib import Path

import sections
from test_support import language_po, message


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
        text = "# Translator notice kept in every section header\n" + language_po(MESSAGES)
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
            owned = sections.ownership(MESSAGES, GROUPS, MANIFEST)
            sections.write_templates(catalogs, {name: sections.pot(part) for name, part in owned.items()})
            stored = {path.stem: path.read_text() for path in (catalogs / "templates").glob("*.pot")}
            self.assertEqual(sections.merge(stored), sections.pot(MESSAGES))
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
            # A section that no longer has messages loses its file.
            (catalogs / "uk" / "gone.po").write_text(parts["common"])
            sections.write_language(catalogs / "uk", parts)
            self.assertFalse((catalogs / "uk" / "gone.po").exists())

    def test_merge_accepts_wrapped_lines_and_rejects_conflicts(self):
        owners = {"common.save": "common", "trial.title": "trial_card"}
        text = language_po(MESSAGES[:1] + MESSAGES[3:4])
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


if __name__ == "__main__":
    unittest.main()
