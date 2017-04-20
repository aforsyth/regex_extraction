"""Convert DFCI formatted files into the relevant fields of RPDR formatted files for use with train_crf and get_cohort"""
import config
import csv
import utils


def date_name_converter(date):
    """Convert date strings like "DD-MonthName3Letters-YY" to "MM-DD-YY" """
    for month_num, month in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
        num_str = str(month_num + 1)
        if len(num_str) == 1:
            num_str = '0' + num_str
        date = date.replace(month, num_str)
    date_dd, date_mm, date_yy = date.split('-')
    return '%s-%s-%s' % (date_mm, date_dd, date_yy)    


def convert_diagnoses():
    breast_cancer_code = '174.1'
    rows = [['EMPI', 'Date', 'Code']]
    new_patient_ids = set()
    num_null_date = 0
    for row_num, row in enumerate(utils.iterate_dfci_csv(config.DFCI_DIAGNOSIS_FILE)):
        if 'breast' in row['SITE_DESCR'].lower():
            patient_id = row['PATIENT_ID']    
            empi = 'DFCI_' + str(patient_id)
            date = row['DIAGNOSIS_DT']
            if date == 'null' or not date:
                num_null_date += 1
                continue
            date = date_name_converter(date)
            new_row = [empi, date, breast_cancer_code]
            rows.append(new_row)
            new_patient_ids.add(patient_id)
    print 'Num rows of breast cancer diagnoses: %d out of %d' % (len(rows) - 1, row_num + 1)
    print 'Num diagnosis null dates:', num_null_date
    return [new_patient_ids, rows]


def convert_chemo_medications(patient_ids):
    rows = [['EMPI', 'Medication', 'Medication_Date']]
    new_patient_ids = set()
    num_null_date = 0
    for row_num, row in enumerate(utils.iterate_dfci_csv(config.DFCI_CHEMO_FILE)):
        dfci_drug_name = row['DFCI_FULL_DRUG_NAME'].lower()
        patient_id = row['PATIENT_ID']
        medication_date = row['VISIT_DT']
        if medication_date == 'null' or not medication_date:
            num_null_date += 1
            continue
        medication_date = date_name_converter(medication_date)
        if patient_id not in patient_ids:
            continue
        for chemo_name in config.CHEMO_NAMES:
            if chemo_name in dfci_drug_name:
                empi = 'DFCI_' + str(patient_id)
                new_patient_ids.add(patient_id)
                rows.append([empi, chemo_name, medication_date])
                break
    print 'Num rows receiving relevant chemo: %d out of %d' % (len(rows) - 1, row_num + 1)
    print 'Num chemo rows with null date:', num_null_date
    print 'Num diagnosis patient IDs seen in chemo file %d out of %d' % (len(new_patient_ids), len(patient_ids))
    return [new_patient_ids, rows]


def convert_notes(patient_ids):
    rows = [['EMPI', 'LMRNote_Date', 'Comments']]
    num_null_date = 0
    dfci_mrn_to_patient_id = utils.get_dfci_mrn_to_patient_id()
    for row_num, row in enumerate(utils.iterate_dfci_notes(config.DFCI_DATASET_FILE)):
        patient_id = dfci_mrn_to_patient_id[row['DFCI_MRN']]
        if patient_id not in patient_ids:
            continue
        empi = 'DFCI_' + str(patient_id)
        lmr_note_date = row['DATE_OF_SERVICE']
        if lmr_note_date == 'null' or not lmr_note_date:
            num_null_date += 1
            continue
        lmr_note_date = lmr_note_date.split(' ')[0] # remove time data
        if 'NOTE_TXT' not in row:
            print row.keys()
            raise
        comments = row['NOTE_TXT']
        rows.append([empi, lmr_note_date, comments])
    print 'Num notes file null date rows:', num_null_date
    return rows


def main():
    patient_ids, dia_rows = convert_diagnoses()
    patient_ids, med_rows = convert_chemo_medications(patient_ids)
    lno_rows = convert_notes(patient_ids)
    
    for extension, rows in [('Dia', dia_rows), ('Med', med_rows), ('Lno', lno_rows)]:
        with open(config.DFCI_RPDR_FORMATTED_FOLDER + extension + '.txt', 'wb') as f: 
            csv_writer = csv.writer(f, delimiter='|') 
            csv_writer.writerows(rows)


if __name__ == '__main__':
    main()

