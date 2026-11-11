"""The Mason views keep line numbers and show xgettext only code."""

import unittest

# Test names state their contracts.
# pylint: disable=missing-function-docstring
import mason

SAMPLE = """<%args>
$title => $c->i18n->p('demo.title', 'Demo')
</%args>
% my $label = $c->i18n->p('demo.label', 'Label');
<h1><% $c->i18n->p('demo.heading', 'Heading') |h %></h1>
<& /util/box.mas, title => $c->i18n->p('demo.box', 'Box') &>
<%perl>
my $q = $ARGS{q};
</%perl>
<script>
var a = SGN.t('demo.js', 'Script text');
var b = <% $value %>;
</script>
<%doc> $c->i18n->p('demo.doc', 'Not code') </%doc>
"""


def lines(text):
    return [line.strip() for line in text.split("\n")]


class MasonViewTests(unittest.TestCase):
    """Check each Mason construct in both views."""

    def setUp(self):
        self.perl, self.js = mason.views(SAMPLE)

    def test_views_keep_every_line(self):
        # Same line count keeps xgettext references; quoting {q} adds characters only.
        self.assertEqual(self.perl.count("\n"), SAMPLE.count("\n"))
        self.assertEqual([len(line) for line in self.js.split("\n")], [len(line) for line in SAMPLE.split("\n")])

    def test_perl_view_has_mason_perl_only(self):
        perl = lines(self.perl)
        self.assertEqual(perl[1], "$title => $c->i18n->p('demo.title', 'Demo')")
        self.assertEqual(perl[3], "my $label = $c->i18n->p('demo.label', 'Label');")
        self.assertEqual(perl[4], "$c->i18n->p('demo.heading', 'Heading') |h ;")
        # The component path is blanked; its arguments stay as a Perl list.
        self.assertEqual(perl[5], "( title => $c->i18n->p('demo.box', 'Box') );")
        self.assertEqual(perl[11], "$value ;")
        self.assertNotIn("<h1>", self.perl)
        self.assertNotIn("SGN.t", self.perl)
        self.assertNotIn("demo.doc", self.perl)

    def test_hash_key_q_is_quoted_for_the_perl_lexer(self):
        self.assertEqual(lines(self.perl)[7], "my $q = $ARGS{'q'};")

    def test_javascript_view_has_script_bodies_only(self):
        js = lines(self.js)
        self.assertEqual(js[10], "var a = SGN.t('demo.js', 'Script text');")
        self.assertEqual(js[11], "var b = _           ;")
        self.assertEqual([line for line in js if line], js[10:12])

    def test_unterminated_block_is_an_error(self):
        with self.assertRaisesRegex(ValueError, "unterminated Mason perl block"):
            mason.views("<%perl>\nmy $x = 1;\n")

    def test_special_components_are_mason(self):
        self.assertTrue(mason.is_mason_source("mason/site/autohandler"))
        self.assertTrue(mason.is_mason_source("mason/a/b.mas"))
        self.assertFalse(mason.is_mason_source("lib/autohandler"))
        self.assertFalse(mason.is_mason_source("js/source/a.js"))


if __name__ == "__main__":
    unittest.main()
