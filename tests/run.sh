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
cp "$fixture/EXCLUDE" "$r/po/EXCLUDE"
cp "$fixture/uk.po" "$r/po/uk.po"
cp "$fixture/compendium-uk.po" "$r/compendium/uk.po"
cp -R "$fixture/sgn/." "$work/sgn/"

# 1. Extraction: the exact messages, contexts, flags and SGN file names.
run pot pot SGN="$work/sgn"
check "make pot succeeds" test "$rc" -eq 0
sed '1,/^$/d' "$r/po/sgn.pot" > "$work/entries.pot"
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

# 5. Check: catalogs and compendium pass; a broken placeholder fails.
run check check
check "make check passes (fuzzy allowed in the compendium)" test "$rc" -eq 0
cp "$mo" "$work/sgn.mo.1"
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

run clean clean
check "make clean removes locale/" test ! -e "$r/locale"

if [ "$failures" -ne 0 ]; then echo "$failures test(s) failed"; exit 1; fi
echo "all tests passed"
