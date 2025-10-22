import unittest
import os
import sys
import io
from unittest.mock import patch

from main import main
from inventory_manager import save_inventory, load_inventory

class TestWorkflow(unittest.TestCase):

    def setUp(self):
        self.cleanup()

    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        if os.path.exists('inventory.json'):
            os.remove('inventory.json')

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_clear_and_calculate_workflow(self, mock_stdout):
        with patch.object(sys, 'argv', ['main.py', 'inventory', 'clear']):
            main()
        self.assertEqual(load_inventory(), {})

        with patch.object(sys, 'argv', ['main.py', 'inventory', 'add', 'Rich Air', '10']):
            main()
        self.assertEqual(load_inventory().get("Rich Air"), 10)

        with patch.object(sys, 'argv', ['main.py', 'calculate', 'Mana Crystal', '1']):
            main()
        
        output = mock_stdout.getvalue()
        self.assertIn("Rich Air: 8", output)

        final_inventory = load_inventory()
        self.assertEqual(final_inventory.get("Rich Air"), 8)
