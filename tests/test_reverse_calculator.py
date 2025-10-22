import unittest
import os
from unittest.mock import patch
import io
import sys

from recipe_manager import RecipeManager
from reverse_calculator import reverse_calculate
from main import main

class TestReverseCalculator(unittest.TestCase):

    def setUp(self):
        """Set up a recipe manager for each test."""
        self.recipe_manager = RecipeManager('recipes.json')

    def tearDown(self):
        """Clean up the inventory file after each test."""
        if os.path.exists('inventory.json'):
            os.remove('inventory.json')

    def test_reverse_calculate_empty_inventory(self):
        """Test reverse calculation with no resources."""
        inventory = {}
        result = reverse_calculate(self.recipe_manager, inventory)
        self.assertEqual(result, {})

    def test_reverse_calculate_simple_recipe(self):
        """Test with enough resources for a simple item."""
        # 2 Rich Air -> 1 Mana Crystal
        inventory = {"Rich Air": 4}
        result = reverse_calculate(self.recipe_manager, inventory)
        self.assertIn("Mana Crystal", result)
        self.assertAlmostEqual(result["Mana Crystal"], 2)

    def test_reverse_calculate_multi_step(self):
        """Test a multi-step craft."""
        # 5 Weak Mana Gem -> 1 Pure Mana Gem
        # 2 Mana Dust, 1 Silica Powder -> 1 Weak Mana Gem
        # 3 Mana Crystal -> 2 Mana Dust, 1 Liquid Curse, 1 Silica Powder
        # 2 Rich Air -> 1 Mana Crystal
        inventory = {"Rich Air": 60} # Enough for 30 Mana Crystal -> 20 Mana Dust, 10 Silica Powder -> 10 Weak Mana Gem -> 2 Pure Mana Gem
        result = reverse_calculate(self.recipe_manager, inventory)
        
        self.assertIn("Pure Mana Gem", result)
        self.assertAlmostEqual(result["Pure Mana Gem"], 2)
        self.assertIn("Weak Mana Gem", result)
        self.assertAlmostEqual(result["Weak Mana Gem"], 10)

    def test_reverse_calculate_with_partial_intermediates(self):
        """Test with some intermediate items already in inventory."""
        # 5 Weak Mana Gem -> 1 Pure Mana Gem
        inventory = {"Weak Mana Gem": 3, "Rich Air": 12} # Can make 6 Mana Crystal -> 4 Mana Dust, 2 Silica -> 2 Weak Mana Gem. Total 5.
        result = reverse_calculate(self.recipe_manager, inventory)
        self.assertIn("Pure Mana Gem", result)
        self.assertAlmostEqual(result["Pure Mana Gem"], 1)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_reverse_from_option(self, mock_stdout):
        """Test the 'reverse --from' command."""
        with patch.object(sys, 'argv', ['main.py', 'reverse', '--from', 'Rich Air,4']):
            main()
        output = mock_stdout.getvalue()
        self.assertIn("Mana Crystal: 2", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_reverse_missing_resources(self, mock_stdout):
        """Test the 'reverse' command for an uncraftable item to see missing resources."""
        with patch.object(sys, 'argv', ['main.py', 'reverse', 'Pure Mana Gem']):
            main()
        output = mock_stdout.getvalue()
        self.assertIn("Cannot craft 'Pure Mana Gem'", output)
        self.assertIn("Missing base resources:", output)
        self.assertIn("Rich Air", output)
