"""make: one gettext .mo per language and browser JSON per section; broken entries stay English."""

import json
import subprocess
import sys
import tempfile
import unittest

# Test names state their contracts.
# pylint: disable=missing-function-docstring
from pathlib import Path

import sections
from test_support import language_po, message

TOOLS = Path(__file__).resolve().parent
MESSAGES = {
    "common": [message("navigation.home", "Home", "mason/site/header.mas:1")],
    "crosses": [message("cross.panel", "Cross", "mason/crosses/panel.mas:1")],
    "trial_card": [
        message("trial.broken", "Saved %{name}.", "a.js:3"),
        message("trial.empty", "Location", "a.js:4"),
        message("trial.fuzzy", "Plot", "a.js:5"),
        message("trial.rows", "%{count} row", "a.js:6", plural="%{count} rows"),
        message("trial.short", "%{count} plot", "a.js:7", plural="%{count} plots"),
    ],
}
LOADED_BY = {"cross.panel": {"crosses", "trial_card"}}
TRANSLATIONS = {
    'msgid "Home"\nmsgstr ""': 'msgid "Home"\nmsgstr "Головна"',
    'msgid "Cross"\nmsgstr ""': 'msgid "Cross"\nmsgstr "Схрещування"',
    'msgid "Saved %{name}."\nmsgstr ""': 'msgid "Saved %{name}."\nmsgstr "Збережено %{title}."',
    'msgctxt "trial.fuzzy"': '#, fuzzy\nmsgctxt "trial.fuzzy"',
    'msgid "Plot"\nmsgstr ""': 'msgid "Plot"\nmsgstr "Ділянка"',
    'msgid_plural "%{count} rows"\nmsgstr[0] ""\nmsgstr[1] ""\nmsgstr[2] ""': (
        'msgid_plural "%{count} rows"\nmsgstr[0] "%{count} рядок"\nmsgstr[1] "%{count} рядки"\nmsgstr[2] "%{count} рядків"'
    ),
    'msgid_plural "%{count} plots"\nmsgstr[0] ""\nmsgstr[1] ""': (
        'msgid_plural "%{count} plots"\nmsgstr[0] "%{count} ділянка"\nmsgstr[1] "%{count} ділянки"'
    ),
}


class BuildTests(unittest.TestCase):
    """Run tools/build.py like make does."""

    def setUp(self):
        # pylint: disable=consider-using-with
        temporary = tempfile.TemporaryDirectory(prefix="sgn-i18n-build-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.catalogs = self.root / "po"
        self.output = self.root / "build"
        everything = [item for part in MESSAGES.values() for item in part]
        loaded_by = {(m["context"], m["source"]): LOADED_BY.get(m["context"], {name}) for name, part in MESSAGES.items() for m in part}
        sections.write_templates(self.catalogs, {name: sections.pot(part, loaded_by) for name, part in MESSAGES.items()})
        owners, names = sections.owners_from_templates(self.catalogs / "templates")
        text = language_po(everything)
        for old, new in TRANSLATIONS.items():
            self.assertIn(old, text)
            text = text.replace(old, new)
        sections.write_language(self.catalogs / "uk", sections.split(text, owners, names))

    def build(self):
        return subprocess.run(
            [sys.executable, "-B", str(TOOLS / "build.py"), "--catalogs", str(self.catalogs), "--output", str(self.output)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_mo_has_usable_translations_and_the_sgn_header(self):
        run = self.build()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn(
            "uk: 3 of 7 messages translated (left out: 1 empty, 1 fuzzy, 2 broken), 3 browser sections", run.stdout
        )
        # Empty and fuzzy are normal work states; only broken entries get a warning.
        self.assertEqual(
            run.stderr.splitlines(),
            [
                "warning: uk: trial.broken: left out, translation does not keep the %{name} values ['name']",
                "warning: uk: trial.short: left out, missing plural forms",
            ],
        )
        mo = self.output / "LocaleData/uk/LC_MESSAGES/sgn.mo"
        text = subprocess.run(["msgunfmt", "--no-wrap", str(mo)], capture_output=True, text=True, check=True).stdout
        self.assertIn('"X-SGN-Language-Name: Українська\\n"', text)
        self.assertIn('"X-SGN-Direction: ltr\\n"', text)
        self.assertEqual(
            sorted(line for line in text.splitlines() if line.startswith("msgctxt")),
            ['msgctxt "cross.panel"', 'msgctxt "navigation.home"', 'msgctxt "trial.rows"'],
        )

    def test_browser_files_follow_the_template_sections(self):
        self.assertEqual(self.build().returncode, 0)
        files = {path.stem: json.loads(path.read_bytes()) for path in (self.output / "js/uk").glob("*.json")}
        self.assertEqual(sorted(files), ["common", "crosses", "trial_card"])
        self.assertEqual(list(files["common"]["messages"]), ["navigation.home\u0004Home"])
        self.assertEqual(list(files["crosses"]["messages"]), ["cross.panel\u0004Cross"])
        self.assertEqual(sorted(files["trial_card"]["messages"]), ["cross.panel\u0004Cross", "trial.rows\u0004%{count} row"])
        trial = files["trial_card"]
        self.assertEqual(
            trial["messages"]["trial.rows\u0004%{count} row"],
            {"plural": "%{count} rows", "forms": ["%{count} рядок", "%{count} рядки", "%{count} рядків"]},
        )
        self.assertEqual(
            {key: trial[key] for key in ("schema", "api", "locale", "direction", "languageName", "nplurals")},
            {"schema": 1, "api": 1, "locale": "uk", "direction": "ltr", "languageName": "Українська", "nplurals": 3},
        )
        self.assertEqual(trial["pluralAst"]["type"], "GROUP")

    def test_bad_language_keeps_the_previous_build(self):
        self.assertEqual(self.build().returncode, 0)
        before = sorted(path.relative_to(self.output) for path in self.output.rglob("*"))
        for path in (self.catalogs / "uk").glob("*.po"):
            path.write_text(path.read_text().replace("X-SGN-Direction: ltr", "X-SGN-Direction: up"))
        run = self.build()
        self.assertEqual(run.returncode, 1)
        self.assertIn("X-SGN-Direction must be ltr or rtl", run.stderr)
        self.assertEqual(sorted(path.relative_to(self.output) for path in self.output.rglob("*")), before)
        self.assertEqual([path.name for path in self.root.iterdir() if path.name.startswith(".build-")], [])


if __name__ == "__main__":
    unittest.main()
