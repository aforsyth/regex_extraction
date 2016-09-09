import unittest

import extract_values


class TestFilterRPDRNotesByColumnVal(unittest.TestCase):
    def setUp(self):
        rpdr_note1 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'}, 'note1')

        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi2', 'MRN_Type': 'mrn_type2',
             'Report_Number': '1232', 'MRN': '1232',
             'Report_Type': 'report_type2',
             'Report_Description': 'report_description2'}, 'note2')

        rpdr_note3 = extract_values.RPDRNote(
            {'EMPI': 'empi3', 'MRN_Type': 'mrn_type3',
             'Report_Number': '1233', 'MRN': '1233',
             'Report_Type': 'report_type3',
             'Report_Description': 'report_description3'}, 'note3')

        self.rpdr_notes = [rpdr_note1, rpdr_note2, rpdr_note3]

    def test_no_filters_does_nothing(self):
        filtered_rpdr_notes = (
            extract_values._filter_rpdr_notes_by_column_val(
                self.rpdr_notes, None, None))
        self.assertEqual(self.rpdr_notes, filtered_rpdr_notes)

    def test_one_filter_works(self):
        filtered_rpdr_notes = (
            extract_values._filter_rpdr_notes_by_column_val(
                self.rpdr_notes, 'report_description1', None))
        self.assertEqual(1, len(filtered_rpdr_notes))

    def test_two_filters_work(self):
        filtered_rpdr_notes = (
            extract_values._filter_rpdr_notes_by_column_val(
                self.rpdr_notes, 'report_description1',
                'report_type1'))
        self.assertEqual(1, len(filtered_rpdr_notes))


if __name__ == '__main__':
    unittest.main()
