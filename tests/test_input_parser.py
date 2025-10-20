import unittest
import os
from unittest.mock import patch

from recipe_manager import RecipeManager
from input_parser import process_input
from exceptions import ItemNotFoundError, InvalidInputError

class TestInputParser(unittest.TestCase):

    def setUp(self):
        """Set up a recipe manager for each test."""
        self.recipe_manager = RecipeManager('recipes.json')

    def tearDown(self):
        """Clean up the inventory file after each test."""
        if os.path.exists('inventory.json'):
            os.remove('inventory.json')

    def test_invalid_item_name(self):
        """Test input with an item name that does not exist."""
        with self.assertRaises(ItemNotFoundError):
            process_input("NonExistentItem, 1", self.recipe_manager, {})

    def test_invalid_input_format(self):
        """Test input with malformed syntax."""
        with self.assertRaises(InvalidInputError):
            process_input("Item, 1, extra", self.recipe_manager, {})
        with self.assertRaises(InvalidInputError):
            process_input("Item, -5", self.recipe_manager, {})
        with self.assertRaises(InvalidInputError):
            process_input("Item, abc", self.recipe_manager, {})

    def test_fuzzy_match_for_item_name(self):
        """Test the fuzzy matching for a misspelled item name."""
        # "Mana rystal" is a typo but close to "Mana Crystal".
        with patch('builtins.print') as mock_print:
            result = process_input("Mana rystal, 1", self.recipe_manager, {})
            self.assertNotIsInstance(result, str, "Processing failed")
            inputs, _, _, _ = result
            self.assertEqual(inputs, {"Rich Air": 2})
            # Check that the user was notified about the fuzzy match assumption.
            mock_print.assert_any_call("Notice: 'Mana rystal' not found. Assuming you meant 'Mana Crystal'.")
