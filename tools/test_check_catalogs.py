"""Each catalog structure rule reports a broken fixture and accepts a good one."""

import subprocess
import sys
import tempfile
import unittest

# Test names state their contracts.
# pylint: disable=missing-function-docstring
from pathlib import Path

import sections
from check_catalogs import LANGUAGES
from test_support import language_po, message

TOOLS = Path(__file__).resolve().parent
MESSAGES = [
    message("trial.created", "Created trial %{name}.", "a.js:1"),
    message("trial.count", "%{count} trial", "a.js:2", plural="%{count} trials"),
    message("trial.empty", "Location", "a.js:3"),
]


class CheckTests(unittest.TestCase):
    """Run the real command on small catalogs."""

    def setUp(self):
        # pylint: disable=consider-using-with
        temporary = tempfile.TemporaryDirectory(prefix="sgn-i18n-check-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.catalogs = self.root / "po"
        self.glossary = self.root / "glossary"
        self.glossary.mkdir()
        sections.write_templates(self.catalogs, {"common": sections.pot(MESSAGES)})
        text = language_po(MESSAGES, plural_forms=LANGUAGES["uk"]["plural"])
        text = text.replace('msgid "Created trial %{name}."\nmsgstr ""', 'msgid "Created trial %{name}."\nmsgstr "Створено дослід %{name}."')
        text = text.replace(
            'msgstr[0] ""\nmsgstr[1] ""\nmsgstr[2] ""',
            'msgstr[0] "%{count} дослід"\nmsgstr[1] "%{count} досліди"\nmsgstr[2] "%{count} дослідів"',
        )
        self.good = text
        (self.catalogs / "uk").mkdir()

    def check(self, text, ok, expected=None, glossary=""):
        (self.catalogs / "uk/common.po").write_text(text, encoding="utf-8")
        (self.glossary / "uk.tsv").write_text(glossary, encoding="utf-8")
        run = subprocess.run(
            [
                sys.executable,
                "-B",
                str(TOOLS / "check_catalogs.py"),
                "--catalogs",
                str(self.catalogs),
                "--glossary",
                str(self.glossary),
                "--count",
                "місц",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(run.returncode == 0, ok, run.stdout + run.stderr)
        if expected:
            self.assertIn(expected, run.stdout)
        return run.stdout

    def test_good_catalog_passes_and_empty_translation_is_allowed(self):
        output = self.check(self.good, True)
        self.assertIn("'empty': 1", output)
        self.assertIn("problems: 0", output)

    def test_missing_and_extra_messages(self):
        record = '\n\n#: a.js:3\nmsgctxt "trial.empty"\nmsgid "Location"\nmsgstr ""\n'
        self.assertTrue(self.good.endswith(record))
        self.check(self.good[: -len(record)] + "\n", False, "missing message trial.empty")
        extra = self.good + '\nmsgctxt "trial.extra"\nmsgid "Extra"\nmsgstr ""\n'
        self.check(extra, False, "message not in template trial.extra")

    def test_missing_section_file(self):
        sections.write_templates(self.catalogs, {"common": sections.pot(MESSAGES), "seedlots": sections.pot([])})
        self.check(self.good, False, "missing section file seedlots.po")

    def test_placeholder_must_be_kept(self):
        text = self.good.replace("Створено дослід %{name}.", "Створено дослід %{title}.")
        self.check(text, False, "translation must keep %{name} values ['name']")

    def test_fuzzy_needs_work_is_not_checked_for_values(self):
        text = self.good.replace("Створено дослід %{name}.", "Створено дослід").replace(
            'msgctxt "trial.created"', '#, fuzzy\nmsgctxt "trial.created"'
        )
        self.check(text, True)

    def test_plural_forms_and_header_rule(self):
        text = self.good.replace('\nmsgstr[2] "%{count} дослідів"', "")
        self.check(text, False, "plural message has 2 msgstr forms, expected 3")
        text = self.good.replace('msgstr[2] "%{count} дослідів"', 'msgstr[2] ""')
        self.check(text, False, "every msgstr form must be filled")
        text = self.good.replace("Створено дослід %{name}.", " ")
        self.check(text, False, "every msgstr form must be filled")
        text = self.good.replace(LANGUAGES["uk"]["plural"], "nplurals=2; plural=(n != 1);")
        self.check(text, False, "Plural-Forms differs from the standard rule")

    def test_msgfmt_must_accept_the_file(self):
        text = self.good.replace('msgctxt "trial.empty"', '#, c-format\nmsgctxt "trial.empty"').replace(
            'msgid "Location"\nmsgstr ""', 'msgid "Location %d"\nmsgstr "Місце"'
        )
        sections.write_templates(
            self.catalogs, {"common": sections.pot(MESSAGES).replace('msgid "Location"', 'msgid "Location %d"')}
        )
        self.check(text, False, "msgfmt --check failed")

    def test_stray_script(self):
        text = self.good.replace("Створено дослід %{name}.", "تم إنشاء %{name}.")
        self.check(text, False, "Arabic letters in a uk translation")

    def test_glossary_rule_and_term_count(self):
        text = self.good.replace('msgid "Location"\nmsgstr ""', 'msgid "Location"\nmsgstr "Локація"')
        rules = "# forbidden<TAB>preferred\nлокаці\tмісце\n"
        self.check(text, False, "glossary: use «місце» instead of «локаці»", glossary=rules)
        text = self.good.replace('msgid "Location"\nmsgstr ""', 'msgid "Location"\nmsgstr "Місце"')
        self.assertIn("'count': {'місц': 1}", self.check(text, True, glossary=rules))


if __name__ == "__main__":
    unittest.main()
