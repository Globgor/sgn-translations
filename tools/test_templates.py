"""make templates on a small SGN tree: xgettext extraction, sections, msgmerge, the loss guard."""

import json
import subprocess
import sys
import tempfile
import unittest

# Test names state their contracts.
# pylint: disable=missing-function-docstring
from pathlib import Path

import sections
from test_support import language_po

TOOLS = Path(__file__).resolve().parent
SOURCES = {
    "mason/site/header.mas": "<h1><% $c->i18n->p('navigation.home', 'Home') |h %></h1>\n",
    "mason/trial.mas": (
        "<%args>\n$id\n</%args>\n"
        "% my $title = $c->i18n->p('trial.title', 'Trial');\n"
        "<& /util/box.mas, title => $c->i18n->p('trial.box', 'Details') &>\n"
        "<& /crosses/panel.mas &>\n"
        "<script>\nalert(SGN.tn('trial.rows', '%{count} row', '%{count} rows', n));\n</script>\n"
    ),
    "mason/crosses/panel.mas": "% my $p = $c->i18n->p('cross.panel', 'Cross');\n",
    "js/source/legacy/CXGN/Trial.js": "var x = SGN.t('trial.saved', 'Saved %{name}.', {name: n});\n",
    "lib/SGN/Seedlot.pm": (
        "my $t = SGN::I18N::translate($c, 'seedlot.missing', 'No seedlot');\n"
        "my $u = $c->i18n->np('seedlot.count', '%{count} seedlot', '%{count} seedlots', 2);\n"
    ),
    "R/plot.R": "plot(x)\n",
}
WORKFLOWS = {
    "schema": 1,
    "common_sources": ["mason/site/header.mas"],
    "common_context_prefixes": ["navigation."],
    "source_workflows": {
        "mason/site/header.mas": "global",
        "mason/trial.mas": "trial_card",
        "mason/crosses/panel.mas": "crosses",
        "js/source/legacy/CXGN/Trial.js": "trial_card",
        "lib/SGN/Seedlot.pm": "seedlots",
        "R/plot.R": "analysis",
    },
}


class TemplatesTests(unittest.TestCase):
    """Run tools/templates.py like make templates does."""

    def setUp(self):
        # pylint: disable=consider-using-with
        temporary = tempfile.TemporaryDirectory(prefix="sgn-i18n-templates-test-")
        self.addCleanup(temporary.cleanup)
        self.sgn = Path(temporary.name) / "sgn"
        for path, text in SOURCES.items():
            (self.sgn / path).parent.mkdir(parents=True, exist_ok=True)
            (self.sgn / path).write_text(text, encoding="utf-8")
        (self.sgn / "locale").mkdir()
        (self.sgn / "locale/sources.txt").write_text("# registered\n" + "\n".join(SOURCES) + "\n")
        (self.sgn / "locale/workflows.json").write_text(json.dumps(WORKFLOWS))
        self.catalogs = Path(temporary.name) / "po"
        (self.catalogs / "uk").mkdir(parents=True)
        (self.catalogs / "uk/common.po").write_text(language_po([]), encoding="utf-8")

    def run_templates(self, *extra):
        return subprocess.run(
            [sys.executable, "-B", str(TOOLS / "templates.py"), "--sgn", str(self.sgn), "--catalogs", str(self.catalogs)]
            + list(extra),
            capture_output=True,
            text=True,
            check=False,
        )

    def read(self, path):
        return (self.catalogs / path).read_text(encoding="utf-8")

    def test_extracts_every_language_and_assigns_sections(self):
        run = self.run_templates()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("1 R files", run.stderr)
        owners, names = sections.owners_from_templates(self.catalogs / "templates")
        self.assertEqual(names, ["common", "crosses", "seedlots", "trial_card"])
        self.assertEqual(
            owners,
            {
                "cross.panel": "crosses",
                "navigation.home": "common",
                "seedlot.count": "seedlots",
                "seedlot.missing": "seedlots",
                "trial.box": "trial_card",
                "trial.rows": "trial_card",
                "trial.saved": "trial_card",
                "trial.title": "trial_card",
            },
        )
        trial = self.read("templates/trial_card.pot")
        self.assertIn("#. sections: trial_card\n#: mason/trial.mas:5\nmsgctxt \"trial.box\"", trial)
        self.assertIn('#: mason/trial.mas:8\nmsgctxt "trial.rows"\nmsgid "%{count} row"\nmsgid_plural "%{count} rows"', trial)
        self.assertIn('#: lib/SGN/Seedlot.pm:1\nmsgctxt "seedlot.missing"', self.read("templates/seedlots.pot"))
        self.assertIn("#. sections: common\n", self.read("templates/common.pot"))
        # The cross panel is a component of the trial page: both sections load it.
        self.assertIn('#. sections: crosses trial_card\n#: mason/crosses/panel.mas:1\nmsgctxt "cross.panel"', self.read("templates/crosses.pot"))
        self.assertEqual(sorted(p.name for p in (self.catalogs / "uk").glob("*.po")), sorted(n + ".po" for n in names))
        uk = self.read("uk/seedlots.po")
        self.assertIn('msgid_plural "%{count} seedlots"\nmsgstr[0] ""\nmsgstr[1] ""\nmsgstr[2] ""', uk)
        self.assertIn('"X-SGN-Direction: ltr\\n"', uk)

    def test_lost_translation_stops_unless_allowed(self):
        self.assertEqual(self.run_templates().returncode, 0)
        for name, english, text in (
            ("seedlots", "No seedlot", "Немає партії"),
            ("trial_card", "Saved %{name}.", "Збережено %{name}."),
        ):
            path = self.catalogs / "uk" / (name + ".po")
            path.write_text(path.read_text().replace(f'msgid "{english}"\nmsgstr ""', f'msgid "{english}"\nmsgstr "{text}"'))
        # One English text changes, one message is removed from SGN.
        source = self.sgn / "lib/SGN/Seedlot.pm"
        source.write_text(source.read_text().replace("'No seedlot'", "'No seedlot found'"))
        (self.sgn / "js/source/legacy/CXGN/Trial.js").write_text("var x = 1;\n")
        before = {p: p.read_bytes() for p in self.catalogs.rglob("*.po*")}
        run = self.run_templates()
        self.assertEqual(run.returncode, 1)
        self.assertIn("uk: 2 filled translations lose their message, e.g. seedlot.missing, trial.saved", run.stderr)
        self.assertEqual({p: p.read_bytes() for p in self.catalogs.rglob("*.po*")}, before)
        run = self.run_templates("--allow-obsolete")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("uk: 2 translations became obsolete (#~) or fuzzy", run.stdout)
        # msgmerge: the changed text gets the old translation as a fuzzy guess;
        # the removed message stays as an obsolete entry at the end of common.po.
        self.assertIn('#, fuzzy\nmsgctxt "seedlot.missing"\nmsgid "No seedlot found"\nmsgstr "Немає партії"', self.read("uk/seedlots.po"))
        self.assertIn('#~ msgctxt "trial.saved"\n#~ msgid "Saved %{name}."\n#~ msgstr "Збережено %{name}."', self.read("uk/common.po"))
        # When the message comes back, msgmerge restores the obsolete translation unchanged.
        (self.sgn / "js/source/legacy/CXGN/Trial.js").write_text(SOURCES["js/source/legacy/CXGN/Trial.js"])
        self.assertEqual(self.run_templates().returncode, 0)
        self.assertIn('msgctxt "trial.saved"\nmsgid "Saved %{name}."\nmsgstr "Збережено %{name}."', self.read("uk/trial_card.po"))

    def test_unregistered_file_type_is_an_error(self):
        (self.sgn / "locale/sources.txt").write_text("docs/readme.txt\n")
        run = self.run_templates()
        self.assertEqual(run.returncode, 1)
        self.assertIn("unsupported source file type: docs/readme.txt", run.stderr)


if __name__ == "__main__":
    unittest.main()
