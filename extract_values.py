import argparse
import csv
import logging
import re
import string

import numpy as np

PHRASE_TYPE_WORD = 0
PHRASE_TYPE_NUM = 1
PHRASE_TYPE_DATE = 2


class RPDRNote(object):
    def __init__(self, rpdr_column_name_to_key, rpdr_note):
        self.empi = rpdr_column_name_to_key['EMPI']
        self.mrn_type = rpdr_column_name_to_key['MRN_Type']
        self.mrn = rpdr_column_name_to_key['MRN']
        self.report_type = (rpdr_column_name_to_key.get('Report_Type') or
                            rpdr_column_name_to_key.get('Subject'))
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

    def remove_punctuation_from_note(self):
        self.note = _remove_punctuation(self.note)


class NotePhraseMatches(object):
    """Describes all phrase matches for a particular RPDR Note"""
    def __init__(self, rpdr_note):
        self.rpdr_note = rpdr_note
        self.phrase_matches = []

    def add_phrase_match(self, phrase_match):
        self.phrase_matches.append(phrase_match)

    def finalize_phrase_matches(self):
        self.phrase_matches.sort(key=lambda x: x.match_start)


class PhraseMatch(object):
    """Describes a single phrase match to a single RPDR Note for a phrase."""
    def __init__(self, extracted_value, match_start, match_end, phrase):
        # Binary 0/1s for extracting phrase presence, else numerical value.
        self.extracted_value = extracted_value
        self.match_start = match_start
        self.match_end = match_end
        self.phrase = phrase


class PhraseMatchContexts(object):
    """Keeps track of words before/after a phrase match."""
    def __init__(self, n_words_before, n_words_after):
        self.n_words_before = n_words_before
        self.n_words_after = n_words_after
        self.context_frequencies = {}

    def add_match_context(self, note, match_start, match_end):
        if self.n_words_before == 0 and self.n_words_after == 0:
            return
        match_word = note[match_start:match_end]
        words_before = note[:match_start].split(' ')[-self.n_words_before:]
        words_after = note[match_end:].split(' ')[:self.n_words_after]
        context = ' '.join(words_before + [match_word] + words_after)
        self.context_frequencies.setdefault(context, 0)
        self.context_frequencies[context] += 1

    def print_ordered_contexts(self):
        if self.n_words_before == 0 and self.n_words_after == 0:
            return
        context_tuples = [(context, frequency) for context, frequency in
                          self.context_frequencies.iteritems()]
        context_tuples.sort(key=lambda x: x[1], reverse=True)
        print 'Frequency: context'
        for context, frequency in context_tuples:
            print '%d: %s' % (frequency, context)


def _remove_punctuation(s):
    return s.translate(None, string.punctuation)


def _extract_phrase_from_notes(
        phrase_type, phrases, rpdr_note, match_contexts):
    """Return a PhraseMatch object with the value as a binary 0/1 indicating
    whether one of the phrases was found in rpdr_note.note."""
    if phrase_type == PHRASE_TYPE_WORD:
        pattern_strings = [
            '(\s%s\s)', '(^%s\s)', '(\s%s$)', '(^%s$)', '(\s%s[\,\.\?\!\-])',
            '(^%s[\,\.\?\!\-])'
        ]
    elif phrase_type == PHRASE_TYPE_NUM:
        pattern_strings = [
            '(?:%s)\s*(?:of|is|was|were|are|\:)?[:]*[\s]*([0-9]+\.?[0-9]*)']
    elif phrase_type == PHRASE_TYPE_DATE:
        pattern_strings = [
            '(?:%s)\s*(?:of|is|was|were|are|\:)?[:]*[\s]*(\d+/\d+/\d+)',
            '(?:%s)\s*(?:of|is|was|were|are|\:)?[:]*[\s]*(\d+-\d+-\d+)']
    else:
        raise Exception('Invalid phrase extraction type.')

    phrase_matches = NotePhraseMatches(rpdr_note)
    for phrase in phrases:
        for pattern_string in pattern_strings:
            pattern_string = pattern_string % phrase
            re_flags = re.I | re.M | re.DOTALL
            pattern = re.compile(pattern_string, flags=re_flags)
            match_iter = pattern.finditer(rpdr_note.note)
            try:
                while True:
                    match = next(match_iter)
                    if phrase_type == PHRASE_TYPE_WORD:
                        extracted_value = 1
                    elif phrase_type == PHRASE_TYPE_NUM:
                        extracted_value = float(match.groups()[0])
                    elif phrase_type == PHRASE_TYPE_DATE:
                        extracted_value = match.groups()[0]
                    new_match = PhraseMatch(extracted_value, match.start(),
                                            match.end(), phrase)
                    phrase_matches.add_phrase_match(new_match)
                    match_contexts.add_match_context(
                        rpdr_note.note, match.start(), match.end())
            except StopIteration:
                continue
    phrase_matches.finalize_phrase_matches()
    return phrase_matches


def _extract_values_from_rpdr_notes(
        rpdr_notes, phrase_type, phrases, ignore_punctuation,
        show_n_words_context_before, show_n_words_context_after):
    """Return a list of NotePhraseMatches for each note in rpdr_notes."""
    note_phrase_matches = []
    if ignore_punctuation:
        logging.info('ignore_punctuation is True, so we will also ignore '
                     'any punctuation in the entered phrases.')
        phrases = [_remove_punctuation(phrase) for phrase in phrases]
    match_contexts = PhraseMatchContexts(
        show_n_words_context_before, show_n_words_context_after)
    for rpdr_note in rpdr_notes:
        if ignore_punctuation:
            rpdr_note.remove_punctuation_from_note()
        phrase_matches = _extract_phrase_from_notes(phrase_type, phrases,
                                                    rpdr_note, match_contexts)
        note_phrase_matches.append(phrase_matches)
    match_contexts.print_ordered_contexts()
    return note_phrase_matches


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


def _group_rpdr_notes_by_patient(rpdr_notes):
    """Group all rpdr notes with the same EMPI as one.

    Group all of the rpdr notes with the same EMPI, adding their notes with
    four empty lines in between, and the other row values equal to the row
    values for the first RPDR note in the input list.
    """
    empi_to_notes = {}
    for rpdr_note in rpdr_notes:
        empi_to_notes.setdefault(rpdr_note.empi, []).append(rpdr_note)

    grouped_rpdr_notes = []
    for empi, rpdr_notes in empi_to_notes.iteritems():
        first_note = rpdr_notes[0]
        for rpdr_note in rpdr_notes[1:]:
            first_note.note += ('\n\n\n\n' + rpdr_note.note)
        grouped_rpdr_notes.append(first_note)
    return grouped_rpdr_notes


def _parse_rpdr_text_file(rpdr_filename):
    """Return a list of RPDR Note objects"""
    with open(rpdr_filename, 'rb') as rpdr_file:
        rpdr_lines = rpdr_file.readlines()
    header_column_names = _split_rpdr_key_line(rpdr_lines[0])

    # None if at the start of the file or in between patient notes.
    rpdr_keys = None

    rpdr_note = ''
    rpdr_notes = []

    ignore_lines = False  # True if bad formatted header
    num_bad_formatted_headers = 0
    for line_number, line in enumerate(rpdr_lines[1:]):
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
                ignore_lines = True
                num_bad_formatted_headers += 1
                continue
                # raise ValueError('Expected RPDR column values of the same '
                #                'length as the header (%s), got: %s of length'
                #                  ' %s at line number: %s'
                #                  % (len(header_column_names), str(rpdr_keys),
                #                     len(rpdr_keys), line_number))
            rpdr_column_name_to_key = {
                column_name: key for (column_name, key) in
                zip(header_column_names, rpdr_keys)
            }
            rpdr_note = ''
        else:  # line is part of notes
            if not ignore_lines:
                rpdr_note += line
            if '[report_end]' in line:
                rpdr_keys = None
                if not ignore_lines:
                    rpdr_note = RPDRNote(rpdr_column_name_to_key, rpdr_note)
                    rpdr_notes.append(rpdr_note)
                ignore_lines = False
    logging.info('Num bad formatted headers: %s' % num_bad_formatted_headers)
    return rpdr_notes


def _html_clean_rpdr_note(html_note):
    html_note = html_note.replace('\r\n', '<br>')
    html_note = html_note.replace('"', "'")
    html_note = html_note.replace('\n', '<br>')
    html_note = html_note.replace('\r', '<br>')
    return html_note


def _write_turk_verification_csv(
        phrase_matches_by_note, phrases, context_size, turk_csv_name,
        num_negative_matches_to_show=0):
    """Convert the notes to HTML with regex extracted value bolded.

    Return only rows for which there was a value extracted. I.e. if extracting
    a numerical value, only rows with a non-None value will be returned. If
    checking phrase presence, only rows with a 1 binary value indicating phrase
    presence will be included.

    If context_size is specified, it will return context_size words before and
    after each match, with each match separated by line breaks.
    """
    return_rows = []
    non_match_notes = []  # indices in phrase_matches_by_note
    for note_phrase_matches in phrase_matches_by_note:
        rpdr_note = note_phrase_matches.rpdr_note.note
        html_note = ''  # extra variable used for context_size matches
        note_offset = 0  # offset due to HTML formatting
        if not note_phrase_matches.phrase_matches:  # no matches
            non_match_notes.append(note_phrase_matches)
            continue
        for phrase_match in note_phrase_matches.phrase_matches:
            match_start = phrase_match.match_start + note_offset
            match_end = phrase_match.match_end + note_offset
            extracted_value_html = ("<span class='highlight'>%s</span>" %
                                    rpdr_note[match_start:match_end])
            # if context_size specified, only get a small context pre/post
            if context_size is not None:
                pre_match_words = ' '.join(
                    rpdr_note[:match_start].split(' ')[-context_size:])
                post_match_words = ' '.join(
                    rpdr_note[match_end:].split(' ')[:context_size])
                html_note += (pre_match_words + extracted_value_html +
                              post_match_words + '<br><br>')
            rpdr_note = (rpdr_note[:match_start] + extracted_value_html +
                         rpdr_note[match_end:])
            if context_size is None:
                html_note = rpdr_note  # if not None, use full rpdr_note

            # keeps track of how many extra chars have been added to the note
            # since match starts/end were for the original note pre-HTML
            note_offset += (len(extracted_value_html) -
                            (match_end - match_start))
        html_note = _html_clean_rpdr_note(html_note)

        # use the value extracted from the first phrase match even if there
        # were multiple matches. this is obviously correct when doing phrase
        # matches. this might not be correct behavior when extracting
        # numerical values, however.
        extracted_value = note_phrase_matches.phrase_matches[0].extracted_value
        return_rows.append((
            html_note, extracted_value, note_phrase_matches.rpdr_note.empi,
            note_phrase_matches.rpdr_note.report_number))

    num_negative_matches_to_show = min(num_negative_matches_to_show,
                                       len(non_match_notes))
    if non_match_notes:
        negative_matches_to_show = np.random.choice(
            non_match_notes, num_negative_matches_to_show)
    else:
        negative_matches_to_show = []
    for note_phrase_matches in negative_matches_to_show:
        html_note = _html_clean_rpdr_note(note_phrase_matches.rpdr_note.note)
        extracted_value = None
        return_rows.append((
            html_note, extracted_value, note_phrase_matches.rpdr_note.empi,
            note_phrase_matches.rpdr_note.report_number))

    with open(turk_csv_name, 'wb') as turk_csv:
        csvwriter = csv.writer(turk_csv)
        csvwriter.writerow(['image1', 'guess', 'empi', 'report_number'])
        csvwriter.writerows(return_rows)
    return return_rows


def _write_csv_output(note_phrase_matches, output_filename):
    """Write one CSV row for each phrase_match where the row contains all of
    the RPDR note keys along with the extracted numerical value at the end of
    the row."""
    rpdr_rows_with_regex_value = []
    for phrase_matches in note_phrase_matches:
        row = phrase_matches.rpdr_note.get_keys()
        if not phrase_matches.phrase_matches:
            extracted_value = None
        else:
            extracted_value = phrase_matches.phrase_matches[0].extracted_value
        row.append(extracted_value)
        rpdr_rows_with_regex_value.append(row)

    with open(output_filename, 'wb') as output_file:
        csv_writer = csv.writer(output_file)
        csv_writer.writerows(rpdr_rows_with_regex_value)


def main(input_filename, output_filename, phrase_type, phrases,
         report_description, report_type, group_by_patient, context_size,
         ignore_punctuation, turk_csv_filename, num_negative_matches_to_show,
         show_n_words_context_before, show_n_words_context_after):
    rpdr_notes = _parse_rpdr_text_file(input_filename)
    rpdr_notes = _filter_rpdr_notes_by_column_val(
        rpdr_notes, report_description, report_type)
    if group_by_patient:
        rpdr_notes = _group_rpdr_notes_by_patient(rpdr_notes)

    note_phrase_matches = _extract_values_from_rpdr_notes(
        rpdr_notes, phrase_type, phrases, ignore_punctuation,
        show_n_words_context_before, show_n_words_context_after)
    _write_csv_output(note_phrase_matches, output_filename)

    _write_turk_verification_csv(
        note_phrase_matches, phrases, context_size, turk_csv_filename,
        num_negative_matches_to_show)

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
    parser.add_argument('--extract_date', action='store_true',
                        default=False, help=('Extracts a date if'
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
        '--group_by_patient', default=False, action='store_true', help=(
            'Aggregate all notes for a single patient into one row per patient'
            '. Output CSV will have one row per patient, and regex extraction '
            'will look for all matches in the notes for that patient.'
            'Enabling this also means that only some context for the extracted'
            'value will be displayed on localturk instead of the entire '
            'patient note.'))
    parser.add_argument('--context_size', type=int, help=(
        'Amount of context to show before/after a match (number of words).'))
    parser.add_argument(
        '--turk_csv_filename', default='localturk/tasks.csv', help=(
            'Will write a CSV file to the specified filenme for turk'
            'verification. Defaults to localturk/tasks.csv'))
    parser.add_argument(
        '--num_negative_turk_matches_to_show', type=int, default=0, help=(
            'Turk verification will ask to verify all positive matches, and '
            'up to this many negative matches.'))
    parser.add_argument(
        '--ignore_punctuation', default=False, action='store_true', help=(
            'If specified, punctuation characters will be ignored when '
            'finding a match. E.g. "full code confirmed" would also match '
            '"full code (confirmed)" and "full code -- confirmed".'))
    parser.add_argument('--verbosity', '-v', action='count')
    parser.add_argument(
        '--show_n_words_context_before', type=int, default=0,
        help=(
            'If specified, N words of context will be printed to the '
            'console prior to each text match in order of and along with '
            'their frequency of occuring in the text.'))
    parser.add_argument(
        '--show_n_words_context_after', default=0, type=int,
        help=(
            'If specified, N words of context will be printed to the '
            'console after each text match in order of and along with '
            'their frequency of occuring in the text.'))
    parser.add_argument('--v', action='count')

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
    if args.context_size is None and args.group_by_patient:
        args.context_size = 10
    logging.debug('%s from %s and outputting rows to %s.' %
                  (extract_type_string, args.input_filename,
                   args.output_filename))
    phrases = args.phrases.split(',')

    if args.extract_numerical_value and args.extract_date:
        raise Exception('Cannot both extract_numerical_value and extract_date'
                        '. Choose one option.')

    if args.extract_numerical_value:
        phrase_type = PHRASE_TYPE_NUM
    elif args.extract_date:
        phrase_type = PHRASE_TYPE_DATE
    else:
        phrase_type = PHRASE_TYPE_WORD

    main(args.input_filename, args.output_filename, phrase_type, phrases,
         args.report_description, args.report_type, args.group_by_patient,
         args.context_size, args.ignore_punctuation,
         args.turk_csv_filename, args.num_negative_turk_matches_to_show,
         args.show_n_words_context_before, args.show_n_words_context_after)
