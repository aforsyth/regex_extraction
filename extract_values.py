import argparse
import csv
import logging
import re


def _extract_numerical_value(preceding_phrase, notes):
    """Return a numerical value preceded by the a set of phrases.

    Return (numerical_value (as a float), match_start, match_end)

    Input:
    preceding_phrase: a phrase or word indicating that the desired numerical
        value will follow. E.g. this might be "EF" for ejection fraction.
    This can be used, for example, to extract lab values from free-text notes.
    This looks for a string matching `preceding_phrase` followed by one of
    the value_indicators (is, of, :), followed by a numerical value. For
    example, if `preceding_phrase` is "EF" then it
    could extract the numerical value 60 from "EF: 60%" or "EF is 60%".
    If there are multiple pattern matches in the notes, the first match is
    returned.
    TODO(aforsyth): is first match the right behavior?
    """
    pattern_string = ('(?:%s)\s*(?:of|is|\:)?[:]*[\s]*([0-9]'
                      '+\.?[0-9]*)' % preceding_phrase)
    re_flags = re.I | re.M | re.DOTALL
    pattern = re.compile(pattern_string, flags=re_flags)
    match = next(pattern.finditer(notes))
    if match:
        numerical_value = float(match.groups()[0])
        return (numerical_value, match.start(), match.end())
    return (None, None, None)


def _check_phrase_in_notes(phrase, notes):
    """Return 1 if the notes contain phrase at least once, else 0."""
    pattern_string = '.*(%s)' % phrase
    re_flags = re.I | re.M | re.DOTALL
    pattern = re.compile(pattern_string, flags=re_flags)
    match = next(pattern.finditer(notes))
    if match:
        return (1, match.start(), match.end())
    return (0, None, None)


def _extract_values_from_rpdr_notes(rpdr_keys_to_notes,
                                    extract_numerical_value, phrase):
    """Return a list of rows with the regex values as the last element.

    Return a list of rows where each row begins with each of the values
    specified in the RPDR header for those notes. The last element of the
    row is the value of the regex extraction (either 0/1 when checking for
    phrase presence, or a numerical value for value extraction).
    """
    return_rows = []
    for rpdr_keys, rpdr_notes in rpdr_keys_to_notes.iteritems():
        if extract_numerical_value:
            (numerical_value, match_start, match_end) = \
                _extract_numerical_value(phrase, rpdr_notes)
        else:
            (numerical_value, match_start, match_end) = _check_phrase_in_notes(
                phrase, rpdr_notes)
        row = list(rpdr_keys)
        row.append(numerical_value)
        return_rows.append(row)
    return return_rows


def _split_rpdr_key_line(text_line):
    """Remove newline chars and split the line by bars."""
    return tuple(text_line.replace('\r', '').replace('\n', '').split('|'))


def _filter_rpdr_notes_by_column_val(rpdr_keys_to_notes,
                                     required_report_description,
                                     required_report_type):
    """Filter the rpdr notes by column values.

    Input:
    rpdr_keys_to_notes: the dict mapping rpdr column values as a tuple in the
        same format as the RPDR text header format to rpdr notes.
    required_report_description: a value for report description such as "ECG"
    required_report_type: a value for the report type such as "CAR"

    Return rpdr_keys_to_notes with all values filtered out whose keys differ
    from either `required_report_type` or `required_report_description` if
    those values are not None.
    """
    return_dict = rpdr_keys_to_notes.copy()
    for rpdr_keys, rpdr_notes in rpdr_keys_to_notes.iteritems():
        (empi, mrn_type, mrn, report_number, mid, report_date_time,
         report_description, report_status,
         report_type, report_text) = rpdr_keys
        if (required_report_description is not None and
                report_description != required_report_description):
            del return_dict[rpdr_keys]
            continue
        if (required_report_type is not None and
                report_type != required_report_type):
            del return_dict[rpdr_keys]
            continue
    return return_dict


def _parse_rpdr_text_file(rpdr_filename):
    """Return a map of tuple of rpdr column values to notes."""
    with open(rpdr_filename, 'rb') as rpdr_file:
        rpdr_lines = rpdr_file.readlines()
    # Expect this header describing the column values
    if rpdr_lines[0] != ('EMPI|MRN_Type|MRN|Report_Number|MID|Report_Date_Time'
                         '|Report_Description|Report_Status|Report_Type|'
                         'Report_Text\r\n'):
        raise ValueError('Invalid header for RPDR formatted text file. Got %s'
                         % rpdr_lines[0])
    header_column_names = _split_rpdr_key_line(rpdr_lines[0])

    # Map tuple of column values to free-text notes
    rpdr_keys_to_notes = {}

    # None if at the start of the file or in between patient notes.
    rpdr_keys = None
    for line in rpdr_lines[1:]:
        # If starting a new note and the current line is empty, continue.
        if not rpdr_keys and not line.replace('\r', '').replace('\n', ''):
            continue
        # If not current notes, try to extract the RPDR column values.
        if not rpdr_keys:
            if '|' not in line:
                raise ValueError('Expected RPDR column values as described in '
                                 'the header, separated by | at the start of '
                                 'a new note. Got %s' % line)
            rpdr_keys = _split_rpdr_key_line(line)
            if len(rpdr_keys) != len(header_column_names):
                raise ValueError('Expected RPDR column values of the same '
                                 'length as the header, got: %s' % rpdr_keys)
            if rpdr_keys in rpdr_keys_to_notes:
                raise KeyError('Expected rpdr_keys to be unique. Got %s '
                               'multiple times' % rpdr_keys)
            rpdr_keys_to_notes[rpdr_keys] = ''
        else:  # line is part of notes
            rpdr_keys_to_notes[rpdr_keys] += line
            if '[report end]' in line:
                rpdr_keys = None
    return rpdr_keys_to_notes


def _get_rows_for_turk_csv(rpdr_keys_to_notes, extract_numerical_value,
                           phrase):
    """Writes turk validation rows to csv including:
    (note, regex_value, patient, note_id, regex_extract_start,
     regex_extract_end)
    """
    return_rows = []
    for rpdr_keys, rpdr_notes in rpdr_keys_to_notes.iteritems():
        if extract_numerical_value:
            (numerical_value, match_start, match_end) = \
                _extract_numerical_value(phrase, rpdr_notes)
        else:
            (numerical_value, match_start, match_end) = _check_phrase_in_notes(
                phrase, rpdr_notes)
        (empi, mrn_type, mrn, report_number, mid, report_date_time,
         report_description, report_status,
         report_type, report_text) = rpdr_keys
        row = [rpdr_notes, numerical_value, empi, report_number, match_start,
               match_end]
        return_rows.append(row)
    return return_rows


def _write_turk_verification_csv(turk_csv_rows, turk_csv_name):
    """Convert the notes to HTML with regex extracted value bolded."""
    return_rows = []
    for [rpdr_notes, numerical_value, empi, report_number, match_start,
         match_end] in turk_csv_rows:
        # Make the extracted value bold.
        extracted_value_html = ("<span class='highlight'>%s</span>" %
                                rpdr_notes[match_start:match_end])
        rpdr_notes = (rpdr_notes[:match_start] + extracted_value_html +
                      rpdr_notes[match_end:])
        rpdr_notes = rpdr_notes.replace('\r\n', '<br>')
        return_rows.append((rpdr_notes, numerical_value, empi, report_number))
    with open(turk_csv_name, 'wb') as turk_csv:
        csvwriter = csv.writer(turk_csv)
        csvwriter.writerow(['image1', 'guess', 'empi', 'report_number'])
        csvwriter.writerows(return_rows)
    return return_rows


def main(input_filename, output_filename, extract_numerical_value, phrase,
         report_description, report_type, turk_csv_filename):
    rpdr_keys_to_notes = _parse_rpdr_text_file(input_filename)
    rpdr_keys_to_notes = _filter_rpdr_notes_by_column_val(
        rpdr_keys_to_notes, report_description, report_type)
    rpdr_rows_with_regex_value = _extract_values_from_rpdr_notes(
        rpdr_keys_to_notes, extract_numerical_value, phrase)
    with open(output_filename, 'wb') as output_file:
        csv_writer = csv.writer(output_file)
        csv_writer.writerows(rpdr_rows_with_regex_value)
    if turk_csv_filename:
        turk_rows = _get_rows_for_turk_csv(
            rpdr_keys_to_notes, extract_numerical_value, phrase)
        _write_turk_verification_csv(turk_rows, turk_csv_filename)

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
    parser.add_argument('--report_description', help=(
        'Only return values from reports matching this exact report '
        'description (e.g. "Cardiac Catheterization").'))
    parser.add_argument('--report_type', help=(
        'Only return values from reports matching this exact report '
        'description (e.g. "CAR").'))
    parser.add_argument('--turk_csv_filename', help=(
        'If a filename to a csv is entered, it will write a CSV file to'
        ' be used for localturk verification. If not entered, no such CSV'
        ' will be written.'))
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
                               % args.phrase)
    logging.debug('%s from %s and outputting rows to %s.' %
                  (extract_type_string, args.input_filename,
                   args.output_filename))

    main(args.input_filename, args.output_filename,
         args.extract_numerical_value, args.phrase,
         args.report_description, args.report_type,
         args.turk_csv_filename)
