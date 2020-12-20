import unittest
from src.bot import is_recongized_difficulty, create_link_reference

class ReconigzedDifficulty(unittest.TestCase):
    def test_recnogized_difficulty_all(self):
        is_recognized = is_recongized_difficulty('all')
        self.assertTrue(is_recognized, 'Is not a reconigzed difficulty')

    def test_recnogized_difficulty_easy(self):
        is_recognized = is_recongized_difficulty('easy')
        self.assertTrue(is_recognized, 'Is not a reconigzed difficulty')

    def test_recnogized_difficulty_medium(self):
        is_recognized = is_recongized_difficulty('medium')
        self.assertTrue(is_recognized, 'Is not a reconigzed difficulty')

    def test_recnogized_difficulty_hard(self):
        is_recognized = is_recongized_difficulty('hard')
        self.assertTrue(is_recognized, 'Is not a reconigzed difficulty')

    def test_recnogized_difficulty_none(self):
        is_recognized = is_recongized_difficulty(None)
        self.assertFalse(is_recognized, 'Is wrongly a reconigzed difficulty')

    def test_recnogized_difficulty_uppercase_all(self):
        is_recognized = is_recongized_difficulty('ALL')
        self.assertTrue(is_recognized, 'Is not a reconigzed difficulty')

    def test_recnogized_difficulty_uppercase_easy(self):
        is_recognized = is_recongized_difficulty('EASY')
        self.assertTrue(is_recognized, 'Is not a reconigzed difficulty')

    def test_recnogized_difficulty_uppercase_medium(self):
        is_recognized = is_recongized_difficulty('MEDIUM')
        self.assertTrue(is_recognized, 'Is not a reconigzed difficulty')

    def test_recnogized_difficulty_uppercase_hard(self):
        is_recognized = is_recongized_difficulty('HARD')
        self.assertTrue(is_recognized, 'Is not a reconigzed difficulty')
