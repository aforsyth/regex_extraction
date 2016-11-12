import argparse
import csv
import datetime


def _convert_rpdr_timestamp_to_seconds(rpdr_timestamp_string):
    date = datetime.datetime.strptime(rpdr_timestamp_string, '%m/%d/%Y')
    epoch = datetime.datetime.utcfromtimestamp(0)
    return (date - epoch).total_seconds()


def _get_empi_to_date_range(filter_csv_filename):
    empi_to_date_range = {}  # map empi to (seconds_start, seconds_end)
    with open(filter_csv_filename, 'rb') as filter_csv:
        csv_reader = csv.reader(filter_csv)
        for row_num, row in enumerate(csv_reader):
            if row_num == 0:
                header_row = row
                expected_header_row = ['empi', 'procedure_date', 'days_before',
                                       'days_after', 'include']
                if (header_row != expected_header_row):
                    raise Exception('Invalid filter csv header. Expected %s, '
                                    'Got %s' %
                                    (str(expected_header_row), str(row)))
                continue
            empi, procedure_date, days_before, days_after, include = row
            days_before = int(days_before)
            days_after = int(days_after)
            include = int(include)
            if include == 0:
                continue
            if empi in empi_to_date_range:
                raise Exception('Seen EMPI: %s multiple times' % empi)
            one_day_seconds = 60 * 60 * 24
            procedure_date_seconds = _convert_rpdr_timestamp_to_seconds(
                procedure_date)
            start_date_seconds = (procedure_date_seconds -
                                  days_before * one_day_seconds)
            end_date_seconds = (procedure_date_seconds +
                                days_after * one_day_seconds)
            empi_to_date_range[empi] = (start_date_seconds, end_date_seconds)
    return empi_to_date_range


def _split_rpdr_key_line(text_line):
    """Remove newline chars and split the line by bars."""
    return tuple(text_line.replace('\r', '').replace('\n', '').split('|'))


def _filter_rpdr_notes(empi_to_date_range, rpdr_filename):
    """Return only RPDR notes for EMPIs in empi_to_date_range with dates
    within that range."""
    filtered_notes = ''
    with open(rpdr_filename, 'rb') as rpdr_file:
        rpdr_lines = rpdr_file.readlines()
    header_column_names = _split_rpdr_key_line(rpdr_lines[0])

    # None if at the start of the file or in between patient notes.
    rpdr_keys = None
    ignore_lines = False  # True if bad formatted header or no EMPI/date match
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
                continue
            rpdr_column_name_to_key = {
                column_name: key for (column_name, key) in
                zip(header_column_names, rpdr_keys)
            }
            empi = rpdr_column_name_to_key['EMPI']
            note_date = (rpdr_column_name_to_key.get('Report_Date_Time') or
                         rpdr_column_name_to_key.get('LMRNote_Date'))
            note_date = note_date.split(' ')[0]  # after space is the time
            # Ignore lines if we're not interested in this EMPI
            if empi not in empi_to_date_range:
                ignore_lines = True
                continue
            note_date_seconds = _convert_rpdr_timestamp_to_seconds(note_date)
            date_range_start, date_range_end = empi_to_date_range[empi]
            # Ignore lines if note date is out of the desired range
            if (note_date_seconds < date_range_start or
                    note_date_seconds > date_range_end):
                ignore_lines = True
                continue
            filtered_notes += line
        else:  # line is part of notes
            if not ignore_lines:
                filtered_notes += line
            if '[report_end]' in line:
                rpdr_keys = None
                ignore_lines = False
    filtered_notes = rpdr_lines[0] + '\n' + filtered_notes
    return filtered_notes


def main(rpdr_filename, filter_csv_filename, output_filename):
    empi_to_date_range = _get_empi_to_date_range(filter_csv_filename)
    filtered_notes = _filter_rpdr_notes(empi_to_date_range, rpdr_filename)
    with open(output_filename, 'wb') as output_file:
        output_file.write(filtered_notes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('rpdr_filename',
                        help=('Path to an RPDR formatted '
                              'text file, e.g. /Users/user1/../file.txt'))
    parser.add_argument('filter_csv_filename',
                        help=('Path to a CSV file specifying EMPIs and '
                              'procedure dates of interest.'))
    parser.add_argument('--output_filename', required=False)
    args = parser.parse_args()
    if not args.output_filename:
        input_fname_list = args.rpdr_filename.split('.')
        output_filename = (input_fname_list[0] + '_filtered.' +
                           input_fname_list[1])
    else:
        output_filename = args.output_filename
    main(args.rpdr_filename, args.filter_csv_filename, output_filename)
