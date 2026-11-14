#!/bin/sh
# Tests for "make pot", "make update", "make" and "make check" on tests/fixture.
# Needs GNU gettext, make, and Perl with HTML::Mason and Locale::TextDomain.
# Works on a copy in a temporary folder; this repository is not changed.
set -eu

repo=$(cd "$(dirname "$0")/.." && pwd)
fixture=$repo/tests/fixture
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
failures=0

ok()   { echo "ok   $1"; }
fail() { echo "FAIL $1"; failures=$((failures + 1)); }
check() { name=$1; shift; if "$@"; then ok "$name"; else fail "$name"; fi; }
# run NAME make-args...: run make in the copy, keep stdout+stderr in $work/NAME.log
run() { log=$work/$1.log; shift; if make -s -C "$r" "$@" > "$log" 2>&1; then rc=0; else rc=$?; fi; }
logged() { grep -q -- "$1" "$log" || { echo "     not in output: $1"; sed 's/^/     | /' "$log"; return 1; }; }
same() { diff -u "$1" "$2" || return 1; }
messages() { sed '1,/^$/d' "$1" | grep -E '^(#,|msgctxt|msgid|msgid_plural) '; }

r=$work/repo
mkdir -p "$r/po" "$r/compendium" "$work/sgn"
cp "$repo/Makefile" "$r/"
cp -R "$repo/tools" "$r/"
ln -s "$repo/node_modules" "$r/node_modules"
cp "$fixture/EXCLUDE" "$r/po/EXCLUDE"
cp "$fixture/uk.po" "$r/po/uk.po"
cp "$fixture/compendium-uk.po" "$r/compendium/uk.po"
cp -R "$fixture/sgn/." "$work/sgn/"

# Server-only builds work when PATH contains no Node.js executable.
mkdir "$work/no-node"
for tool in make msgfmt mkdir chmod mktemp mv rm; do
    ln -s "$(command -v "$tool")" "$work/no-node/$tool"
done
log=$work/mo-only.log
if PATH="$work/no-node" make -s -C "$r" mo > "$log" 2>&1; then rc=0; else rc=$?; fi
check "make mo works without Node.js" test "$rc" -eq 0
check "make mo builds a server catalog" test -f "$r/locale/uk/LC_MESSAGES/sgn.mo"
check "make mo builds no browser catalog" test ! -f "$r/locale/uk/sgn.js"
run fresh js
check "fresh checkout without browser POT remains usable" test "$rc" -eq 0
check "missing browser POT prints one notice" test "$(wc -l < "$log")" -eq 1
check "missing browser POT explains generation" logged 'Browser catalogs skipped: po/sgn-js.pot is missing'
check "missing browser POT builds no browser catalog" test ! -f "$r/locale/uk/sgn.js"
run freshall
check "make works without a generated browser POT" test "$rc" -eq 0
check "make without browser POT builds only MO" test -f "$r/locale/uk/LC_MESSAGES/sgn.mo" -a ! -f "$r/locale/uk/sgn.js"

# 1. Extraction: the exact messages, contexts, flags and SGN file names.
run pot pot SGN="$work/sgn"
check "make pot succeeds" test "$rc" -eq 0
sed '1,/^$/d' "$r/po/sgn.pot" > "$work/entries.pot"
check "JavaScript template has all four keywords" test "$(grep -c '^msgid ' "$r/po/sgn-js.pot")" -eq 5
check "npgettext has plural and context" grep -q '^msgctxt "row"$' "$r/po/sgn-js.pot"
check "JavaScript is also in the shared template" grep -q '^msgid "Browser row"$' "$r/po/sgn.pot"
check "only explicit keywords and nonexcluded files are extracted" sh -c "! grep -q -e 'Not a translation' -e 'Excluded browser text' '$r/po/sgn-js.pot'"
check "make pot extracts exactly tests/expected.pot" same "$repo/tests/expected.pot" "$work/entries.pot"
check "make pot reports a listed component that compiles" logged 'mason/still_listed.mas compiles and is UTF-8 now'

sed 's/^"POT-Creation-Date: .*/"POT-Creation-Date: 2000-01-01 00:00+0000\\n"/' "$r/po/sgn.pot" > "$work/sgn.pot.1"
cp "$work/sgn.pot.1" "$r/po/sgn.pot"
run pot2 pot SGN="$work/sgn"
check "make pot again: no change, file kept" logged 'po/sgn.pot: no change'
check "make pot again: old POT-Creation-Date kept (no churn)" cmp -s "$work/sgn.pot.1" "$r/po/sgn.pot"

# 2. Extraction errors stop it and keep po/sgn.pot.
cp "$fixture/broken.mas" "$work/sgn/mason/site/broken.mas"
run broken pot SGN="$work/sgn"
check "a component that does not compile fails make pot" test "$rc" -ne 0
check "the error names the component" logged 'mason/site/broken.mas: Found component with content ending tag'
check "po/sgn.pot is kept after the error" cmp -s "$work/sgn.pot.1" "$r/po/sgn.pot"
rm "$work/sgn/mason/site/broken.mas"

grep -v legacy_latin1 "$fixture/EXCLUDE" > "$r/po/EXCLUDE"
run latin1 pot SGN="$work/sgn"
check "a component that is not UTF-8 fails make pot" test "$rc" -ne 0
check "the error names the file and line" logged 'mason/legacy_latin1.mas: line 1 is not UTF-8'
cp "$fixture/EXCLUDE" "$r/po/EXCLUDE"

mkdir -p "$work/nolib/Locale"
echo 'die "Locale::TextDomain is not installed\n";' > "$work/nolib/Locale/TextDomain.pm"
log=$work/nolib.log
if PERL5LIB="$work/nolib:${PERL5LIB:-}" make -s -C "$r" pot SGN="$work/sgn" > "$log" 2>&1; then rc=0; else rc=$?; fi
check "make pot fails without Locale::TextDomain" test "$rc" -ne 0
check "the error names the module" logged 'Locale::TextDomain'
check "po/sgn.pot is kept without the module" cmp -s "$work/sgn.pot.1" "$r/po/sgn.pot"

# English ids cannot switch between singular and plural across languages.
cp "$r/po/sgn-js.pot" "$work/js.pot.1"
printf "gettext('one plot');\n" > "$work/sgn/js/source/collision.js"
run collision pot SGN="$work/sgn"
check "mixed Perl plural and JavaScript singular stops extraction" test "$rc" -ne 0
check "mixed plural usage is explained" logged 'is used without plural and with plural'
check "shared POT survives a plural collision" cmp -s "$work/sgn.pot.1" "$r/po/sgn.pot"
check "browser POT survives a plural collision" cmp -s "$work/js.pot.1" "$r/po/sgn-js.pot"
rm "$work/sgn/js/source/collision.js"

# 3. Update: only exact, non-fuzzy compendium matches are copied.
run update update
check "make update succeeds" test "$rc" -eq 0
msgattrib --translated --no-obsolete "$r/po/uk.po" > "$work/translated.po"
messages "$work/translated.po" > "$work/translated"
cat > "$work/translated.expected" <<'EOF'
msgid "Search"
#, perl-brace-format
msgid "Trial {name}"
#, perl-brace-format
msgid "{count} trial"
msgid_plural "{count} trials"
EOF
check "make update fills exactly the exact matches" same "$work/translated.expected" "$work/translated"
check "the fuzzy compendium entry is not used" sh -c "! grep -q -e 'fuzzy' -e 'Назва файлу' '$r/po/uk.po'"
msgattrib --untranslated "$r/po/uk.po" > "$work/untranslated.po"
check "a near match (Search trial / Search trials) is not used" grep -q '^msgid "Search trial"$' "$work/untranslated.po"
check "a message with context gets no contextless translation" grep -q '^msgctxt "verb"$' "$work/untranslated.po"

# 4. Build: modes for another user, replacement by rename.
mo=$r/locale/uk/LC_MESSAGES/sgn.mo
if (umask 077 && make -s -C "$r" > "$work/build.log" 2>&1); then rc=0; else rc=$?; fi
check "make builds the catalog" test "$rc" -eq 0 -a -f "$mo"
check "catalog modes do not depend on umask (755 dirs, 644 file)" \
    test "$(stat -c %a "$r/locale" "$r/locale/uk" "$r/locale/uk/LC_MESSAGES" "$mo" | tr '\n' ' ')" = "755 755 755 644 "
check "the catalog holds the translation" sh -c "msgunfmt '$mo' | grep -q 'Пошук'"
inode=$(stat -c %i "$mo")
touch -d "@$(($(stat -c %Y "$mo") - 10))" "$mo"
run rebuild
check "a rebuild replaces the file by rename (new inode)" test "$(stat -c %i "$mo")" != "$inode"
check "no temporary file is left" test -z "$(find "$r/locale" -name '.sgn.mo.*')"

# Browser prerequisites are checked once, even when catalogs are up to date.
cp "$mo" "$work/mo-before-missing-node"
cp "$r/locale/uk/sgn.js" "$work/js-before-missing-node"
fix='run npm ci, or use make mo for server-side translation only'
log=$work/no-node.log
if PATH="$work/no-node" make -s -C "$r" js > "$log" 2>&1; then rc=0; else rc=$?; fi
check "make js without Node.js fails clearly" test "$rc" -ne 0
check "missing Node.js gives exactly one fix line" test "$(grep -c "$fix" "$log")" -eq 1
check "missing Node.js preserves server catalog" cmp -s "$work/mo-before-missing-node" "$mo"
check "missing Node.js preserves browser catalog" cmp -s "$work/js-before-missing-node" "$r/locale/uk/sgn.js"
mv "$r/node_modules" "$r/node_modules.saved"
run noparser js
check "make js without gettext-parser fails clearly" test "$rc" -ne 0
check "missing parser gives exactly one fix line" test "$(grep -c "$fix" "$log")" -eq 1
check "missing parser preserves browser catalog" cmp -s "$work/js-before-missing-node" "$r/locale/uk/sgn.js"
mv "$r/node_modules.saved" "$r/node_modules"
# The default target must complete server compilation before checking Node.js.
rm "$mo"
log=$work/all-no-node.log
if PATH="$work/no-node" make -s -C "$r" > "$log" 2>&1; then rc=0; else rc=$?; fi
check "make reports the missing browser prerequisite" test "$rc" -ne 0
check "make builds MO before reporting missing Node.js" test -f "$mo"
check "default target gives exactly one fix line" test "$(grep -c "$fix" "$log")" -eq 1

mv "$r/po/sgn-js.pot" "$work/browser-template.saved"
run missingtemplate js
check "missing browser POT preserves installed JS" cmp -s "$work/js-before-missing-node" "$r/locale/uk/sgn.js"
check "missing browser POT remains nonfatal after a build" test "$rc" -eq 0
mv "$work/browser-template.saved" "$r/po/sgn-js.pot"

# 5. Check: catalogs and compendium pass; a broken placeholder fails.
run check check
check "make check passes (fuzzy allowed in the compendium)" test "$rc" -eq 0
cp "$mo" "$work/sgn.mo.1"
# msgfmt accepts these three; a translation must not add, repeat or misplace a placeholder.
cp "$r/po/uk.po" "$work/uk.po.good"
badplaceholder() {   # badplaceholder NAME MSGID MSGSTR EXPECTED-REASON
    cp "$work/uk.po.good" "$r/po/uk.po"
    printf '\n#, perl-brace-format\nmsgid "%s"\nmsgstr "%s"\n' "$2" "$3" >> "$r/po/uk.po"
    run "$1" check
    check "make check fails on $1" test "$rc" -ne 0
    check "make check explains $1" logged "$4"
}
badplaceholder "an added placeholder" 'Read the {link}help{end_link}' 'Читайте {link}довідку{end_link} {text}' '{text} is not in the message'
badplaceholder "a repeated placeholder" 'Found {count} trials' 'Знайдено {count} {count} дослідів' '{count} is there 2 times'
badplaceholder "a pair that closes before it opens" 'Read the {link}help{end_link}' 'Читайте {end_link}довідку{link}' '{end_link} comes before {link}'
cp "$work/uk.po.good" "$r/po/uk.po"
printf '\n#, perl-brace-format\nmsgid "Read the {link}help{end_link} for {name}"\nmsgstr "{name}: читайте {link}довідку{end_link}"\n' >> "$r/po/uk.po"
run movedplaceholder check
check "make check accepts placeholders in another order" test "$rc" -eq 0
cp "$work/uk.po.good" "$r/po/uk.po"
cat >> "$r/po/uk.po" <<'EOF'

#, perl-brace-format
msgid "Broken {name}"
msgstr "Зламано {nmae}"
EOF
run badcheck check
check "make check fails on a wrong placeholder" test "$rc" -ne 0
run badbuild
check "make fails on it too" test "$rc" -ne 0
check "the old catalog stays in place" cmp -s "$work/sgn.mo.1" "$mo"
check "no temporary file is left after the error" test -z "$(find "$r/locale" -name '.sgn.mo.*')"

# 6. Browser build: exact selection, drafts, context, plurals and safe replacement.
cp "$fixture/browser.po" "$r/po/uk.po"
cat >> "$r/po/sgn-js.pot" <<'EOF'

msgid "Draft"
msgstr ""

msgid "Empty"
msgstr ""

msgid "Obsolete"
msgstr ""
EOF
js=$r/locale/uk/sgn.js
run browser locale/uk/sgn.js
check "browser build succeeds" test "$rc" -eq 0
if [ "$rc" -ne 0 ]; then cat "$log"; fi
check "browser data exactly matches the expected catalog" same "$repo/tests/expected-sgn.js" "$js"
check "browser file is readable by another user" test "$(stat -c %a "$js")" = 644
inode=$(stat -c %i "$js")
touch -d "@$(($(stat -c %Y "$js") - 10))" "$js"
run browseragain locale/uk/sgn.js
check "browser rebuild replaces by rename" test "$(stat -c %i "$js")" != "$inode"
cp "$js" "$work/sgn.js.1"
sed '/^"Plural-Forms:/d' "$fixture/browser.po" > "$r/po/uk.po"
run noheader locale/uk/sgn.js
check "browser build refuses a catalog without Plural-Forms" test "$rc" -ne 0
check "missing plural header is reported" logged 'Plural-Forms'
check "old browser catalog survives a missing header" cmp -s "$work/sgn.js.1" "$js"
printf 'msgid "broken\n' > "$r/po/uk.po"
run brokenbrowser locale/uk/sgn.js
check "browser build refuses broken PO input" test "$rc" -ne 0
check "old browser catalog survives broken input" cmp -s "$work/sgn.js.1" "$js"
check "browser temporary files are removed after failure" test -z "$(find "$r/locale" -name '.sgn.js.*')"

# A singular-only MO reaches the converter even without a plural header.
printf 'msgid ""\nmsgstr "Content-Type: text/plain; charset=UTF-8\\n"\n\nmsgid "Text"\nmsgstr "Текст"\n' > "$work/noheader.po"
msgfmt -o "$work/noheader.mo" "$work/noheader.po"
log=$work/converter.log
if node "$r/tools/mo2js.js" "$work/noheader.mo" > "$log" 2>&1; then rc=0; else rc=$?; fi
check "converter itself refuses a missing plural header" test "$rc" -ne 0
check "converter names the missing header" logged 'no Plural-Forms header'

run clean clean
check "make clean removes locale/" test ! -e "$r/locale"

if [ "$failures" -ne 0 ]; then echo "$failures test(s) failed"; exit 1; fi
echo "all tests passed"
