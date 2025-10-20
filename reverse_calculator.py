# -*- coding: utf-8 -*-
from collections import defaultdict
from typing import Dict, List, Tuple, Set

from recipe_manager import RecipeManager


def get_max_craftable_single_item(item_name: str, inventory: Dict[str, float], recipe_manager: RecipeManager, memo: Dict[str, float]) -> float:
    """
    Recursively calculates the maximum craftable quantity of a single item.
    Uses memoization to avoid re-calculating for the same item.
    """
    if item_name in memo:
        return memo[item_name]

    # If the item is a base resource, the max we can "craft" is what's in inventory.
    if item_name in recipe_manager.get_base_resources():
        return inventory.get(item_name, 0)

    total_producible_from_all_routes = 0.0

    possible_routes = recipe_manager.find_recipes_for(item_name)

    # To prevent infinite recursion on loops, we'll treat the item as non-craftable for its own sub-calculations.
    memo[item_name] = inventory.get(item_name, 0)

    for route in possible_routes:
        # Determine the max number of times this recipe can be run
        max_runs_for_this_route = float('inf')

        for input_item, required_qty_per_run in route["inputs"].items():
            if required_qty_per_run <= 1e-9:
                continue
            
            # Max available for this input is inventory + what we can craft of it
            max_available_for_input = get_max_craftable_single_item(input_item, inventory, recipe_manager, memo)
            
            num_runs_possible_for_input = max_available_for_input / required_qty_per_run
            max_runs_for_this_route = min(max_runs_for_this_route, num_runs_possible_for_input)

        if max_runs_for_this_route == float('inf'):
            max_runs_for_this_route = 0

        # This route contributes this much to the item's total
        produced_qty = route["outputs"][item_name] * max_runs_for_this_route
        total_producible_from_all_routes += produced_qty

    # The total max for this item is its inventory amount + what can be crafted
    final_max = inventory.get(item_name, 0) + total_producible_from_all_routes
    memo[item_name] = final_max
    return final_max

def reverse_calculate(recipe_manager: RecipeManager, available_resources: Dict[str, float]) -> Dict[str, float]:
    """
    Calculates all craftable items and their maximum possible quantities based on available resources.

    Returns:
        A dictionary mapping craftable item names to their maximum craftable quantity.
    """
    memo: Dict[str, float] = {}
    craftable_items: Dict[str, float] = {}
    all_items = recipe_manager.get_all_items()
    base_resources = recipe_manager.get_base_resources()

    # Pre-populate memo with base resources from inventory
    for item, qty in available_resources.items():
        if item in base_resources:
            memo[item] = qty

    for item_name in all_items:
        if item_name in base_resources:
            continue

        max_qty = get_max_craftable_single_item(item_name, available_resources, recipe_manager, memo)
        
        # We only care about what we can craft, not what we already have.
        craftable_amount = max_qty - available_resources.get(item_name, 0)

        if craftable_amount > 1e-9:
            craftable_items[item_name] = craftable_amount

    return craftable_items
