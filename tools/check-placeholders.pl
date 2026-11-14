#!/usr/bin/env perl
# Check the {name} placeholders of translated messages: usage: check-placeholders.pl po/<lang>.po...
#
# msgfmt --check makes sure that no placeholder of a perl-brace-format message is lost. SGN puts
# markup and values into the placeholders after it has escaped the translation, so a translation
# must also not add a name, repeat one, or close a pair before it opens ({end_link} before {link}):
# that would leave a tag open on the page.
use strict;
use warnings;

my $problems = 0;

sub names { return $_[0] =~ /\{(\w+)\}/g }

sub count_of {
    my %count;
    $count{$_}++ for @_;
    return \%count;
}

# Why the placeholders of a translation do not fit those of its message; empty when they fit.
sub problem {
    my ( $original, $translation ) = @_;
    my ( $want, $have ) = ( count_of( names($original) ), count_of( names($translation) ) );
    for my $name ( sort keys %$have ) {
        return "{$name} is not in the message" if !$want->{$name};
        return "{$name} is there $have->{$name} times, the message has it $want->{$name} times" if $have->{$name} != $want->{$name};
    }
    my %open;
    for my $name ( names($translation) ) {
        if ( $name =~ /\Aend_(\w+)\z/ && $want->{$1} ) {
            return "{$name} comes before {$1}" if !$open{$1};
            $open{$1}--;
        }
        else {
            $open{$name}++;
        }
    }
    return q{};
}

sub text_of {    # the text of one PO string that may continue on the next lines
    my ($lines) = @_;
    return join q{}, map { /\A"(.*)"\z/ ? $1 : () } @$lines;
}

for my $file (@ARGV) {
    open( my $po, q{-|}, 'msgattrib', '--no-obsolete', '--translated', '--no-fuzzy', '--no-wrap', $file )
        or die "Cannot run msgattrib on $file: $!\n";
    local $/ = q{};    # one entry at a time
    while ( my $entry = <$po> ) {
        next if $entry !~ /^#,.*\bperl-brace-format\b/m;
        my ( %part, $key );
        for my $line ( split /\n/, $entry ) {
            if    ( $line =~ /\A(msgid|msgid_plural|msgstr(?:\[\d+\])?) (".*")\z/ ) { $key = $1; push @{ $part{$key} }, $2 }
            elsif ( $line =~ /\A"/ && defined $key )                                 { push @{ $part{$key} }, $line }
        }
        my @originals = map { text_of( $part{$_} ) } grep { $part{$_} } qw( msgid msgid_plural );
        for my $form ( grep { /\Amsgstr/ } sort keys %part ) {
            my $translation = text_of( $part{$form} );
            my @why = map { problem( $_, $translation ) } @originals;
            next if grep { $_ eq q{} } @why;    # fits the singular or the plural message
            print STDERR "$file: $why[0]\n    msgid \"$originals[0]\"\n    $form \"$translation\"\n";
            $problems++;
        }
    }
    close $po or die "msgattrib failed on $file\n";
}

exit( $problems ? 1 : 0 );
