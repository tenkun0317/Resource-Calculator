import unittest
from unittest.mock import patch
import os
import sys
import io

from main import main
from inventory_manager import save_inventory, load_inventory

class TestCommands(unittest.TestCase):

    def setUp(self):
        """Ensure a clean inventory before each test."""
        self.cleanup()

    def tearDown(self):
        """Clean up the inventory file after each test."""
        self.cleanup()

    def cleanup(self):
        """Remove the inventory file if it exists."""
        if os.path.exists('inventory.json'):
            os.remove('inventory.json')

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_list_command_empty(self, mock_stdout):
        """Test the 'list' command with an empty inventory."""
        with patch.object(sys, 'argv', ['main.py', 'list']):
            main()
        output = mock_stdout.getvalue()
        self.assertIn("Current Available Resources", output)
        self.assertIn("(None)", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_list_command_with_items(self, mock_stdout):
        """Test the 'list' command with items in inventory."""
        inventory = {"Rich Air": 10, "Copper Coin": 5}
        save_inventory(inventory)
        with patch.object(sys, 'argv', ['main.py', 'list']):
            main()
        output = mock_stdout.getvalue()
        self.assertIn("Rich Air: 10", output)
        self.assertIn("Copper Coin: 5", output)

    def test_clear_all_command(self):
        """Test the 'clear' command without arguments."""
        inventory = {"Rich Air": 10}
        save_inventory(inventory)
        with patch.object(sys, 'argv', ['main.py', 'clear']):
            main()
        new_inventory = load_inventory()
        self.assertEqual(new_inventory, {})

    def test_clear_specific_item_command(self):
        """Test the 'clear' command with a specific item."""
        inventory = {"Rich Air": 10, "Copper Coin": 5}
        save_inventory(inventory)
        with patch.object(sys, 'argv', ['main.py', 'clear', 'Rich Air']):
            main()
        new_inventory = load_inventory()
        self.assertEqual(new_inventory, {"Copper Coin": 5})

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_calculate_command(self, mock_stdout):
        """Test the 'calculate' command with a single item."""
        with patch.object(sys, 'argv', ['main.py', 'calculate', 'Mana Crystal', '2']):
            main()
        output = mock_stdout.getvalue()
        self.assertIn("Total base resources needed", output)
        self.assertIn("Rich Air: 4", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_reverse_fuzzy_match(self, mock_stdout):
        """Test the 'reverse' command with a fuzzy matched item name."""
        inventory = {"Rich Air": 2}
        save_inventory(inventory)
        with patch.object(sys, 'argv', ['main.py', 'reverse', 'Mana rystal']):
            main()
        output = mock_stdout.getvalue()
        self.assertIn("Assuming you meant 'Mana Crystal'", output)
        self.assertIn("You can craft 1 of 'Mana Crystal'", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_recipes_command(self, mock_stdout):
        """Test the 'recipes' command."""
        with patch.object(sys, 'argv', ['main.py', 'recipes']):
            main()
        output = mock_stdout.getvalue()
        self.assertIn("Available Recipes", output)
        self.assertIn("-> 1 Phylactery", output) # Check for a known recipe

    def test_add_command_with_quantity(self):
        """Test the 'add' command with a specific quantity."""
        with patch.object(sys, 'argv', ['main.py', 'add', 'Rich Air', '25']):
            main()
        inventory = load_inventory()
        self.assertEqual(inventory.get("Rich Air"), 25)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_calculate_no_args(self, mock_stdout):
        """Test the 'calculate' command with no arguments, which should list all available items."""
        with patch.object(sys, 'argv', ['main.py', 'calculate']):
            main()
        output = mock_stdout.getvalue()
        self.assertIn("Available Items for Calculation", output)
        self.assertIn("Rich Air", output) # Check for a known base resource
        self.assertIn("Phylactery", output) # Check for a known craftable item

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_help_command(self, mock_stdout):
        """Test the 'help' command."""
        with patch.object(sys, 'argv', ['main.py', 'help']):
            main()
        output = mock_stdout.getvalue()
        self.assertIn("usage: main.py", output)

    @patch('argparse.ArgumentParser.print_help')
    def test_main_no_args(self, mock_print_help):
        """Test that running with no arguments prints help."""
        with patch.object(sys, 'argv', ['main.py']):
            with self.assertRaises(SystemExit):
                main()
        mock_print_help.assert_called_once()
