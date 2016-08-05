import argparse
import logging


def _extract_numerical_value(preceding_phrase, value_indicators, notes):
    """Return a numerical value preceded by the a set of phrases.

    Input:
    preceding_phrase: a phrase or word indicating that the desired numerical
        value will follow. E.g. this might be "EF" for ejection fraction.
    value_indicators: tokens or words following `preceding_phrase` indicating
        that the numerical value will follow. Common examples include
        "is, :, of".
    This can be used, for example, to extract lab values from free-text notes.
    This looks for a string matching `preceding_phrase` followed by one of
    the `value_indicators`, followed by a numerical value. Spaces are assumed
    to be between `preceding_phrase` and the value indicator, as well as
    between the value indicator and the numerical value. For example, if
    `preceding_phrase` is "EF" and `value_indicators` are [:, is], then it
    could extract the numerical value 60 from "EF: 60%" or "EF is 60%".
    If there are multiple pattern matches in the notes, the first match is
    returned.
    TODO(aforsyth): is first match the right behavior?
    """
    pass


def _check_phrase_in_notes(phrase, notes):
    """Return 1 if the notes contain phrase at least once, else 0."""
    pass


def _extract_values_from_rpdr_notes(rpdr_file, extraction_type, phrase,
                                    value_indicators=None):
    pass


def main(input_filename, output_filename, extract_numerical_value, phrase,
         value_indicators):
    print input_filename, output_filename

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_filename', required=True,
                        help=('Path to an RPDR formatted '
                              'text file, e.g. /Users/user1/../file.txt'))
    parser.add_argument('--output_filename', default='output.csv',
                        help=('Path to csv file to output results. Defaults to'
                              ' ./output.csv'))
    parser.add_argument('--extract_numerical_value', action='store_true',
                        default=False, help=('Extracts a numerical value if'
                                             ' specified. Else, checks for '
                                             'presence of the phrase.'))
    parser.add_argument('--phrase', required=True, help=(
        'Either the phrase to check for if not exracting a numerical value, '
        'or the phrase preceding the numerical value if extracting a number.'))
    parser.add_argument('--value_indicators', help=(
        'A string of comma separated tokens or single words expected to come '
        'after the phrase, but before the numerical value (e.g. ":,is,of")'))
    parser.add_argument('--verbosity', '-v', action='count')
    args = parser.parse_args()

    if args.verbosity == 1:
        logging.basicConfig(filename='extraction.log', level=logging.INFO)
    elif args.verbosity > 1:
        logging.basicConfig(filename='extraction.log', level=logging.DEBUG)

    if not args.extract_numerical_value:
        extract_type_string = 'Extracting exact phrase "%s"' % args.phrase
    else:
        extract_type_string = ('Extracting numerical value preceded by "%s" '
                               'and one of "%s"' %
                               (args.phrase, args.value_indicators))
    logging.debug('%s from %s and outputting rows to %s.' %
                  (extract_type_string, args.input_filename,
                   args.output_filename))

    main(args.input_filename, args.output_filename,
         args.extract_numerical_value, args.phrase, args.value_indicators)
