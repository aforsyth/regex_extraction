"""Convert DFCI formatted files into the relevant fields of RPDR formatted
files for use with train_crf and get_cohort"""
import argparse
import csv


def date_name_converter(date):
    """Convert date strings like "DD-MonthName3Letters-YY" to "MM-DD-YY" """
    for month_num, month in enumerate(
        ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct',
         'Nov', 'Dec']):
        num_str = str(month_num + 1)
        if len(num_str) == 1:
            num_str = '0' + num_str
        date = date.replace(month, num_str)
    date_dd, date_mm, date_yy = date.split('-')
    return '%s-%s-%s' % (date_mm, date_dd, date_yy)


def iterate_dfci_notes(fname):
    if fname[-3:].lower() != 'txt':
        raise Exception('Expected txt file for DFCI notes')
    num_wrong_size_row = 0
    with open(fname, 'rb') as f:
        for row_num, row in enumerate(f):
            if row_num == 0:
                header_row = row.split('|')
                header_row = [header_row_e.replace('\n', '').replace('\r', '')
                              for header_row_e in header_row]
                continue
            row = row.split('|')
            if len(row) == len(header_row) - 1 and not header_row[-1]:
                pass
            elif len(row) != len(header_row):
                num_wrong_size_row += 1
                continue
            yield {header_row_e: row_e for header_row_e, row_e in
                   zip(header_row, row)}
    print 'Num wrong sized rows:', num_wrong_size_row
    print 'Num rows:', row_num


def convert_notes(input_filename):
    rows = [['EMPI', 'MRN', 'MRN_Type', 'Report_Number', 'Report_Description',
             'Report_Type', 'LMRNote_Date', 'Comments']]
    num_null_date = 0
    for row_num, row in enumerate(iterate_dfci_notes(input_filename)):
        patient_id = row['DFCI_MRN']
        mrn = 'DFCI_MRN_' + str(patient_id)
        lmr_note_date = row['DATE_OF_SERVICE']
        if lmr_note_date == 'null' or not lmr_note_date:
            num_null_date += 1
            continue
        lmr_note_date = lmr_note_date.split(' ')[0]  # remove time data
        if 'NOTE_TXT' not in row:
            print row.keys()
            raise
        comments = row['NOTE_TXT']
        empi = 'DFCI_PATIENT_ID_' + row['#PATIENT_ID']
        mrn_type = 'DFCI'
        report_number = row['NOTE_ID']
        report_description = row['INPATIENT_NOTE_TYPE_DESCR']
        report_type = row['INPATIENT_NOTE_TYPE_CD']
        rows.append([empi, mrn, mrn_type, report_number, report_description,
                     report_type, lmr_note_date, comments])
    print 'Num notes file null date rows:', num_null_date
    return rows


def main(input_filename, output_filename):
    lno_rows = convert_notes(input_filename)
    with open(output_filename, 'wb') as f:
        csv_writer = csv.writer(f, delimiter='|')
        csv_writer.writerows(lno_rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_filename',
                        help=('Path to a DFCI formatted '
                              'text file, e.g. /Users/user1/../file.txt'))
    parser.add_argument('output_filename',
                        help=('Path to write an RPDR file at'
                              'text file, e.g. /Users/user1/../file.txt'))
    args = parser.parse_args()
    main(args.input_filename, args.output_filename)
