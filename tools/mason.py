#!/usr/bin/env python3
"""Mason preprocessor for GNU xgettext: one Perl view and one JavaScript view.

xgettext knows Perl and JavaScript, not Mason. Each view has the same lines as
the Mason file, so xgettext references keep the real line numbers. Everything
that is not code of the view's language becomes blank.

Perl view: ``%`` lines, <%perl|init|once|shared|args|flags|attr|filter|cleanup>
blocks, ``<% expr %>`` and the arguments of ``<& component, args &>`` (the
component path is blanked: ``/a/b.mas`` would read as a Perl regex).
JavaScript view: <script> elements; Mason code inside them becomes an inert
identifier (``_``), and its Perl goes to the Perl view.
"""

import re
import sys
from pathlib import Path

BLOCKS = r"init|perl|once|shared|args|flags|attr|filter|method|def|doc|text|cleanup"
NAMED = re.compile(r"<%(" + BLOCKS + r")(?:\s[^>]*)?>")
NOT_CODE = ("doc", "text", "method", "def")  # bodies that are not Perl


def is_mason_source(path):
    """.mas files and the reviewed special components under mason/."""
    value = Path(path)
    return value.suffix == ".mas" or (
        len(value.parts) >= 2
        and value.parts[0] == "mason"
        and (value.name in ("autohandler", "dhandler") or value.as_posix() == "mason/tools/bulk/tabs/clone_search.html")
    )


def tag_end(text, start):
    """Find an HTML tag end outside quoted attributes and Mason expressions."""
    quote = None
    i = start
    while i < len(text):
        if text.startswith("<%", i):
            end = text.find("%>", i + 2)
            if end < 0:
                raise ValueError("unterminated Mason expression in tag")
            i = end + 2
            continue
        ch = text[i]
        if quote:
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
        elif ch == ">":
            return i
        i += 1
    return -1


def blank(text):
    """Keep line breaks, blank everything else."""
    return "".join(c if c in "\r\n" else " " for c in text)


class Views:
    """Build both views as character arrays aligned with the Mason text."""

    def __init__(self, text):
        self.text = text
        self.perl = list(blank(text))
        self.js = list(blank(text))

    def code(self, view, start, end, terminator=";"):
        """Copy text[start:end] into a view and end it with a statement terminator."""
        view[start:end] = self.text[start:end]
        if terminator and end < len(view) and view[end] not in "\r\n":
            view[end] = terminator

    def component_arguments(self, start, end):
        """<& path, args &>: keep the arguments as a Perl list, blank the path."""
        source = self.text[start:end]
        header = re.match(r"\s*\|?\s*/?[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\s*(?:,|$)", source)
        self.code(self.perl, start, end)
        if header:
            self.perl[start : start + header.end()] = blank(header[0])
            if header[0].rstrip().endswith(","):
                self.perl[start + header.end() - 1] = "("
                self.perl[end] = ")"
                if end + 1 < len(self.perl) and self.perl[end + 1] not in "\r\n":
                    self.perl[end + 1] = ";"

    def script(self, start, end):
        """Copy one <script> body to the JS view; Mason inside goes to Perl."""
        cursor = start
        self.js[start:end] = self.text[start:end]
        while cursor < end:
            choices = [(self.text.find(m, cursor, end), m) for m in ("<%", "<&")]
            choices = [(s, m) for s, m in choices if s >= 0]
            if not choices:
                break
            first, marker = min(choices)
            named = NAMED.match(self.text, first) if marker == "<%" else None
            if named:
                body = named.end()
                close = self.text.find("</%" + named[1] + ">", body)
                if close < 0:
                    raise ValueError("unterminated Mason " + named[1] + " block")
                stop = close + len(named[1]) + 4
                if named[1] not in NOT_CODE:
                    self.code(self.perl, body, close)
                expression = False
            else:
                ending = "%>" if marker == "<%" else "&>"
                close = self.text.find(ending, first + 2)
                if close < 0:
                    raise ValueError("unterminated Mason expression")
                stop = close + 2
                if marker == "<&":
                    self.component_arguments(first + 2, close)
                else:
                    self.code(self.perl, first + 2, close)
                expression = True
            self.js[first:stop] = blank(self.text[first:stop])
            if expression:
                # An inert identifier keeps the JavaScript statement well formed.
                self.js[first] = "_"
            cursor = stop
        for match in re.finditer(r"(?m)^%[^\r\n]*", self.text[start:end]):
            line_start, line_end = start + match.start(), start + match.end()
            if self.js[line_start] == "%":  # not inside a Mason block or expression
                self.js[line_start:line_end] = blank(match[0])
                self.perl[line_start + 1 : line_end] = self.text[line_start + 1 : line_end]

    def build(self):
        """Walk the Mason text once; return (perl_view, js_view)."""
        text = self.text
        covered = []
        cursor = 0
        while cursor < len(text):
            choices = [(text.find(m, cursor), m) for m in ("<%", "<&", "<script")]
            choices = [(s, m) for s, m in choices if s >= 0]
            if not choices:
                break
            start, marker = min(choices)
            if marker == "<script":
                opening = tag_end(text, start)
                close = text.lower().find("</script", opening)
                if opening < 0 or close < 0:
                    raise ValueError("unterminated script element")
                self.script(opening + 1, close)
                cursor = tag_end(text, close) + 1
            elif marker == "<&":
                close = text.find("&>", start + 2)
                if close < 0:
                    raise ValueError("unterminated Mason component call")
                self.component_arguments(start + 2, close)
                cursor = close + 2
            else:
                named = NAMED.match(text, start)
                if named:
                    body = named.end()
                    close = text.find("</%" + named[1] + ">", body)
                    if close < 0:
                        raise ValueError("unterminated Mason " + named[1] + " block")
                    if named[1] not in NOT_CODE:
                        self.code(self.perl, body, close)
                    cursor = close + len(named[1]) + 4
                    if named[1] in ("method", "def"):
                        # Their bodies are Mason again: continue inside them.
                        cursor = body
                else:
                    close = text.find("%>", start + 2)
                    if close < 0:
                        raise ValueError("unterminated Mason expression")
                    self.code(self.perl, start + 2, close)
                    cursor = close + 2
            covered.append((start, cursor))
        offset = 0
        for line in text.splitlines(keepends=True):
            if line.startswith("%") and not any(a <= offset < b for a, b in covered):
                body = line.rstrip("\r\n")
                self.perl[offset + 1 : offset + len(body)] = body[1:]
            offset += len(line)
        return quote_hash_keys("".join(self.perl)), "".join(self.js)


# xgettext's Perl lexer reads $ARGS{q} as the start of a q{...} string and then
# misses every message after it. Quoting such hash keys keeps lines unchanged.
QUOTE_LIKE_KEY = re.compile(r"(?<!%)\{(\s*)(q|qq|qw|qr|s|m|y|tr)(\s*)\}")


def quote_hash_keys(perl):
    """Turn {q}, {s}, ... into {'q'}, {'s'}, ... in the Perl view."""
    return QUOTE_LIKE_KEY.sub(lambda m: "{" + m[1] + "'" + m[2] + "'" + m[3] + "}", perl)


def views(text):
    """Return (perl_view, js_view) for Mason text."""
    return Views(text).build()


if __name__ == "__main__":
    perl, js = views(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sys.stdout.write(perl if sys.argv[2:] == ["perl"] else js)
