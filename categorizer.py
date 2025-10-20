# -*- coding: utf-8 -*-
from collections import defaultdict
from typing import Dict, List

from recipe_manager import RecipeManager

EPSILON = 1e-9

def categorize_products(
    outputs: Dict[str, float],
    final_available: Dict[str, float],
    intermediates_consumed: Dict[str, float],
    requested_items: List[str],
    recipe_manager: RecipeManager
) -> Dict[str, Dict[str, float]]:
    """Categorizes products into finished, intermediate, and byproduct."""
    categories: Dict[str, Dict[str, float]] = {
        "intermediate": defaultdict(float),
        "finished": defaultdict(float),
        "byproduct": defaultdict(float)
    }
    requested_set = set(requested_items)
    base_res_set = recipe_manager.get_base_resources()

    for item, amount in outputs.items():
        if item in requested_set and amount > EPSILON:
            categories["finished"][item] += amount

    for item, amount in intermediates_consumed.items():
        if amount > EPSILON:
            categories["intermediate"][item] += amount

    for item, final_amount in final_available.items():
        if final_amount <= EPSILON or item in base_res_set:
            continue

        amount_as_finished = categories["finished"].get(item, 0)

        if item not in categories["finished"]:
            categories["byproduct"][item] = final_amount
        else:
            excess_over_finished = final_amount - amount_as_finished 
            if excess_over_finished > EPSILON:
                categories["byproduct"][item] += excess_over_finished

    return {
        cat_name: {item: amount for item, amount in cat_dict.items() if amount > EPSILON}
        for cat_name, cat_dict in categories.items()
    }
