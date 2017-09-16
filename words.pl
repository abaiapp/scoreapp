#!/usr/bin/perl
use strict;
use warnings;
use DBI;

use Data::Dumper;

# MySQL database configuration
my $dsn = "DBI:mysql:";
my $username = '';
my $password = '';
 
# connect to MySQL database
my %attr = ( PrintError=>0,  # turn off error reporting via warn()
             RaiseError=>1);   # turn on error reporting via die()           
 
my $dbh  = DBI->connect($dsn,$username,$password, \%attr);
 
sub get_sentences {
    my $param = shift;
    my @sentences = ();
    my @sentence = ();
    my $word = $param->{'word'};
    
    my @words = split ' ', $word;
    
    foreach (@words) {
        push @sentence, "$_ ";
        if ($_ =~ /\w+\!$|\.$|\?$/gm) {
            my $current_sentence = join '', @sentence;
            push @sentences, substr $current_sentence, 0, -1;
            @sentence = ();
        }
    }
    return @sentences;
}


sub get_words {
    my @sentence = ();
    open (my $inFile, '<', 'abai.txt') or die $!;
    my $word = "";
    my $words;
    my $current_word = 1;
    while (<$inFile>) {
        chomp;
        if ($_ eq '===') {
            $words->{$current_word++} = $word;
            $word = "";
        } else {
            $word .= "$_ ";
        }
    }
    $words->{$current_word++} = $word;
    return $words;   
}

my $words = get_words();
my $sentences = {};
for (1 .. 45) {
    my @this_word = get_sentences({'word' => $words->{$_} } );
    $sentences->{$_} = \@this_word;
}

my $UPDATE_QUESTION_WORD = 1;
my $UPDATE_WORD = 0;

if ($UPDATE_WORD) {
    my $insert_handle = 
                 $dbh->prepare_cached('INSERT INTO Word VALUES (?,?)'); 
    for my $w (1 .. 45) {
        $insert_handle->execute($w, $words->{$w});
    }
}

if ($UPDATE_QUESTION_WORD) {

    my $sth = $dbh->prepare('SELECT * FROM Question WHERE is_real = 1')
                    or die "Couldn't prepare statement: " . $dbh->errstr;
    $sth->execute() or die "Couldn't execute statement: " . $sth->errstr;

    my $insert_handle = 
                 $dbh->prepare_cached('INSERT INTO QuestionWord VALUES (?,?,?)'); 

    while (my @data = $sth->fetchrow_array()) {
        my ($q_id, $sentence, $is_real) = @data;
        
        my $which_word = 0;

        for my $w (1 .. 45) {
            for my $s (@{$sentences->{$w}}) {
                if ($s eq $sentence) {
                    $which_word = $w;
                    last;
                }
            }
            if ($which_word > 0) {
                last;
            }

#        if ($words->{$w} =~ /$sentence/) {
#            $which_word = $w;
#            last;
#        }

        }   
        if ($which_word > 0) {
            $insert_handle->execute($q_id, $sentence, $which_word);
        }

    }
}
