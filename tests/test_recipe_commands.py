import unittest
import os
import json
import shutil
from unittest.mock import patch
import io
import sys

from main import main

class TestRecipeCommands(unittest.TestCase):

    RECIPE_FILE = 'recipes.json'
    RECIPE_BACKUP_FILE = 'recipes.json.bak'

    def setUp(self):
        """Backup the original recipes.json before each test."""
        if os.path.exists(self.RECIPE_FILE):
            shutil.copy(self.RECIPE_FILE, self.RECIPE_BACKUP_FILE)

    def tearDown(self):
        """Restore the original recipes.json after each test."""
        if os.path.exists(self.RECIPE_BACKUP_FILE):
            shutil.move(self.RECIPE_BACKUP_FILE, self.RECIPE_FILE)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_recipe_list(self, mock_stdout):
        """Test 'recipes list' command."""
        with patch.object(sys, 'argv', ['main.py', 'recipe', 'list']):
            main()
        output = mock_stdout.getvalue()
        self.assertIn("Available Recipes", output)
        self.assertIn("-> 1 Phylactery", output)

    def test_recipe_add(self):
        """Test 'recipes add' command."""
        recipe_str = "Wood,2;Stone,1 -> Advanced Tool,1"
        with patch.object(sys, 'argv', ['main.py', 'recipe', 'add', recipe_str]):
            main()
        
        with open(self.RECIPE_FILE, 'r') as f:
            recipes = json.load(f)
        
        new_recipe = recipes[-1]
        self.assertEqual(new_recipe['inputs'], {"Wood": 2.0, "Stone": 1.0})
        self.assertEqual(new_recipe['outputs'], {"Advanced Tool": 1.0})

    def test_recipe_delete(self):
        """Test 'recipes delete' command."""
        # First, get the original number of recipes
        with open(self.RECIPE_FILE, 'r') as f:
            original_recipes = json.load(f)
        original_length = len(original_recipes)

        # Delete the first recipe (index 1)
        with patch.object(sys, 'argv', ['main.py', 'recipe', 'delete', '1']):
            main()

        with open(self.RECIPE_FILE, 'r') as f:
            new_recipes = json.load(f)
        
        self.assertEqual(len(new_recipes), original_length - 1)
        # Check that the first recipe is gone (the old second recipe is now the first)
        self.assertEqual(new_recipes[0]['outputs'], original_recipes[1]['outputs'])
