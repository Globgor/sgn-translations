# SGN interface translations. Needs GNU gettext, make and Perl.
#
#   make                      locale/<lang>/LC_MESSAGES/sgn.mo from po/<lang>.po
#   make check                msgfmt --check on po/*.po and compendium/*.po
#   make pot SGN=/path/to/sgn extract po/sgn.pot from SGN (needs HTML::Mason, libintl-perl)
#   make update               merge po/sgn.pot into every po/<lang>.po
#   make test                 test pot, update and the build on tests/fixture
#   make clean                remove locale/

SGN ?=
LANGUAGES := $(basename $(notdir $(wildcard po/*.po)))
MO := $(LANGUAGES:%=locale/%/LC_MESSAGES/sgn.mo)

.PHONY: all check pot update test clean
.NOTPARALLEL:

all: $(MO)

# SGN runs as another user (www-data): set modes, do not rely on umask.
# A running SGN may hold the old file: write a new file, then rename it.
locale/%/LC_MESSAGES/sgn.mo: po/%.po
	mkdir -p $(@D) && chmod 755 locale locale/$* $(@D)
	tmp=$$(mktemp $(@D)/.sgn.mo.XXXXXX) && \
	{ msgfmt --check --statistics -o "$$tmp" $< && chmod 644 "$$tmp" && mv -f "$$tmp" $@ || { rm -f "$$tmp"; exit 1; }; }

check:
	@status=0; for po in po/*.po compendium/*.po; do \
		msgfmt --check -o /dev/null "$$po" || { echo "$$po: FAILED" >&2; status=1; }; \
	done; exit $$status

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
	options=$$(perl -MLocale::TextDomain -e 'print join " ", Locale::TextDomain->options') && \
	xgettext -L Perl --from-code=UTF-8 --add-location=file --sort-by-file --force-po --package-name=sgn -k $$options \
		-D "$$tmp/perl" -D "$(SGN)" -f "$$tmp/files" -o "$$tmp/sgn.pot" && \
	if test -f po/sgn.pot && diff -q -I '^"POT-Creation-Date:' po/sgn.pot "$$tmp/sgn.pot" >/dev/null; \
	then echo "po/sgn.pot: no change"; \
	else cp "$$tmp/sgn.pot" po/sgn.pot && echo "po/sgn.pot: $$(grep -c '^msgid ' po/sgn.pot) msgid lines (with the header)"; fi

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
