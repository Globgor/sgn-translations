#!/bin/sh
# Install the qualified check/test toolchain on Ubuntu 24.04 (run as root).
# Used by .github/workflows/check.yml and by a local clean-container run.
#   GNU gettext, Python 3, Perl with PPI, Node with npm, git,
#   R 4.5.0 with jsonlite 2.0.0 (the extractors accept only qualified versions).
set -eu
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq --no-install-recommends \
    ca-certificates curl git gettext python3 perl libppi-perl nodejs npm >/dev/null
# R from Posit's versioned Ubuntu build; the exact version is required.
R_VERSION=4.5.0
deb="/tmp/r-${R_VERSION}.deb"
curl -fsSL -o "$deb" "https://cdn.posit.co/r/ubuntu-2404/pkgs/r-${R_VERSION}_1_amd64.deb"
apt-get install -y -qq "$deb" >/dev/null
rm -f "$deb"
ln -sf "/opt/R/${R_VERSION}/bin/R" /usr/local/bin/R
ln -sf "/opt/R/${R_VERSION}/bin/Rscript" /usr/local/bin/Rscript
# jsonlite 2.0.0 from a dated Posit Package Manager snapshot.
Rscript --vanilla -e 'install.packages("https://p3m.dev/cran/2025-06-01/src/contrib/jsonlite_2.0.0.tar.gz", repos = NULL, type = "source", lib = .Library)'
Rscript --vanilla -e 'stopifnot(paste(getRversion(), packageVersion("jsonlite"), sep = "/") == "4.5.0/2.0.0")'
