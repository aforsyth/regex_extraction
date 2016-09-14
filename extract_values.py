import argparse
import csv
import logging
import re


class RPDRNote(object):
    def __init__(self, rpdr_column_name_to_key, rpdr_note):
        self.empi = rpdr_column_name_to_key['EMPI']
        self.mrn_type = rpdr_column_name_to_key['MRN_Type']
        self.mrn = rpdr_column_name_to_key['MRN']
        self.report_type = rpdr_column_name_to_key['Report_Type']
        self.report_number = (rpdr_column_name_to_key.get('Report_Number') or
                              rpdr_column_name_to_key.get('Record_Id'))
        self.report_description = rpdr_column_name_to_key.get(
            'Report_Description')
        self.report_date = (rpdr_column_name_to_key.get('Report_Date_Time') or
                            rpdr_column_name_to_key.get('LMRNote_Date'))
        self.note = rpdr_note

    def get_keys(self):
        return [self.empi, self.mrn_type, self.mrn, self.report_type,
                self.report_number, self.report_date]


def _extract_numerical_value(preceding_phrases, note):
    """Return a numerical value preceded by the a set of phrases.

    Return (numerical_value (as a float), match_start, match_end). Will return
        the first match for the first phrase in preceding_phrases that has a
        match in the supplied note.

    Input:
    preceding_phrases: a list of phrases or words indicating that the desired
        numerical value will follow. E.g. this might be ["EF",
        "ejection fraction", "LVEF"] for ejection fraction.
    This can be used, for example, to extract lab values from free-text notes.
    This looks for a string matching `preceding_phrase` followed by one of
    the value_indicators (is, of, :), followed by a numerical value. For
    example, if `preceding_phrase` is "EF" then it
    could extract the numerical value 60 from "EF: 60%" or "EF is 60%".
    If there are multiple pattern matches in the notes, the first match is
    returned.
    TODO(aforsyth): is first match the right behavior?
    """
    for preceding_phrase in preceding_phrases:
        pattern_string = ('(?:%s)\s*(?:of|is|\:)?[:]*[\s]*([0-9]'
                          '+\.?[0-9]*)' % preceding_phrase)
        re_flags = re.I | re.M | re.DOTALL
        pattern = re.compile(pattern_string, flags=re_flags)
        try:
            match = next(pattern.finditer(note))
            numerical_value = float(match.groups()[0])
            return (numerical_value, match.start(), match.end())
        except StopIteration:
            continue
    return (None, None, None)


def _check_phrase_in_notes(phrases, note):
    """Return 1 if the notes contain at least one of the phrases at least once,
    else 0."""
    for phrase in phrases:
        pattern_string = '(%s)' % phrase
        re_flags = re.I | re.M | re.DOTALL
        pattern = re.compile(pattern_string, flags=re_flags)
        try:
            match = next(pattern.finditer(note))
            return (1, match.start(), match.end())
        except StopIteration:
            continue
    return (0, None, None)


def _extract_values_from_rpdr_notes(rpdr_notes,
                                    extract_numerical_value, phrases):
    """Return a list of rows with the regex values as the last element.

    Return a list of rows where each row begins with each of the values
    specified in the RPDR header for those notes. The last element of the
    row is the value of the regex extraction (either 0/1 when checking for
    phrase presence, or a numerical value for value extraction).
    """
    return_rows = []
    for rpdr_note in rpdr_notes:
        if extract_numerical_value:
            (numerical_value, match_start, match_end) = \
                _extract_numerical_value(phrases, rpdr_note.note)
        else:
            (numerical_value, match_start, match_end) = _check_phrase_in_notes(
                phrases, rpdr_note.note)
        row = rpdr_note.get_keys()
        row.append(numerical_value)
        return_rows.append(row)
    return return_rows


def _split_rpdr_key_line(text_line):
    """Remove newline chars and split the line by bars."""
    return tuple(text_line.replace('\r', '').replace('\n', '').split('|'))


def _filter_rpdr_notes_by_column_val(rpdr_notes,
                                     required_report_description,
                                     required_report_type):
    """Filter the rpdr notes by column values.

    Input:
    rpdr_notes: the list of RPDR note objects.
    required_report_description: a value for report description such as "ECG"
    required_report_type: a value for the report type such as "CAR"

    Return rpdr_notes with all values filtered out whose keys differ
    from either `required_report_type` or `required_report_description` if
    those values are not None.
    """
    filtered_rpdr_notes = []
    for rpdr_note in rpdr_notes:
        if (required_report_description is not None and
                rpdr_note.report_description != required_report_description):
            continue
        if (required_report_type is not None and
                rpdr_note.report_type != required_report_type):
            continue
        filtered_rpdr_notes.append(rpdr_note)
    return filtered_rpdr_notes


def _parse_rpdr_text_file(rpdr_filename):
    """Return a list of RPDR Note objects"""
    with open(rpdr_filename, 'rb') as rpdr_file:
        rpdr_lines = rpdr_file.readlines()
    header_column_names = _split_rpdr_key_line(rpdr_lines[0])

    # None if at the start of the file or in between patient notes.
    rpdr_keys = None

    rpdr_note = ''
    rpdr_notes = []
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
            rpdr_column_name_to_key = {
                column_name: key for (column_name, key) in
                zip(header_column_names, rpdr_keys)
            }
            rpdr_note = ''
        else:  # line is part of notes
            rpdr_note += line
            if '[report_end]' in line:
                rpdr_keys = None
                rpdr_note = RPDRNote(rpdr_column_name_to_key, rpdr_note)
                rpdr_notes.append(rpdr_note)
    return rpdr_notes


def _get_rows_for_turk_csv(rpdr_notes, extract_numerical_value,
                           phrases):
    """Writes turk validation rows to csv including:
    (note, regex_value, patient, note_id, regex_extract_start,
     regex_extract_end)
    """
    return_rows = []
    for rpdr_note in rpdr_notes:
        if extract_numerical_value:
            (numerical_value, match_start, match_end) = \
                _extract_numerical_value(phrases, rpdr_note.note)
        else:
            (numerical_value, match_start, match_end) = _check_phrase_in_notes(
                phrases, rpdr_note.note)
        row = [rpdr_note.note, numerical_value, rpdr_note.empi,
               rpdr_note.report_number, match_start, match_end]
        return_rows.append(row)
    return return_rows


def _write_turk_verification_csv(turk_csv_rows, turk_csv_name,
                                 extract_numerical_value):
    """Convert the notes to HTML with regex extracted value bolded.

    Return only rows for which there was a value extracted. I.e. if extracting
    a numerical value, only rows with a non-None value will be returned. If
    checking phrase presence, only rows with a 1 binary value indicating phrase
    presence will be included.
    """
    return_rows = []
    for [rpdr_notes, numerical_value, empi, report_number, match_start,
         match_end] in turk_csv_rows:
        # Make the extracted value bold.
        extracted_value_html = ("<span class='highlight'>%s</span>" %
                                rpdr_notes[match_start:match_end])
        rpdr_notes = (rpdr_notes[:match_start] + extracted_value_html +
                      rpdr_notes[match_end:])
        rpdr_notes = rpdr_notes.replace('\r\n', '<br>')

        # If extracting numerical value, and None was extracted, continue. Or,
        # if not extracting numerical value, and no match, continue.
        if ((numerical_value is None and extract_numerical_value) or
                (numerical_value == 0.0 and not extract_numerical_value)):
            continue
        return_rows.append((rpdr_notes, numerical_value, empi, report_number))
    with open(turk_csv_name, 'wb') as turk_csv:
        csvwriter = csv.writer(turk_csv)
        csvwriter.writerow(['image1', 'guess', 'empi', 'report_number'])
        csvwriter.writerows(return_rows)
    return return_rows


def main(input_filename, output_filename, extract_numerical_value, phrases,
         report_description, report_type, turk_csv_filename):
    rpdr_notes = _parse_rpdr_text_file(input_filename)
    rpdr_notes = _filter_rpdr_notes_by_column_val(
        rpdr_notes, report_description, report_type)

    rpdr_rows_with_regex_value = _extract_values_from_rpdr_notes(
        rpdr_notes, extract_numerical_value, phrases)
    with open(output_filename, 'wb') as output_file:
        csv_writer = csv.writer(output_file)
        csv_writer.writerows(rpdr_rows_with_regex_value)

    turk_rows = _get_rows_for_turk_csv(
        rpdr_notes, extract_numerical_value, phrases)
    _write_turk_verification_csv(turk_rows, turk_csv_filename,
                                 extract_numerical_value)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_filename',
                        help=('Path to an RPDR formatted '
                              'text file, e.g. /Users/user1/../file.txt'))
    parser.add_argument('--output_filename', default='output.csv',
                        help=('Path to csv file to output results. Defaults to'
                              ' ./output.csv'))
    parser.add_argument('--extract_numerical_value', action='store_true',
                        default=False, help=('Extracts a numerical value if'
                                             ' specified. Else, checks for '
                                             'presence of the phrase.'))
    parser.add_argument('--phrases', required=True, help=(
        'A list of comma separated phrases such as "phrase1,phrase2". Each '
        'phrase should be either the phrase to check for if not exracting a '
        'numerical value, or the phrase preceding the numerical value if '
        'extracting a number.'))
    parser.add_argument('--report_description', help=(
        'Only return values from reports matching this exact report '
        'description (e.g. "Cardiac Catheterization").'))
    parser.add_argument('--report_type', help=(
        'Only return values from reports matching this exact report '
        'description (e.g. "CAR").'))
    parser.add_argument(
        '--turk_csv_filename', default='localturk/tasks.csv', help=(
            'Will write a CSV file to the specified filenme for turk'
            'verification. Defaults to localturk/tasks.csv'))
    parser.add_argument('--verbosity', '-v', action='count')
    args = parser.parse_args()

    if args.verbosity == 1:
        logging.basicConfig(filename='extraction.log', level=logging.INFO)
    elif args.verbosity > 1:
        logging.basicConfig(filename='extraction.log', level=logging.DEBUG)

    if not args.extract_numerical_value:
        extract_type_string = 'Extracting exact phrases "%s"' % args.phrases
    else:
        extract_type_string = ('Extracting numerical value preceded by one of'
                               '"%s" ' % args.phrases)
    logging.debug('%s from %s and outputting rows to %s.' %
                  (extract_type_string, args.input_filename,
                   args.output_filename))
    phrases = args.phrases.split(',')

    main(args.input_filename, args.output_filename,
         args.extract_numerical_value, phrases,
         args.report_description, args.report_type,
         args.turk_csv_filename)
