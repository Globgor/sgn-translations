#!/usr/bin/perl
# Compile SGN's Mason components to Perl with HTML::Mason's own compiler, so
# that "xgettext -L Perl" finds the __() calls in them.
#
# Usage: mason2perl.pl EXCLUDE SGN OUT
#   EXCLUDE  components to skip, one "path reason" per line; # starts a comment
#   SGN      SGN checkout; reads SGN/mason/**/*.mas, autohandler, dhandler
#   OUT      new or empty directory; gets OUT/mason/... as Perl
# Prints the compiled paths (relative to SGN, sorted), one per line.
# A component that does not compile or is not UTF-8 is an error (exit 1),
# unless EXCLUDE lists it. A listed component that passes is reported.
use strict;
use warnings;
use Encode qw(decode FB_CROAK LEAVE_SRC);
use File::Basename qw(dirname);
use File::Find qw(find);
use File::Path qw(make_path);
use HTML::Mason::Compiler::ToObject;

@ARGV == 3 or die "usage: $0 EXCLUDE SGN OUT\n";
my ( $exclude_file, $sgn, $out ) = @ARGV;
$sgn =~ s{(?<=.)/+$}{};

my %exclude;
open my $list, '<', $exclude_file or die "$exclude_file: $!\n";
while (<$list>) {
    next if /^\s*(?:#|$)/;
    my ($path) = /^(\S+)\s+\S/ or die "$exclude_file:$.: write 'path reason'\n";
    $exclude{$path} = 1 if $path =~ m{\Amason/};
}

-d "$sgn/mason" or die "$sgn/mason: not a directory\n";
mkdir $out or die "$out: $!\n" unless -e $out;
opendir my $dir, $out or die "$out: $!\n";
die "$out: not empty\n" if grep { !/^\.\.?$/ } readdir $dir;

my @components;
find( { no_chdir => 1, wanted => sub {
    push @components, substr( $_, length($sgn) + 1 ) if -f && m{(?:\.mas|/autohandler|/dhandler)$};
} }, "$sgn/mason" );

my $compiler = HTML::Mason::Compiler::ToObject->new;
sub compile {    # returns (error) or (undef, perl code)
    my ($path) = @_;
    open my $in, '<:raw', "$sgn/$path" or return "cannot read: $!";
    my $source = do { local $/; <$in> };
    my $line = 0;
    for ( split /\n/, $source ) {
        $line++;
        eval { decode( 'UTF-8', $_, FB_CROAK | LEAVE_SRC ); 1 } or return "line $line is not UTF-8";
    }
    my $perl = eval { $compiler->compile( comp_source => $source, name => $path, comp_path => "/$path" ) };
    return ( split /\n/, "$@" )[0] unless defined $perl;
    return ( undef, ref $perl ? $$perl : $perl );
}

my ( @done, %seen, $failed );
for my $path ( sort @components ) {
    $seen{$path} = 1;
    my ( $error, $perl ) = compile($path);
    if ( $exclude{$path} ) {
        warn "$exclude_file: $path compiles and is UTF-8 now; remove it from the list\n" unless $error;
        next;
    }
    if ($error) { warn "$path: $error\n"; $failed++; next }
    make_path( dirname("$out/$path") );
    open my $fh, '>:raw', "$out/$path" or die "$out/$path: $!\n";
    print $fh $perl;
    close $fh or die "$out/$path: $!\n";
    push @done, $path;
}
warn "$exclude_file: $_ is not an SGN component; remove it from the list\n" for grep { !$seen{$_} } sort keys %exclude;
if ($failed) {
    warn "mason2perl: $failed component(s) failed; fix them in SGN or list them in $exclude_file with a reason\n";
    exit 1;
}
print "$_\n" for @done;
