#!/usr/bin/perl
# One-time conversion of the keyed machine drafts into a suggestion compendium.
# See compendium/README.md for the full pipeline and its results.
#
# Input: one language, all section files joined by
#   msgcat --no-wrap --no-location po/<lang>/*.po | msgattrib --no-wrap --no-obsolete
# Output (stdout): the same messages without msgctxt, %{name} -> {name},
# ready for msguniq. Report (stderr): counts and every changed or dropped message.
use strict;
use warnings;

my $NAME = qr/[A-Za-z][A-Za-z0-9_]*/;    # placeholder names, as the old catalog check defined them
my ($input) = @ARGV;
die "usage: $0 joined.po > flat.po\n" unless defined $input;
open my $fh, '<:raw', $input or die "$input: $!\n";
local $/ = '';                           # one PO entry per paragraph (--no-wrap output)

sub placeholders { my %seen; $seen{$_}++ for $_[0] =~ /%\{($NAME)\}/g; join ',', sort keys %seen }

my $header = <$fh>;
my (@entries, %forms);
while ( my $block = <$fh> ) {
    my ( %e, $field );
    for my $line ( split /\n/, $block ) {
        if    ( $line =~ /^#, (.*)/ ) { $e{flags} = [ split /, /, $1 ] }
        elsif ( $line =~ /^#/ )       { }    # notes of the old review workflow are dropped
        elsif ( $line =~ /^(msgctxt|msgid|msgid_plural|msgstr(?:\[\d+\])?) (".*")$/ ) {
            $field = $1;
            push @{ $e{fields} }, $field;
            $e{$field} = $2;
        }
        elsif ( $line =~ /^"/ && $field ) { $e{$field} .= "\n$line" }
        else                              { die "$input: cannot parse: $line\n" }
    }
    defined $e{msgctxt} or die "$input: message without a key: $e{msgid}\n";
    my $want = placeholders( $e{msgid} );
    for my $f ( grep { $_ ne 'msgctxt' } @{ $e{fields} } ) {
        my $got = placeholders( $e{$f} );
        warn "PLACEHOLDER MISMATCH $e{msgctxt} $f: {$got} vs msgid {$want}\n" if $got ne $want && $e{$f} ne '""';
        $e{$f} =~ s/%\{($NAME)\}/{$1}/g;
        warn "UNCONVERTED %{ in $e{msgctxt} $f\n" if $e{$f} =~ /%\{/;
    }
    push @{ $e{flags} }, 'perl-brace-format' if length $want;
    $e{iso} = $e{msgctxt} =~ /^"locations\.country\./;
    push @entries, \%e;
    push @{ $forms{ $e{msgid} } }, \%e;
}

# The same English text with and without a plural cannot share one entry.
# Keep the plural entry (it carries all forms) and drop the singular one.
my %drop;
for my $msgid ( sort keys %forms ) {
    my @plural   = grep { defined $_->{msgid_plural} } @{ $forms{$msgid} };
    my @singular = grep { !defined $_->{msgid_plural} } @{ $forms{$msgid} };
    my %plurals  = map { $_->{msgid_plural} => 1 } @plural;
    die "msgid $msgid has different plural texts: @{[ sort keys %plurals ]}\n" if keys %plurals > 1;
    next unless @plural && @singular;
    for my $e (@singular) {
        warn "DROPPED singular $e->{msgctxt} msgid $msgid msgstr $e->{msgstr} (kept plural $plural[0]{msgctxt})\n";
        $drop{$e} = 1;
    }
}

# Header: keep the license notices, replace the notes about the old layout.
my ( @comments, @fields );
for ( split /\n/, $header ) {
    if    (/^#,/) { die "$input: fuzzy header: the section file headers differ\n" }
    elsif (/^# (Only the locations|iso-codes \(LGPL|See docs\/TRANSLATION|SGN interface translations)/) { }
    elsif (/^#/)                                     { push @comments, $_ }
    elsif (/^"(X-SGN-|Project-Id-Version:)/)         { }
    elsif (/^"/)                                     { push @fields, $_ }
}
print <<'TEXT', map( "$_\n", @comments ), qq{msgid ""\nmsgstr ""\n"Project-Id-Version: sgn compendium\\n"\n}, map( "$_\n", @fields ), "\n";
# Machine-draft translations of SGN interface texts: a suggestion compendium.
# "make update" copies a translation from here into po/<lang>.po only when the
# English text matches exactly and this entry is not fuzzy. msgfmt never builds
# this file. Every text is a machine draft; a native speaker must review it.
# A fuzzy entry lists different drafts of one English text; choose one in po/.
# Made once from the keyed drafts; see compendium/README.md.
# Entries marked "iso-codes" are country names adapted from iso-codes v4.20.1
# (LGPL-2.1-or-later): see docs/TRANSLATION_SOURCES.md and LICENSE.iso-codes.
# The other entries are MIT (LICENSE). Notices of the iso-codes catalogs:
TEXT

my %count = ( in => scalar @entries );
for my $e (@entries) {
    next if $drop{$e};
    $count{out}++;
    $count{iso}++ if $e->{iso};
    print "# iso-codes v4.20.1, LGPL-2.1-or-later\n" if $e->{iso};
    print '#, ', join( ', ', @{ $e->{flags} } ), "\n" if @{ $e->{flags} || [] };
    print "$_ $e->{$_}\n" for grep { $_ ne 'msgctxt' } @{ $e->{fields} };
    print "\n";
}
printf STDERR "convert: %d keyed messages in, %d out, %d dropped, %d iso-codes country names\n",
    $count{in}, $count{out}, scalar keys %drop, $count{iso} // 0;
