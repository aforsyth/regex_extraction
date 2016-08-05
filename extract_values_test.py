import unittest

import extract_values


class TestFilterRPDRNotesByColumnVal(unittest.TestCase):
    def setUp(self):
        rpdr_keys1 = ('empi', 'mrn_type', 'mrn', 'report_number', 'mid',
                      'report_date_time', 'report_description1',
                      'report_status', 'report_type1', 'report_text')
        rpdr_keys2 = ('empi', 'mrn_type', 'mrn', 'report_number', 'mid',
                      'report_date_time', 'report_description2',
                      'report_status', 'report_type2', 'report_text')
        rpdr_keys3 = ('empi', 'mrn_type', 'mrn', 'report_number', 'mid',
                      'report_date_time', 'report_description3',
                      'report_status', 'report_type3', 'report_text')
        self.rpdr_keys_to_notes = {rpdr_keys1: '', rpdr_keys2: '',
                                   rpdr_keys3: ''}

    def test_no_filters_does_nothing(self):
        filtered_rpdr_keys_to_notes = (
            extract_values._filter_rpdr_notes_by_column_val(
                self.rpdr_keys_to_notes, None, None))
        self.assertEqual(self.rpdr_keys_to_notes, filtered_rpdr_keys_to_notes)

    def test_one_filter_works(self):
        filtered_rpdr_keys_to_notes = (
            extract_values._filter_rpdr_notes_by_column_val(
                self.rpdr_keys_to_notes, 'report_description1', None))
        self.assertEqual(1, len(filtered_rpdr_keys_to_notes))
        self.assertTrue(
            'report_description1' in filtered_rpdr_keys_to_notes.keys()[0])

    def test_two_filters_work(self):
        filtered_rpdr_keys_to_notes = (
            extract_values._filter_rpdr_notes_by_column_val(
                self.rpdr_keys_to_notes, 'report_description1',
                'report_type1'))
        self.assertEqual(1, len(filtered_rpdr_keys_to_notes))
        self.assertTrue(
            'report_description1' in filtered_rpdr_keys_to_notes.keys()[0])


if __name__ == '__main__':
    unittest.main()
