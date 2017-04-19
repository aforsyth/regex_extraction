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
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            0, ['vent'], self.rpdr_note, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(0, len(phrase_matches))

    def test_dont_match_at_end_of_longer_word(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            0, ['ate'], self.rpdr_note, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(0, len(phrase_matches))

    def test_dont_match_in_middle_of_longer_word(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            0, ['tila'], self.rpdr_note, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(0, len(phrase_matches))

    def test_match_exact_single_phrase_begin_and_end(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            0, ['ventilate'], self.rpdr_note, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(1, len(phrase_matches))
        phrase_match = phrase_matches[0]
        self.assertEqual(1, phrase_match.extracted_value)

    def test_match_space_surround1(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'}, ' ventilate')
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            0, ['ventilate'], rpdr_note2, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(1, len(phrase_matches))
        phrase_match = phrase_matches[0]
        self.assertEqual(1, phrase_match.extracted_value)

    def test_match_space_surround2(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'}, ' ventilate ')
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            0, ['ventilate'], rpdr_note2, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(1, len(phrase_matches))
        phrase_match = phrase_matches[0]
        self.assertEqual(1, phrase_match.extracted_value)

    def test_match_surrounded_by_punctuation_ignore_true(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'}, ' (ventilate).')
        rpdr_note2.remove_punctuation_from_note()
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            0, ['ventilate'], rpdr_note2, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(1, len(phrase_matches))
        phrase_match = phrase_matches[0]
        self.assertEqual(1, phrase_match.extracted_value)

    def test_match_surrounded_by_punctuation_ignore_true_no_space(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'}, '(ventilate).')
        rpdr_note2.remove_punctuation_from_note()
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            0, ['ventilate'], rpdr_note2, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(1, len(phrase_matches))
        phrase_match = phrase_matches[0]
        self.assertEqual(1, phrase_match.extracted_value)

    def test_match_punctuation_ignore_true(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'}, ' ventilate.')
        rpdr_note2.remove_punctuation_from_note()
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            0, ['ventilate'], rpdr_note2, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(1, len(phrase_matches))
        phrase_match = phrase_matches[0]
        self.assertEqual(1, phrase_match.extracted_value)

    def test_match_punctuation_ignore_false(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'}, ' ventilate.')
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            0, ['ventilate'], rpdr_note2, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(1, len(phrase_matches))
        phrase_match = phrase_matches[0]
        self.assertEqual(1, phrase_match.extracted_value)

    def test_match_punctuation2_ignore_false(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'}, ' ventilate?')
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            0, ['ventilate'], rpdr_note2, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(1, len(phrase_matches))
        phrase_match = phrase_matches[0]
        self.assertEqual(1, phrase_match.extracted_value)

    def test_match_beginning_punctuation_ignore_false(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'}, 'ventilate.')
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            0, ['ventilate'], rpdr_note2, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(1, len(phrase_matches))
        phrase_match = phrase_matches[0]
        self.assertEqual(1, phrase_match.extracted_value)

    def test_match_beginning_punctuation_ignore_true(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'}, 'ventilate.')
        rpdr_note2.remove_punctuation_from_note()
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            0, ['ventilate'], rpdr_note2, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(1, len(phrase_matches))
        phrase_match = phrase_matches[0]
        self.assertEqual(1, phrase_match.extracted_value)

    def test_match_beginning_punctuation2(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'}, 'ventilate?')
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            0, ['ventilate'], rpdr_note2, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(1, len(phrase_matches))
        phrase_match = phrase_matches[0]
        self.assertEqual(1, phrase_match.extracted_value)

    def test_multiple_matches_same_phrase(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'},
            'ventilate ventilate')
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            0, ['ventilate'], rpdr_note2, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(2, len(phrase_matches))
        for phrase_match in phrase_matches:
            self.assertEqual(1, phrase_match.extracted_value)

    def test_many_matches_same_phrase(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'},
            'ventilate ventilate alex alex alex ventilate, ventilate alex')
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            0, ['ventilate'], rpdr_note2, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(4, len(phrase_matches))
        for phrase_match in phrase_matches:
            self.assertEqual(1, phrase_match.extracted_value)

    def test_multiple_matches_different_phrase(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'},
            'ventilate g-tube')
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            0, ['ventilate', 'g-tube'], rpdr_note2, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(2, len(phrase_matches))
        self.assertEqual(0, phrase_matches[0].match_start)
        self.assertEqual(10, phrase_matches[0].match_end)
        for phrase_match in phrase_matches:
            self.assertEqual(1, phrase_match.extracted_value)

    def test_multiple_matches_different_phrase_punctuation_in_phrase(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'},
            'ventilate g-tube')
        phrases = ['ventilate', 'g-tube']
        phrases = [
            extract_values._remove_punctuation(phrase) for phrase in phrases]
        rpdr_note2.remove_punctuation_from_note()
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            0, phrases, rpdr_note2, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(2, len(phrase_matches))
        self.assertEqual(0, phrase_matches[0].match_start)
        self.assertEqual(10, phrase_matches[0].match_end)
        for phrase_match in phrase_matches:
            self.assertEqual(1, phrase_match.extracted_value)

    def test_extract_numerical(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'},
            'ef 2.0')
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            1, ['ef'], rpdr_note2, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(1, len(phrase_matches))
        self.assertEqual(2.0, phrase_matches[0].extracted_value)

    def test_extract_multiple_numerical(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'},
            'ef 2.0 alex alex ef 20.0')
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            1, ['ef'], rpdr_note2, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(2, len(phrase_matches))
        self.assertEqual(2.0, phrase_matches[0].extracted_value)
        self.assertEqual(20.0, phrase_matches[1].extracted_value)

    def test_extract_multiple_numerical_multiple_phrases(self):
        phrase_match_context = extract_values.PhraseMatchContexts(0, 0)
        rpdr_note2 = extract_values.RPDRNote(
            {'EMPI': 'empi1', 'MRN_Type': 'mrn_type1',
             'Report_Number': '1231', 'MRN': '1231',
             'Report_Type': 'report_type1',
             'Report_Description': 'report_description1'},
            'ef 2.0 alex alex ef 20.0 alex ejection fraction 4.0')
        note_phrase_matches = extract_values._extract_phrase_from_notes(
            1, ['ef', 'ejection fraction'], rpdr_note2, phrase_match_context)
        phrase_matches = note_phrase_matches.phrase_matches
        self.assertEqual(3, len(phrase_matches))
        self.assertEqual(2.0, phrase_matches[0].extracted_value)
        self.assertEqual(20.0, phrase_matches[1].extracted_value)
        self.assertEqual(4.0, phrase_matches[2].extracted_value)


if __name__ == '__main__':
    unittest.main()
