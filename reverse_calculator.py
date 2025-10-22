# -*- coding: utf-8 -*-
from collections import defaultdict
from typing import Dict, List, Tuple, Set

from recipe_manager import RecipeManager


def get_max_craftable_single_item(item_name: str, inventory: Dict[str, float], recipe_manager: RecipeManager, memo: Dict[str, Tuple[float, Dict[str, float]]]) -> Tuple[float, Dict[str, float]]:
    """
    Recursively calculates the maximum craftable quantity of a single item and any missing resources.
    Uses memoization to avoid re-calculating for the same item.
    Returns a tuple: (craftable_quantity, missing_resources_dict).
    """
    if item_name in memo:
        return memo[item_name]

    if item_name in recipe_manager.get_base_resources():
        qty_in_inv = inventory.get(item_name, 0)
        memo[item_name] = (qty_in_inv, {})
        return qty_in_inv, {}

    memo[item_name] = (inventory.get(item_name, 0), {})

    producible_qty = 0.0
    aggregated_missing = defaultdict(float)

    possible_routes = recipe_manager.find_recipes_for(item_name)
    if not possible_routes:
        missing = {item_name: 1} 
        memo[item_name] = (inventory.get(item_name, 0), missing)
        return inventory.get(item_name, 0), missing

    for route in possible_routes:
        route_missing_items = defaultdict(float)
        max_runs_for_this_route = float('inf')

        temp_inventory_for_route = inventory.copy()
        for input_item, required_qty_per_run in route["inputs"].items():
            if required_qty_per_run <= 1e-9:
                continue
            
            max_available_for_input, missing_for_input = get_max_craftable_single_item(input_item, temp_inventory_for_route, recipe_manager, memo)
            
            if max_available_for_input < required_qty_per_run:
                shortage = required_qty_per_run - max_available_for_input
                if not missing_for_input:
                     route_missing_items[input_item] += shortage
                for missing_item, missing_qty in missing_for_input.items():
                    route_missing_items[missing_item] += missing_qty * shortage

            num_runs_possible = max_available_for_input / required_qty_per_run if required_qty_per_run > 0 else float('inf')
            max_runs_for_this_route = min(max_runs_for_this_route, num_runs_possible)

        if max_runs_for_this_route == float('inf'):
            max_runs_for_this_route = 0

        if max_runs_for_this_route < 1:
            for item, qty in route_missing_items.items():
                aggregated_missing[item] += qty
        
        producible_qty += route["outputs"].get(item_name, 0) * max_runs_for_this_route

    final_qty = inventory.get(item_name, 0) + producible_qty
    final_missing = {k: v for k, v in aggregated_missing.items() if v > 1e-9}
    memo[item_name] = (final_qty, final_missing)
    
    return final_qty, final_missing

def reverse_calculate(recipe_manager: RecipeManager, available_resources: Dict[str, float]) -> Dict[str, float]:
    """
    Calculates all craftable items and their maximum possible quantities based on available resources.
    """
    memo: Dict[str, Tuple[float, Dict[str, float]]] = {}
    craftable_items: Dict[str, float] = {}
    all_items = recipe_manager.get_all_items()
    base_resources = recipe_manager.get_base_resources()

    for item, qty in available_resources.items():
        if item in base_resources:
            memo[item] = (qty, {})

    for item_name in all_items:
        if item_name in base_resources:
            continue

        max_qty, _ = get_max_craftable_single_item(item_name, available_resources, recipe_manager, memo)
        
        craftable_amount = max_qty - available_resources.get(item_name, 0)

        if craftable_amount > 1e-9:
            craftable_items[item_name] = craftable_amount

    return craftable_items
