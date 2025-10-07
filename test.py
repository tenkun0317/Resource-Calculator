
import unittest
from unittest.mock import patch
import main

class TestResourceCalculator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Load recipes once for all tests."""
        # Load recipes from the actual file to ensure tests run against real data
        main.RECIPES = main.load_recipes_from_json('recipes.json')
        # Reset caches to ensure clean state for testing
        main._all_items_cache = None
        main._base_resources_cache = None
        main.get_all_items()
        main.get_base_resources()

    def test_simple_craft_mana_crystal(self):
        """Test crafting Mana Crystal from Rich Air."""
        # Recipe: 2 Rich Air -> 1 Mana Crystal
        result = main.process_input("Mana Crystal, 1")
        self.assertNotIsInstance(result, str, "Processing failed")
        inputs, categorized_prods, final_available, _ = result
        
        self.assertEqual(inputs, {"Rich Air": 2})
        self.assertEqual(categorized_prods.get("finished"), {"Mana Crystal": 1})
        self.assertFalse(categorized_prods.get("intermediate"))
        self.assertFalse(categorized_prods.get("byproduct"))
        self.assertEqual(final_available, {})

    def test_multi_step_craft_astral_sheet(self):
        """Test a more complex craft like Astral Sheet."""
        result = main.process_input("Astral Sheet, 1")
        self.assertNotIsInstance(result, str, "Processing failed")
        inputs, categorized_prods, final_available, _ = result

        # Check that some base resources are required.
        # The exact amount can be complex, so we just check for their presence.
        self.assertIn("Rich Air", inputs)
        self.assertIn("Silver Coin", inputs)
        self.assertIn("Copper Coin", inputs)
        self.assertIn("Gold Coin", inputs)

        self.assertEqual(categorized_prods.get("finished"), {"Astral Sheet": 1})
        
        # Check for some of the expected intermediate products
        intermediates = categorized_prods.get("intermediate", {})
        self.assertIn("Pure Mana Gem", intermediates)
        self.assertIn("Adamantine Bar", intermediates)
        self.assertIn("Bright Shard", intermediates)

    def test_with_initial_stock(self):
        """Test calculation with some resources already available in stock."""
        # To craft 1 Mana Crystal, 2 Rich Air are needed. We provide 1 from stock.
        initial_stock = {"Rich Air": 1}
        result = main.process_input("Mana Crystal, 1", initial_available_resources=initial_stock)
        self.assertNotIsInstance(result, str, "Processing failed")
        inputs, _, final_available, _ = result
        
        # The calculation should only require 1 additional Rich Air.
        self.assertEqual(inputs, {"Rich Air": 1})
        # The initial stock should be consumed, so final_available is empty.
        self.assertEqual(final_available, {})

    def test_byproducts_and_excess(self):
        """Test that byproducts and excess from recipes are correctly calculated."""
        # Recipe: 3 Mana Crystal -> 2 Mana Dust, 1 Liquid Curse, 1 Silica Powder
        # We need 3 Mana Crystals for this. 1 Mana Crystal needs 2 Rich Air. So, 6 Rich Air total.
        result = main.process_input("Mana Dust, 2")
        self.assertNotIsInstance(result, str, "Processing failed")
        inputs, categorized_prods, final_available, _ = result

        self.assertEqual(inputs, {"Rich Air": 6})
        self.assertEqual(categorized_prods.get("finished"), {"Mana Dust": 2})
        
        # The byproducts should appear in the final_available resources.
        self.assertIn("Liquid Curse", final_available)
        self.assertIn("Silica Powder", final_available)
        self.assertAlmostEqual(final_available["Liquid Curse"], 1.0)
        self.assertAlmostEqual(final_available["Silica Powder"], 1.0)

    def test_invalid_item_name(self):
        """Test input with an item name that does not exist."""
        result = main.process_input("NonExistentItem, 1")
        self.assertIsInstance(result, str)
        self.assertIn("not found", result)

    def test_fuzzy_match_for_item_name(self):
        """Test the fuzzy matching for a misspelled item name."""
        # "Mana rystal" is a typo but close to "Mana Crystal".
        with patch('builtins.print') as mock_print:
            result = main.process_input("Mana rystal, 1")
            self.assertNotIsInstance(result, str, "Processing failed")
            inputs, _, _, _ = result
            self.assertEqual(inputs, {"Rich Air": 2})
            # Check that the user was notified about the fuzzy match assumption.
            mock_print.assert_any_call("Notice: 'Mana rystal' not found. Assuming you meant 'Mana Crystal'.")

    def test_base_resource_request(self):
        """Test requesting a base resource directly, which should just pass through."""
        result = main.process_input("Rich Air, 10")
        self.assertNotIsInstance(result, str, "Processing failed")
        inputs, categorized_prods, _, _ = result
        
        self.assertEqual(inputs, {"Rich Air": 10})
        # Requesting a base resource is considered producing a "finished" good in this context.
        self.assertEqual(categorized_prods.get("finished"), {"Rich Air": 10})

    def test_full_integration_phylactery(self):
        """Test the most complex item, 'Phylactery', as a full integration test."""
        result = main.process_input("Phylactery, 1")
        self.assertNotIsInstance(result, str, "Processing failed")
        _, categorized_prods, final_available, _ = result

        self.assertEqual(categorized_prods.get("finished"), {"Phylactery": 1})
        
        # Check for key high-level intermediates
        intermediates = categorized_prods.get("intermediate", {})
        self.assertIn("Elemental Chassis", intermediates)
        self.assertIn("Immacurate Soul", intermediates)
        self.assertIn("Energized Spark", intermediates)
        
        # Check that there are byproducts/excess materials left over.
        self.assertTrue(len(final_available) > 0, "Expected byproducts or excess materials, but none were found.")
        self.assertIn("Vial of Blood", final_available) # This is a common byproduct in the chain

if __name__ == '__main__':
    unittest.main()
