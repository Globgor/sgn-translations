package SGN::Fixture;
use strict;
use warnings;
use Locale::TextDomain 'sgn';

sub saved   { __('Saved') }
sub save    { __px( 'button', 'Save {what}', what => $_[0] ) }
sub plots   { __n( 'one plot', 'many plots', $_[0] ) }
sub ignored { 'Not wrapped' }

1;
