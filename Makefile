# SGN interface translations. Server catalogs need GNU gettext and make only.
#
#   make (or make all)        build mo first, then js
#   make mo                   server catalogs only; GNU gettext, no Node.js
#   make js                   browser catalogs only; Node.js 24 and npm ci
#   make check                msgfmt --check on po/*.po and compendium/*.po, placeholders of po/*.po (Perl)
#   make pot SGN=/path/to/sgn extract po/sgn.pot and po/sgn-js.pot from SGN
#   make update               merge po/sgn.pot into every po/<lang>.po
#   make test                 test pot, update and the build on tests/fixture
#   make clean                remove locale/

SGN ?=
LANGUAGES := $(basename $(notdir $(wildcard po/*.po)))
JS := $(LANGUAGES:%=locale/%/sgn.js)
MO := $(LANGUAGES:%=locale/%/LC_MESSAGES/sgn.mo)

.PHONY: all mo js check pot update test clean
.NOTPARALLEL:

all: mo js

mo: $(MO)

# A fresh checkout can build server catalogs before the browser POT is generated.
js:
	@if ! command -v node >/dev/null 2>&1 || ! test -d node_modules/gettext-parser; then \
		echo 'Browser catalogs require Node.js and gettext-parser: run npm ci, or use make mo for server-side translation only' >&2; exit 1; \
	elif ! test -f po/sgn-js.pot; then \
		echo 'Browser catalogs skipped: po/sgn-js.pot is missing; run make pot SGN=/path/to/sgn'; \
	else $(MAKE) --no-print-directory $(JS); fi

# SGN runs as another user (www-data): set modes, do not rely on umask.
# A running SGN may hold the old file: write a new file, then rename it.
locale/%/LC_MESSAGES/sgn.mo: po/%.po
	mkdir -p $(@D) && chmod 755 locale locale/$* $(@D)
	tmp=$$(mktemp $(@D)/.sgn.mo.XXXXXX) && \
	{ msgfmt --check --statistics -o "$$tmp" $< && chmod 644 "$$tmp" && mv -f "$$tmp" $@ || { rm -f "$$tmp"; exit 1; }; }

# Restrict browser data to the JavaScript template; msgfmt drops draft entries.
locale/%/sgn.js: po/%.po po/sgn-js.pot tools/mo2js.js
	mkdir -p $(@D) && chmod 755 locale $(@D)
	@tmp=$$(mktemp -d $(@D)/.sgn.js.XXXXXX) && trap 'rm -rf "$$tmp"' EXIT && set -e && \
	msgfmt --check -o /dev/null $< && \
	msgattrib --no-obsolete -o "$$tmp/current.po" $< && \
	msgmerge --quiet --no-fuzzy-matching -o "$$tmp/browser.po" "$$tmp/current.po" po/sgn-js.pot && \
	msgfmt --check -o "$$tmp/browser.mo" "$$tmp/browser.po" && \
	node tools/mo2js.js "$$tmp/browser.mo" > "$$tmp/sgn.js" && \
	chmod 644 "$$tmp/sgn.js" && mv -f "$$tmp/sgn.js" $@

# msgfmt finds a lost placeholder; the tool finds an added, repeated or misplaced one.
check:
	@status=0; for po in po/*.po compendium/*.po; do \
		msgfmt --check -o /dev/null "$$po" || { echo "$$po: FAILED" >&2; status=1; }; \
	done; \
	perl tools/check-placeholders.pl po/*.po || status=1; exit $$status

# Mason components go through tools/mason2perl.pl; Perl files go to xgettext
# as they are. -D makes xgettext find both but name the SGN paths.
# -k: only the Locale::TextDomain functions mark a message, not every call of
# gettext() or dgettext() in SGN.
pot:
	@test -d "$(SGN)/mason" || { echo 'usage: make pot SGN=/path/to/sgn' >&2; exit 2; }
	@tmp=$$(mktemp -d) && trap 'rm -rf "$$tmp"' EXIT && set -e && \
	perl tools/mason2perl.pl po/EXCLUDE "$(SGN)" "$$tmp/perl" > "$$tmp/files" && \
	(cd "$(SGN)" && find lib cgi-bin -type f \( -name '*.pm' -o -name '*.pl' \)) > "$$tmp/perl-files" && \
	LC_ALL=C sort "$$tmp/perl-files" >> "$$tmp/files" && \
	nogit=$$(xgettext --help | sed -n 's/^ *\(--no-git\).*/\1/p') && \
	options=$$(perl -MLocale::TextDomain -e 'print join " ", Locale::TextDomain->options') && \
	xgettext $$nogit -L Perl --from-code=UTF-8 --add-location=file --sort-by-file --force-po --package-name=sgn -k $$options \
		-D "$$tmp/perl" -D "$(SGN)" -f "$$tmp/files" -o "$$tmp/server.pot" && \
	(cd "$(SGN)" && find js/source -type f -name '*.js') > "$$tmp/js-found" && \
	LC_ALL=C sort "$$tmp/js-found" > "$$tmp/js-sorted" && \
	perl -lane 'BEGIN { open my $$f, "<", "po/EXCLUDE" or die $$!; while (<$$f>) { $$skip{$$1}=1 if /^(\S+)\s+\S/ } } print unless $$skip{$$_}' "$$tmp/js-sorted" > "$$tmp/js-files" && \
	xgettext $$nogit -L JavaScript --from-code=UTF-8 --add-location=file --sort-by-file --force-po --package-name=sgn \
		-k -kgettext -kngettext:1,2 -kpgettext:1c,2 -knpgettext:1c,2,3 \
		-D "$(SGN)" -f "$$tmp/js-files" -o "$$tmp/sgn-js.pot" && \
	msgcat --use-first "$$tmp/server.pot" "$$tmp/sgn-js.pot" -o "$$tmp/sgn.pot" && \
	for pot in sgn sgn-js; do \
		if test -f po/$$pot.pot && diff -q -I '^"POT-Creation-Date:' po/$$pot.pot "$$tmp/$$pot.pot" >/dev/null; \
		then echo "po/$$pot.pot: no change"; \
		else chmod 644 "$$tmp/$$pot.pot" && mv -f "$$tmp/$$pot.pot" po/$$pot.pot; fi; \
	done

# Exact matches only: no fuzzy matching, and fuzzy compendium entries are left out.
# Messages that leave the template stay in po/<lang>.po as obsolete (#~) entries;
# msgfmt ignores them, and msgmerge restores them if the text comes back.
update:
	@test -f po/sgn.pot || { echo 'po/sgn.pot is missing: run make pot SGN=/path/to/sgn' >&2; exit 2; }
	@tmp=$$(mktemp -d) && trap 'rm -rf "$$tmp"' EXIT && set -e && \
	for lang in $(LANGUAGES); do \
		compendium=; \
		if test -f compendium/$$lang.po; then \
			msgattrib --no-fuzzy -o "$$tmp/$$lang.po" compendium/$$lang.po; \
			compendium="-C $$tmp/$$lang.po"; \
		fi; \
		echo "po/$$lang.po:"; \
		msgmerge --update --backup=off --no-fuzzy-matching --quiet $$compendium po/$$lang.po po/sgn.pot; \
		msgfmt --statistics -o /dev/null po/$$lang.po; \
	done

test:
	sh tests/run.sh

clean:
	rm -rf locale
