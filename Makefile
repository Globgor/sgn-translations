# SGN translations. Needs GNU gettext, Python 3 and make; nothing else.
#
#   make                            build/ for SGN: .mo files and browser JSON
#   make check                      catalog checks, msgfmt --check, tool tests
#   make templates SGN=/path/to/sgn regenerate po/templates, msgmerge every language
#   make clean                      remove build/
#
# make check SGN=/path/to/sgn also runs the manual tests that read SGN files.
# make templates ... ALLOW_OBSOLETE=1 accepts translations that lose their message.

PYTHON ?= python3
SGN ?=
ALLOW_OBSOLETE ?=
LANGUAGES := $(filter-out templates,$(notdir $(patsubst %/,%,$(wildcard po/*/))))

.PHONY: all build check templates clean

all: build

build:
	$(PYTHON) -B tools/build.py

# Every step runs; make check fails at the end if any step failed.
check:
	@status=0; \
	$(PYTHON) -B tools/check_catalogs.py || status=1; \
	for lang in $(LANGUAGES); do \
		echo "msgfmt --check $$lang:"; \
		msgcat --use-first po/$$lang/*.po | msgfmt --check --statistics -o /dev/null - || status=1; \
	done; \
	(cd tools && SGN_CHECKOUT="$(SGN)" $(PYTHON) -B -m unittest discover -s . -p 'test_*.py') || status=1; \
	exit $$status

templates:
	@test -n "$(SGN)" || { echo "usage: make templates SGN=/path/to/sgn" >&2; exit 2; }
	$(PYTHON) -B tools/templates.py --sgn "$(SGN)" $(if $(ALLOW_OBSOLETE),--allow-obsolete)

clean:
	rm -rf build
