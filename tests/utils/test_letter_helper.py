import unittest
from app.utils.letter_helper import LetterHelper

class TestLetterHelper(unittest.TestCase):

    ## Date Extraction Tests
    def test_extract_date_valid_key(self):
        key = "fmb-1839-04-23-01"
        self.assertEqual(LetterHelper.extract_date_from_key(key), "1839-04-23")

    def test_extract_date_invalid_key(self):
        key = "some-random-text-without-date"
        self.assertEqual(LetterHelper.extract_date_from_key(key), "Unknown Date")

    ## Sentence Splitting Tests
    def test_basic_splitting(self):
        text = "Das ist der erste Satz. Und das ist der zweite!"
        result = LetterHelper.split_into_sentences(text)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "Das ist der erste Satz.")

    def test_abbreviation_protection_vm(self):
        # Testing "v. M." (vom letzten Monat) protection
        text = "Ihr Schreiben v. M. habe ich erhalten. Es war sehr erfreulich."
        result = LetterHelper.split_into_sentences(text)
        # Should NOT split after 'v.' or 'M.' if followed by a space
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "Ihr Schreiben v. M. habe ich erhalten.")

    def test_title_protection(self):
        # Testing "Dr." and "Prof." protection
        text = "Ich sprach mit Dr. Mendelssohn. Er war in Leipzig."
        result = LetterHelper.split_into_sentences(text)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "Ich sprach mit Dr. Mendelssohn.")

    def test_work_reference_protection(self):
        # Testing "op." or "No." (Musical works)
        text = "Wir spielten sein Quartet op. 44. Es klang wunderbar."
        result = LetterHelper.split_into_sentences(text)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "Wir spielten sein Quartet op. 44.")

    def test_no_split_on_lowercase(self):
        # Sentences usually start with Uppercase. 
        # A period followed by lowercase is often an abbreviation.
        text = "Dies ist ein Test. dieser Teil sollte nicht getrennt werden."
        result = LetterHelper.split_into_sentences(text)
        # Because of (?=[A-Z0-9]), it should not split here
        self.assertEqual(len(result), 1)

if __name__ == '__main__':
    unittest.main()
