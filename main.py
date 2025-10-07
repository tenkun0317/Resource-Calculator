# -*- coding: utf-8 -*-
import math
from copy import deepcopy
from collections import defaultdict
from typing import Dict, Union, List, Tuple, Optional, Set
from difflib import get_close_matches

# --- Constants ---
EPSILON = 1e-9  # For floating point comparisons

# --- Node class definition ---
class Node:
    def __init__(self, item: str, needed: float, depth: int):
        self.item = item
        self.needed = needed
        self.produced = 0.0  # Amount of 'item' this node contributes to fulfilling 'needed'
        self.actual_produced_by_recipe = 0.0  # Total amount of 'item' produced by the recipe (can be > needed)
        self.source = "unknown"  # How this item was obtained (e.g., "stock", "base", "recipe_X")
        self.recipe_details: Optional[Tuple[Dict[str, float], Dict[str, float]]] = None # Inputs and outputs of the chosen recipe
        self.children: List['Node'] = []  # Child nodes representing inputs or stock usage
        self.depth = depth  # Depth in the crafting tree

    def add_child(self, child: 'Node'):
        self.children.append(child)

    def __repr__(self):
        return (f"Node({self.item}, needed={self.needed:.2f}, produced={self.produced:.2f}, "
                f"actual_produced={self.actual_produced_by_recipe:.2f}, source={self.source}, depth={self.depth})")

import json

# --- Global Variables / Helper Functions ---
def load_recipes_from_json(file_path: str) -> List[Tuple[Dict[str, float], Dict[str, float]]]:
    """Loads recipes from a JSON file and converts them to the expected format."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Convert list of {"inputs": {...}, "outputs": {...}} to list of (inputs, outputs)
        return [(item['inputs'], item['outputs']) for item in data]
    except FileNotFoundError:
        print(f"Error: Recipe file not found at '{file_path}'")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{file_path}'")
        return []

RECIPES = load_recipes_from_json('recipes.json')

_all_items_cache: Optional[List[str]] = None
_base_resources_cache: Optional[Set[str]] = None

def format_float(value: float) -> str:
    """Formats a float for display, removing trailing zeros and converting to int if possible."""
    if abs(value) < EPSILON:
        return "0"
    if abs(value - round(value)) < EPSILON:
        return str(int(round(value)))
    else:
        return f"{value:.4f}".rstrip('0').rstrip('.')

def get_all_items() -> List[str]:
    """Returns a sorted list of all unique items mentioned in RECIPES."""
    global _all_items_cache
    if _all_items_cache is None:
        all_items = set()
        for inputs, outputs in RECIPES:
            all_items.update(inputs.keys())
            all_items.update(outputs.keys())
        _all_items_cache = sorted(list(all_items))
    return _all_items_cache

def get_base_resources() -> Set[str]:
    """Returns a set of base resources (items that can be inputs but not outputs of any recipe)."""
    global _base_resources_cache
    if _base_resources_cache is None:
        all_items = set(get_all_items())
        all_outputs = set()
        for _, outputs in RECIPES:
            all_outputs.update(outputs.keys())
        _base_resources_cache = all_items - all_outputs
    return _base_resources_cache

# --- Core Calculation Logic ---
def calculate_resources(
    items: List[Tuple[str, float]],
    initial_available_resources: Optional[Dict[str, float]] = None
) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float], Dict[str, float], List[Node]]:
    """
    Calculates the resources needed for a list of items.

    Returns:
        Tuple containing:
        - aggregated_inputs: Total base resources required.
        - aggregated_outputs: Total final products produced (matching requested items).
        - final_available_resources: Resources remaining/produced after calculation.
        - aggregated_intermediates: Intermediate products crafted and consumed.
        - tree_roots: List of root nodes for the recipe trees.
    """
    available_resources = defaultdict(float, initial_available_resources or {})
    aggregated_inputs = defaultdict(float)  # Tracks total base resources needed
    aggregated_outputs = defaultdict(float) # Tracks successfully produced requested items
    aggregated_intermediates = defaultdict(float) # Tracks items crafted and consumed as part of a larger recipe
    tree_roots: List[Node] = []

    # --- Recursive function to calculate resources for a single item ---
    def recurse(
        item: str,
        qty: float,
        current_available_resources: Dict[str, float],
        processing: Set[str], # Set of items currently being processed in the recursion stack (for loop detection)
        dependency_chain: List[str], # List of items in the current dependency chain (for debugging/info)
        depth: int = 0
    ) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float], Dict[str, float], Node]:
        """
        Recursively calculates resources for a given item and quantity.

        Returns:
            Tuple containing:
            - call_inputs: Base resources consumed by this call.
            - call_outputs: Target items produced by this call.
            - call_byproducts: Byproducts generated by this call.
            - resources_after_fulfillment: State of available resources after this call.
            - current_node: The Node object representing this item in the crafting tree.
        """
        current_node = Node(item, qty, depth)

        if qty <= EPSILON:
            current_node.source = "zero_needed"
            return defaultdict(float), defaultdict(float), defaultdict(float), current_available_resources, current_node

        if item in processing:
            current_node.source = "unresolved_loop"
            return {item: qty}, defaultdict(float), defaultdict(float), current_available_resources.copy(), current_node

        new_processing = processing.copy()
        new_processing.add(item)
        new_dependency_chain = dependency_chain + [item]

        call_inputs = defaultdict(float)
        call_outputs = defaultdict(float)
        call_byproducts = defaultdict(float)

        resources_before_fulfillment = deepcopy(current_available_resources)
        resources_after_stock_use = deepcopy(resources_before_fulfillment)

        available_qty_in_stock = resources_before_fulfillment.get(item, 0)
        used_from_stock = min(available_qty_in_stock, qty)

        if used_from_stock > EPSILON:
            resources_after_stock_use[item] -= used_from_stock
            qty -= used_from_stock

            stock_node = Node(item, used_from_stock, depth + 1)
            stock_node.source = "stock"
            stock_node.produced = used_from_stock
            current_node.add_child(stock_node)
            current_node.produced += used_from_stock

        if qty <= EPSILON:
            if not current_node.source or current_node.source == "unknown":
                current_node.source = "stock_only"
            # If the entire need is met from stock, it's considered an "output" of this process.
            call_outputs[item] += current_node.produced
            return call_inputs, call_outputs, call_byproducts, resources_after_stock_use, current_node

        possible_routes = []
        for i, (recipe_inputs, recipe_outputs) in enumerate(RECIPES):
            if item in recipe_outputs and recipe_outputs[item] > EPSILON:
                possible_routes.append({
                    "index": i,
                    "inputs": recipe_inputs,
                    "outputs": recipe_outputs
                })

        if possible_routes:
            all_evaluated_route_results = []
            resources_for_recipe_evaluation_phase = resources_after_stock_use

            for route_info in possible_routes:
                recipe_index = route_info["index"]
                recipe_inputs_template = route_info["inputs"]
                recipe_outputs_template = route_info["outputs"]

                route_total_inputs_needed = defaultdict(float)
                route_total_byproducts_generated = defaultdict(float)
                route_children_nodes = []
                is_route_viable = True
                num_sub_recipe_steps = 0

                if item not in recipe_outputs_template or recipe_outputs_template[item] <= EPSILON:
                    is_route_viable = False
                    continue

                recipe_output_qty_per_run = recipe_outputs_template[item]
                scale_factor = math.ceil(qty / recipe_output_qty_per_run)
                current_resources_for_this_route = deepcopy(resources_for_recipe_evaluation_phase)

                for input_item, input_qty_per_recipe in recipe_inputs_template.items():
                    required_qty_for_input_item = input_qty_per_recipe * scale_factor

                    sub_inputs, _, sub_byproducts, resources_after_sub_call, sub_node = recurse(
                        input_item, required_qty_for_input_item, current_resources_for_this_route,
                        new_processing, new_dependency_chain, depth + 1
                    )
                    current_resources_for_this_route = resources_after_sub_call

                    if input_item in sub_inputs and input_item not in get_base_resources():
                        if sub_inputs[input_item] >= required_qty_for_input_item - EPSILON:
                            is_route_viable = False
                            break

                    for res, amount in sub_inputs.items():
                        route_total_inputs_needed[res] += amount
                    for res, amount in sub_byproducts.items():
                        route_total_byproducts_generated[res] += amount
                    route_children_nodes.append(sub_node)

                    if any(n.source.startswith("recipe_") for n in sub_node.children) or sub_node.source.startswith("recipe_"):
                        num_sub_recipe_steps += 1

                if not is_route_viable:
                    continue

                actual_produced_target_item_qty = recipe_output_qty_per_run * scale_factor
                used_target_item_qty = qty

                excess_target_item_qty = actual_produced_target_item_qty - used_target_item_qty
                if excess_target_item_qty > EPSILON:
                    route_total_byproducts_generated[item] += excess_target_item_qty

                for output_item, output_qty_per_recipe in recipe_outputs_template.items():
                    if output_item != item:
                        produced_byproduct_qty = output_qty_per_recipe * scale_factor
                        if produced_byproduct_qty > EPSILON:
                            route_total_byproducts_generated[output_item] += produced_byproduct_qty

                final_resource_state_for_this_route = defaultdict(float, resources_for_recipe_evaluation_phase)

                for res, amount in route_total_inputs_needed.items():
                    if res in get_base_resources():
                        final_resource_state_for_this_route[res] -= amount
                        if final_resource_state_for_this_route[res] < EPSILON: # Handles potential floating point inaccuracies leading to tiny negatives
                            final_resource_state_for_this_route[res] = 0

                for res, amount in route_total_byproducts_generated.items():
                    final_resource_state_for_this_route[res] += amount

                final_resource_state_for_this_route = defaultdict(float, {
                    k: v for k, v in final_resource_state_for_this_route.items() if v > EPSILON
                })

                route_score = (sum(route_total_inputs_needed.values()) * 1000) + num_sub_recipe_steps

                all_evaluated_route_results.append({
                    "score": route_score,
                    "inputs": route_total_inputs_needed,
                    "outputs": {item: used_target_item_qty},
                    "byproducts": route_total_byproducts_generated,
                    "available_after_route": dict(final_resource_state_for_this_route),
                    "recipe_index": recipe_index,
                    "children_nodes": route_children_nodes,
                    "actual_produced_by_recipe": actual_produced_target_item_qty
                })

            if all_evaluated_route_results:
                best_route_info = min(all_evaluated_route_results, key=lambda x: x["score"])

                for res, amount in best_route_info["inputs"].items():
                    call_inputs[res] += amount
                for res, amount in best_route_info["outputs"].items():
                    call_outputs[res] += amount
                for res, amount in best_route_info["byproducts"].items():
                    call_byproducts[res] += amount

                resources_after_fulfillment = defaultdict(float, best_route_info["available_after_route"])

                current_node.source = f"recipe_{best_route_info['recipe_index']}"
                current_node.recipe_details = (RECIPES[best_route_info['recipe_index']][0], RECIPES[best_route_info['recipe_index']][1])
                current_node.produced += best_route_info["outputs"].get(item, 0)
                current_node.actual_produced_by_recipe = best_route_info["actual_produced_by_recipe"]
                current_node.children.extend(best_route_info["children_nodes"])

            else:
                current_node.source = "no_viable_route"
                call_inputs[item] += qty
                resources_after_fulfillment = resources_after_stock_use

        else:
            if item in get_base_resources():
                current_node.source = "base"
                current_node.produced = qty
                current_node.actual_produced_by_recipe = qty
                call_inputs[item] += qty
                # If a base resource is "calculated", it's both an input and an output of this step.
                call_outputs[item] += qty
                resources_after_fulfillment = resources_after_stock_use
            else:
                current_node.source = "missing_recipe_or_base"
                call_inputs[item] += qty
                resources_after_fulfillment = resources_after_stock_use

        if item not in get_base_resources() and \
            current_node.source.startswith("recipe_") and \
            current_node.produced > EPSILON and \
            depth > 0:
            aggregated_intermediates[item] += current_node.produced

        return call_inputs, call_outputs, call_byproducts, dict(resources_after_fulfillment), current_node

    current_overall_available_resources = deepcopy(available_resources)
    for item_name, item_qty in items:
        inputs_for_item, outputs_for_item, _, resources_after_item_calc, top_node = recurse(
            item_name, item_qty, current_overall_available_resources,
            processing=set(), dependency_chain=[], depth=0
        )
        tree_roots.append(top_node)

        current_overall_available_resources = resources_after_item_calc
        for resource, amount in inputs_for_item.items():
            aggregated_inputs[resource] += amount
        for resource, amount in outputs_for_item.items():
            aggregated_outputs[resource] += amount

    final_inputs = {k: v for k, v in aggregated_inputs.items() if v > EPSILON}
    final_outputs = {k: v for k, v in aggregated_outputs.items() if v > EPSILON}
    final_available_resources = {k: v for k, v in current_overall_available_resources.items() if v > EPSILON}
    final_intermediates = {k: v for k, v in aggregated_intermediates.items() if v > EPSILON}

    return final_inputs, final_outputs, final_available_resources, final_intermediates, tree_roots

# --- Product Categorization ---
def categorize_products(
    outputs: Dict[str, float],
    final_available: Dict[str, float],
    intermediates_consumed: Dict[str, float],
    requested_items: List[str]
) -> Dict[str, Dict[str, float]]:
    """Categorizes products into finished, intermediate, and byproduct."""
    categories: Dict[str, Dict[str, float]] = {
        "intermediate": defaultdict(float),
        "finished": defaultdict(float),
        "byproduct": defaultdict(float)
    }
    requested_set = set(requested_items)
    base_res_set = get_base_resources()

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

# --- Input Parsing and Fuzzy Matching ---
def fuzzy_match_item(item_name: str, all_item_names: List[str]) -> Union[List[str], None]:
    """Finds close matches for an item name if an exact match isn't found."""
    matches = get_close_matches(item_name.lower(), [i.lower() for i in all_item_names], n=3, cutoff=0.6)
    if not matches:
        return None
    item_lower_map = {i.lower(): i for i in all_item_names}
    return [item_lower_map[match] for match in matches]

def process_input(
    input_str: str,
    initial_available_resources: Optional[Dict[str, float]] = None
) -> Union[Tuple[Dict[str, float], Dict[str, Dict[str, float]], Dict[str, float], List[Node]], str]:
    """Processes user input string, calculates resources, and categorizes products."""
    all_items_list = get_all_items()
    items_to_calculate: List[Tuple[str, float]] = []
    requested_item_names: List[str] = []

    initial_available_dict = initial_available_resources or {}

    try:
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
                        raise ValueError(f"Quantity for {item_name_from_input} must be positive.")
                except ValueError:
                    raise ValueError(f"Invalid quantity for {item_name_from_input}: '{parts[1]}'")
            elif len(parts) > 2:
                raise ValueError(f"Invalid format for item entry: '{item_input_part}'. Expected 'Item, Quantity' or 'Item'.")

            actual_item_name = item_name_from_input
            if item_name_from_input not in all_items_list:
                matched_items = fuzzy_match_item(item_name_from_input, all_items_list)
                if not matched_items:
                    return f"Item '{item_name_from_input}' not found, and no close matches found."
                print(f"Notice: '{item_name_from_input}' not found. Assuming you meant '{matched_items[0]}'.")
                actual_item_name = matched_items[0]

            items_to_calculate.append((actual_item_name, quantity))
            requested_item_names.append(actual_item_name)

        if not items_to_calculate:
            return "No valid items entered for calculation."

        final_inputs, final_outputs, final_available, final_intermediates, trees = calculate_resources(
            items_to_calculate, initial_available_dict
        )

        categorized_products_result = categorize_products(
            final_outputs, final_available, final_intermediates, requested_item_names
        )

        return dict(final_inputs), categorized_products_result, dict(final_available), trees

    except ValueError as e:
        return f"Input error: {str(e)}"
    except Exception as e:
        import traceback
        print(f"An unexpected error occurred during input processing: {traceback.format_exc()}")
        return f"An unexpected error occurred: {str(e)}."

# --- Output Printing ---
def _get_node_sort_priority(source_str: Optional[str]) -> int:
    """Helper for sorting nodes in the tree view."""
    if source_str is None:
        return 3
    if source_str == "stock":
        return 0
    if source_str == "base":
        return 1
    if source_str.startswith("recipe_"):
        return 2
    return 3

def print_recipe_tree(nodes: List[Node]):
    """Prints the recipe tree(s) in a human-readable format."""
    print("\n--- Recipe Tree ---")
    if not nodes:
        print("  (No tree generated)")
        return

    def print_node_recursive(node: Node, prefix: str = "", is_last_child: bool = True):
        connector = "└─ " if is_last_child else "├─ "
        line = f"{prefix}{connector}{node.item} (Needed: {format_float(node.needed)}"

        source_info = node.source or "unknown"
        if source_info.startswith("recipe_") and node.actual_produced_by_recipe > EPSILON:
            line += f", Produced by recipe: {format_float(node.actual_produced_by_recipe)}"
        elif source_info == "stock" and node.produced > EPSILON:
            line += f", Used from Stock: {format_float(node.produced)}"
        elif node.produced > EPSILON and not source_info.startswith("recipe_"):
            line += f", Provided: {format_float(node.produced)}"

        line += f") [{source_info}]"
        print(line)

        new_prefix = prefix + ("    " if is_last_child else "│   ")

        sorted_children = sorted(
            node.children,
            key=lambda child: (_get_node_sort_priority(child.source), child.item)
        )

        for i, child_node in enumerate(sorted_children):
            print_node_recursive(child_node, new_prefix, i == len(sorted_children) - 1)

    for root_node in nodes:
        print(f"\nTree for: {root_node.item} (Needed: {format_float(root_node.needed)}) [{root_node.source or 'unknown'}]")
        sorted_root_children = sorted(
            root_node.children,
            key=lambda child: (_get_node_sort_priority(child.source), child.item)
        )
        for i, child_node in enumerate(sorted_root_children):
            print_node_recursive(child_node, "", i == len(sorted_root_children) - 1)

# --- Main Program Loop ---
def main() -> None:
    """Main function to run the interactive resource calculator."""
    session_available_resources = defaultdict(float)

    print("Welcome to the Resource Calculator!")
    print("Enter items and quantities (e.g., 'Planks, 5; Stick, 2' or 'Wooden Pickaxe').")

    get_all_items()
    get_base_resources()

    print("Available items:", ", ".join(get_all_items()))
    print("Base resources:", ", ".join(sorted(list(get_base_resources()))))
    print("Type 'quit' to exit.")

    while True:
        user_input = input("\nEnter items to calculate (or 'quit'): ").strip()
        if user_input.lower() == 'quit':
            break
        if not user_input:
            continue

        calculation_result = process_input(user_input, dict(session_available_resources))

        if isinstance(calculation_result, str):
            print(f"Error: {calculation_result}")
        else:
            inputs, categorized_prods, final_available_after_calc, trees = calculation_result

            print_recipe_tree(trees)

            print("\n--- Calculation Summary ---")

            print("\nTotal base resources needed for this request:")
            base_resources_found_in_inputs = False
            for res, amt in sorted(inputs.items()):
                if res in get_base_resources():
                    print(f"  {res}: {format_float(math.ceil(amt))}")
                    base_resources_found_in_inputs = True
            if not base_resources_found_in_inputs:
                print("  None")

            print("\nProducts Breakdown:")
            output_category_printed = False
            if categorized_prods.get("finished"):
                output_category_printed = True
                print("  Finished products (Requested & Produced):")
                for res, amt in sorted(categorized_prods["finished"].items()):
                    print(f"    {res}: {format_float(amt)}")

            if categorized_prods.get("intermediate"):
                output_category_printed = True
                print("  Intermediate products (Crafted & Consumed):")
                for res, amt in sorted(categorized_prods["intermediate"].items()):
                    print(f"    {res}: {format_float(amt)}")

            if categorized_prods.get("byproduct"):
                output_category_printed = True
                print("  Byproducts / Excess (Remaining non-base items):")
                for res, amt in sorted(categorized_prods["byproduct"].items()):
                    print(f"    {res}: {format_float(amt)}")

            if not output_category_printed and not inputs:
                print("  No specific products generated or resources needed/remaining from this request.")
            elif not output_category_printed and inputs:
                print("  Only base inputs were consumed; no complex products generated or remaining.")

            session_available_resources = defaultdict(float, final_available_after_calc)

            print("\nUpdated available resources for next calculation (includes byproducts/excess from this run):")
            has_any_available_resources = False
            for item, amount in sorted(session_available_resources.items()):
                if amount > EPSILON:
                    print(f"  {item}: {format_float(amount)}")
                    has_any_available_resources = True
            if not has_any_available_resources:
                print("  None")

        print("-" * 40)

    print("Exiting program.")

if __name__ == "__main__":
    main()
