# -*- coding: utf-8 -*-
from typing import Dict, Union, List, Tuple, Optional
from difflib import get_close_matches

from models import Node
from recipe_manager import RecipeManager
from calculator import ResourceCalculator
from exceptions import InvalidInputError, ItemNotFoundError
from categorizer import categorize_products

def fuzzy_match_item(item_name: str, all_item_names: List[str]) -> Union[List[str], None]:
    """Finds close matches for an item name if an exact match isn't found."""
    matches = get_close_matches(item_name.lower(), [i.lower() for i in all_item_names], n=3, cutoff=0.6)
    if not matches:
        return None
    item_lower_map = {i.lower(): i for i in all_item_names}
    return [item_lower_map[match] for match in matches]

def process_input(
    input_str: str,
    recipe_manager: RecipeManager,
    initial_available_resources: Dict[str, float]
) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]], Dict[str, float], List[Node]]:
    """Processes user input string, calculates resources, and categorizes products."""
    all_items_list = recipe_manager.get_all_items()
    items_to_calculate: List[Tuple[str, float]] = []
    requested_item_names: List[str] = []

    if not input_str:
        raise InvalidInputError("No valid items entered for calculation.")

    for item_input_part in input_str.split(';'):
        item_input_part = item_input_part.strip()
        if not item_input_part:
            continue

        parts = [p.strip() for p in item_input_part.split(',')]
        item_name_from_input = parts[0]
        quantity = 1.0

        if len(parts) == 2:
            try:
                quantity = float(parts[1])
                if quantity <= 0:
                    raise InvalidInputError(f"Quantity for {item_name_from_input} must be positive.")
            except ValueError:
                raise InvalidInputError(f"Invalid quantity for {item_name_from_input}: '{parts[1]}'")
        elif len(parts) > 2:
            raise InvalidInputError(f"Invalid format for item entry: '{item_input_part}'. Expected 'Item, Quantity' or 'Item'.")

        actual_item_name = item_name_from_input
        if item_name_from_input not in all_items_list:
            matched_items = fuzzy_match_item(item_name_from_input, all_items_list)
            if not matched_items:
                raise ItemNotFoundError(item_name_from_input)
            print(f"Notice: '{item_name_from_input}' not found. Assuming you meant '{matched_items[0]}'.")
            actual_item_name = matched_items[0]

        items_to_calculate.append((actual_item_name, quantity))
        requested_item_names.append(actual_item_name)

    if not items_to_calculate:
        raise InvalidInputError("No valid items entered for calculation.")

    calculator = ResourceCalculator(recipe_manager)
    final_inputs, final_outputs, final_available, final_intermediates, trees = calculator.calculate(
        items_to_calculate, initial_available_resources
    )

    categorized_products_result = categorize_products(
        final_outputs, final_available, final_intermediates, requested_item_names, recipe_manager
    )

    return dict(final_inputs), categorized_products_result, dict(final_available), trees
