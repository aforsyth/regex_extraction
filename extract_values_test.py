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


class TestRegexPhraseMatch(unittest.TestCase):
    def setUp(self):
        self.rpdr_note = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'}, 'ventilate')

    def test_dont_match_at_start_of_longer_word(self):
        note_phrase_matches = extract_values._check_phrase_in_notes(
            ['vent'], self.rpdr_note)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(0, len(phrase_matches))

    def test_dont_match_at_end_of_longer_word(self):
        note_phrase_matches = extract_values._check_phrase_in_notes(
            ['ate'], self.rpdr_note)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(0, len(phrase_matches))

    def test_dont_match_in_middle_of_longer_word(self):
        note_phrase_matches = extract_values._check_phrase_in_notes(
            ['tila'], self.rpdr_note)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(0, len(phrase_matches))

    def test_match_exact_single_phrase_begin_and_end(self):
        note_phrase_matches = extract_values._check_phrase_in_notes(
            ['ventilate'], self.rpdr_note)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(1, len(phrase_matches))
        phrase_match = phrase_matches[0]
        self.assertEqual(1, phrase_match.extracted_value)

    def test_match_space_surround1(self):
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'}, ' ventilate')
        note_phrase_matches = extract_values._check_phrase_in_notes(
            ['ventilate'], rpdr_note2)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(1, len(phrase_matches))
        phrase_match = phrase_matches[0]
        self.assertEqual(1, phrase_match.extracted_value)

    def test_match_space_surround2(self):
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'}, ' ventilate ')
        note_phrase_matches = extract_values._check_phrase_in_notes(
            ['ventilate'], rpdr_note2)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(1, len(phrase_matches))
        phrase_match = phrase_matches[0]
        self.assertEqual(1, phrase_match.extracted_value)

    def test_match_punctuation(self):
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'}, ' ventilate.')
        note_phrase_matches = extract_values._check_phrase_in_notes(
            ['ventilate'], rpdr_note2)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(1, len(phrase_matches))
        phrase_match = phrase_matches[0]
        self.assertEqual(1, phrase_match.extracted_value)

    def test_match_punctuation2(self):
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'}, ' ventilate?')
        note_phrase_matches = extract_values._check_phrase_in_notes(
            ['ventilate'], rpdr_note2)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(1, len(phrase_matches))
        phrase_match = phrase_matches[0]
        self.assertEqual(1, phrase_match.extracted_value)

    def test_match_beginning_punctuation(self):
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'}, 'ventilate.')
        note_phrase_matches = extract_values._check_phrase_in_notes(
            ['ventilate'], rpdr_note2)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(1, len(phrase_matches))
        phrase_match = phrase_matches[0]
        self.assertEqual(1, phrase_match.extracted_value)

    def test_match_beginning_punctuation2(self):
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'}, 'ventilate?')
        note_phrase_matches = extract_values._check_phrase_in_notes(
            ['ventilate'], rpdr_note2)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(1, len(phrase_matches))
        phrase_match = phrase_matches[0]
        self.assertEqual(1, phrase_match.extracted_value)


if __name__ == '__main__':
    unittest.main()
