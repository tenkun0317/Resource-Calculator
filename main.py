import math
from copy import deepcopy
from collections import defaultdict
from typing import Dict, Union, List, Tuple, Optional, Set
from difflib import get_close_matches

# --- Node class definition ---
class Node:
    def __init__(self, item: str, needed: float, depth: int):
        self.item = item
        self.needed = needed
        self.produced = 0.0
        self.source = "unknown"
        self.recipe_details: Optional[Tuple[Dict[str, float], Dict[str, float]]] = None
        self.children: List['Node'] = []
        self.depth = depth

    def add_child(self, child: 'Node'):
        self.children.append(child)

    def __repr__(self):
        return f"Node({self.item}, needed={self.needed:.2f}, produced={self.produced:.2f}, source={self.source}, depth={self.depth})"

# --- Global Variables / Helper Functions ---
resources = [
    ({"Log": 1}, {"Planks": 4}),
    ({"Planks": 2}, {"Stick": 4}),
    ({"Planks": 3, "Stick": 2}, {"Wooden Pickaxe": 1}),
]
_all_items_cache: Optional[List[str]] = None
_base_resources_cache: Optional[Set[str]] = None
def get_all_items() -> List[str]:
    global _all_items_cache
    if _all_items_cache is None:
        all_items = set()
        for recipe_inputs, recipe_outputs in resources:
            all_items.update(recipe_inputs.keys())
            all_items.update(recipe_outputs.keys())
        _all_items_cache = sorted(list(all_items))
    return _all_items_cache
def get_base_resources() -> Set[str]:
    global _base_resources_cache
    if _base_resources_cache is None:
        all_items = set(get_all_items())
        all_outputs = set()
        for _, recipe_outputs in resources:
            all_outputs.update(recipe_outputs.keys())
        _base_resources_cache = all_items - all_outputs
    return _base_resources_cache

# --- calculate_resources / recurse ---
def calculate_resources(
    items: List[Tuple[str, float]],
    initial_available_resources: Dict[str, float] = None
) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float], Dict[str, float], List[Node]]:
    indent = 0
    available_resources = defaultdict(float, initial_available_resources or {})
    aggregated_inputs = defaultdict(float)
    aggregated_outputs = defaultdict(float)
    aggregated_intermediates = defaultdict(float)
    tree_roots: List[Node] = []

    base_resources = get_base_resources()


    def recurse(
        item: str,
        qty: float,
        current_available_resources: Dict[str, float],
        indent: int,
        processing: Optional[set] = None,
        dependency_chain: List[str] = [],
        depth: int = 0,
        parent_node: Optional[Node] = None
    ) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float], Dict[str, float]]:

        # --- Node Creation ---
        current_node = Node(item, qty, depth)
        if parent_node:
            parent_node.add_child(current_node)

        if processing is None: processing = set()
        if qty <= 1e-9:
            current_node.source = "zero_needed"
            current_node.produced = 0.0
            return defaultdict(float), defaultdict(float), defaultdict(float), current_available_resources

        if item in processing:
            current_node.source = "unresolved_loop"
            current_node.produced = 0.0
            loop_start_index = dependency_chain.index(item)
            unresolved_resources = dependency_chain[loop_start_index:]
            for resource in unresolved_resources:
                if resource in base_resources:
                    return {resource: qty}, defaultdict(float), defaultdict(float), current_available_resources.copy()
            return {item: qty}, defaultdict(float), defaultdict(float), current_available_resources.copy()

        new_processing = processing.copy()
        new_processing.add(item)
        new_dependency_chain = dependency_chain + [item]

        call_inputs = defaultdict(float)
        call_outputs = defaultdict(float)
        call_byproducts = defaultdict(float)
        updated_available_resources = deepcopy(current_available_resources)

        # --- Stock Use ---
        available_qty = updated_available_resources.get(item, 0)
        used_from_stock = min(available_qty, qty)

        if used_from_stock > 1e-9:
            updated_available_resources[item] -= used_from_stock
            call_outputs[item] += used_from_stock
            qty -= used_from_stock
            stock_node = Node(item, used_from_stock, depth + 1)
            stock_node.source = "stock"
            stock_node.produced = used_from_stock
            current_node.add_child(stock_node)
            current_node.produced += used_from_stock

        if qty <= 1e-9:
            current_node.source = "stock_only"
            return call_inputs, call_outputs, call_byproducts, updated_available_resources

        # --- Recipe Search ---
        routes = []
        for i, (recipe_inputs, recipe_outputs) in enumerate(resources):
            if item in recipe_outputs and recipe_outputs[item] > 1e-9:
                routes.append({"index": i, "inputs": recipe_inputs, "outputs": recipe_outputs})

        if routes:
            all_route_results = []
            candidate_children_per_route: List[List[Node]] = [[] for _ in routes]

            for route_idx, route_info in enumerate(routes):
                recipe_index = route_info["index"]
                recipe_inputs = route_info["inputs"]
                recipe_outputs = route_info["outputs"]

                route_inputs_agg = defaultdict(float)
                route_byproducts_agg = defaultdict(float)
                route_available_resources_state = deepcopy(updated_available_resources)
                sub_routes_count = 0
                possible_route = True

                recipe_output_qty = recipe_outputs[item]
                scale_factor = math.ceil(qty / recipe_output_qty)

                temp_route_available = deepcopy(route_available_resources_state)
                temp_parent_node_for_route = Node(item, qty, depth)

                for input_item, input_qty_per_recipe in recipe_inputs.items():
                    required_qty_float = input_qty_per_recipe * scale_factor
                    required_qty = required_qty_float

                    if input_item not in base_resources:
                        aggregated_intermediates[input_item] += required_qty

                    available_input_qty = temp_route_available.get(input_item, 0)
                    needed_from_production_float = required_qty - available_input_qty

                    if needed_from_production_float <= 1e-9:
                        temp_route_available[input_item] -= required_qty
                        if input_item in base_resources:
                            base_node = Node(input_item, required_qty, depth + 1)
                            base_node.source = "base_direct"
                            base_node.produced = required_qty
                            temp_parent_node_for_route.add_child(base_node)
                    else:
                        temp_route_available[input_item] = 0
                        additional_qty = needed_from_production_float

                        sub_inputs, sub_outputs_rec, sub_byproducts_rec, temp_route_available_after_rec = recurse(
                            input_item, additional_qty, temp_route_available, indent + 1, new_processing, new_dependency_chain,
                            depth=depth + 1, parent_node=temp_parent_node_for_route
                        )

                        if any(res in base_resources for res in sub_inputs):
                            pass

                        for resource, amount in sub_inputs.items():
                            route_inputs_agg[resource] += amount

                        temp_route_available = temp_route_available_after_rec
                        sub_routes_count += 1

                        for resource, amount in sub_byproducts_rec.items():
                            route_byproducts_agg[resource] += amount

                route_available_resources_state = temp_route_available

                produced_target_item_qty = recipe_output_qty * scale_factor
                used_target_item_qty = qty
                excess_target_item_qty = produced_target_item_qty - used_target_item_qty

                if excess_target_item_qty > 1e-9:
                    route_byproducts_agg[item] += excess_target_item_qty
                    route_available_resources_state[item] += excess_target_item_qty

                for output_item, output_qty_per_recipe in recipe_outputs.items():
                    if output_item != item:
                        produced_byproduct_qty = output_qty_per_recipe * scale_factor
                        if produced_byproduct_qty > 1e-9:
                            route_byproducts_agg[output_item] += produced_byproduct_qty
                            route_available_resources_state[output_item] += produced_byproduct_qty

                route_score = (sum(route_inputs_agg.values()) * 1000) + sub_routes_count
                all_route_results.append({
                    "score": route_score,
                    "inputs": route_inputs_agg,
                    "outputs": {item: qty},
                    "byproducts": route_byproducts_agg,
                    "available": route_available_resources_state,
                    "recipe_index": recipe_index,
                    "children": temp_parent_node_for_route.children
                })

            # --- Optimal route selection ---
            if all_route_results:
                best_route_info = min(all_route_results, key=lambda x: x["score"])

                for resource, amount in best_route_info["inputs"].items():
                    call_inputs[resource] += amount
                for resource, amount in best_route_info["outputs"].items():
                    call_outputs[resource] += amount
                for resource, amount in best_route_info["byproducts"].items():
                    call_byproducts[resource] += amount
                updated_available_resources = best_route_info["available"]

                # --- Tree information update ---
                current_node.source = f"recipe_{best_route_info['recipe_index']}"
                current_node.recipe_details = (resources[best_route_info['recipe_index']][0], resources[best_route_info['recipe_index']][1])
                current_node.produced += best_route_info["outputs"].get(item, 0)
                current_node.children.extend(best_route_info["children"])

            else:
                current_node.source = "no_viable_route"
                call_inputs[item] += qty

        else:
            current_node.source = "base"
            current_node.produced = qty
            call_inputs[item] += qty

        return call_inputs, call_outputs, call_byproducts, updated_available_resources

    # --- calculate_resources Main processing ---
    current_available_resources = deepcopy(available_resources)

    for item_name, item_qty in items:
        top_node = Node(item_name, item_qty, 0)
        tree_roots.append(top_node)

        inputs, outputs, byproducts, current_available_resources_after = recurse(
            item_name, item_qty, current_available_resources, indent, processing=set(),
            depth=0, parent_node=top_node
        )
        current_available_resources = current_available_resources_after
        for resource, amount in inputs.items():
            aggregated_inputs[resource] += amount
        for resource, amount in outputs.items():
            aggregated_outputs[resource] += amount

    final_inputs = dict(aggregated_inputs)
    final_outputs = dict(aggregated_outputs)
    final_available_resources = dict(current_available_resources)
    final_intermediates = dict(aggregated_intermediates)

    return final_inputs, final_outputs, final_available_resources, final_intermediates, tree_roots


# --- categorize_products ---
def categorize_products(
    inputs: Dict[str, float], outputs: Dict[str, float], final_available: Dict[str, float],
    intermediates_consumed: Dict[str, float], requested_items: List[str]
) -> Dict[str, Dict[str, float]]:
    categories = {"intermediate": defaultdict(float), "finished": defaultdict(float), "byproduct": defaultdict(float)}
    requested_set = set(requested_items)
    for item, amount in outputs.items():
        if item in requested_set and amount > 1e-9: categories["finished"][item] = amount
    for item, amount in intermediates_consumed.items():
        if amount > 1e-9: categories["intermediate"][item] = amount
    for item, amount in final_available.items():
        if amount > 1e-9: categories["byproduct"][item] = amount
    final_categories = {
        "intermediate": {k: v for k, v in categories["intermediate"].items() if v > 1e-9},
        "finished": {k: v for k, v in categories["finished"].items() if v > 1e-9},
        "byproduct": {k: v for k, v in categories["byproduct"].items() if v > 1e-9},
    }
    return final_categories

# --- fuzzy_match_item ---
def fuzzy_match_item(item: str, all_items: List[str]) -> Union[List[str], None]:
    matches = get_close_matches(item.lower(), [i.lower() for i in all_items], n=3, cutoff=0.6)
    if not matches: return None
    original_matches = []
    item_lower_map = {i.lower(): i for i in all_items}
    for match in matches: original_matches.append(item_lower_map[match])
    return original_matches

# --- process_input ---
def process_input(
    input_str: str,
    initial_available_resources: Dict[str, float] = None
) -> Union[Tuple[Dict[str, float], Dict[str, Dict[str, float]], Dict[str, float], List[Node]], str]:
    all_items = get_all_items()
    items_to_calculate = []
    requested_item_names = []
    try:
        for item_input in input_str.split(';'):
            item_input = item_input.strip()
            if not item_input: continue
            parts = [part.strip() for part in item_input.split(',')]
            item = parts[0]
            number = 1.0
            if len(parts) == 2:
                number_str = parts[1]
                try:
                    number = float(number_str)
                    if number <= 0 or number != math.floor(number): raise ValueError("Quantity must be a positive integer.")
                    number = int(number)
                except ValueError: raise ValueError(f"Quantity '{number_str}' for item '{item}' is not a valid positive integer.")
            elif len(parts) > 2: raise ValueError(f"Invalid format for '{item_input}'. Use 'Item Name, Quantity' or 'Item Name'.")
            if item not in all_items:
                matched_candidates = fuzzy_match_item(item, all_items)
                if not matched_candidates: return f"Item '{item}' not found. No similar items found."
                suggested_item = matched_candidates[0]
                print(f"Assuming '{item}' meant '{suggested_item}'")
                item = suggested_item
            items_to_calculate.append((item, float(number)))
            requested_item_names.append(item)
        if not items_to_calculate: return "No valid items entered."

        current_available = defaultdict(float, initial_available_resources or {})
        final_inputs, final_outputs, final_available_state, final_intermediates, recipe_tree_roots = calculate_resources(
            items_to_calculate, current_available
        )
        categorized_outputs = categorize_products(
            final_inputs, final_outputs, final_available_state, final_intermediates, requested_item_names
        )
        return dict(final_inputs), categorized_outputs, dict(final_available_state), recipe_tree_roots
    except ValueError as e: return f"Input error: {str(e)}"
    except Exception as e:
        import traceback
        print(f"An unexpected error occurred: {traceback.format_exc()}")
        return f"An unexpected error occurred: {str(e)}. Please check logs or contact developer."

# --- print_recipe_tree ---
def print_recipe_tree(nodes: List[Node]):
    print("\n--- Recipe Tree ---")
    if not nodes:
        print("  (No tree generated)")
        return

    def format_float(value):
        if abs(value - round(value)) < 1e-9:
            return str(int(round(value)))
        else:
            return f"{value:.2f}".rstrip('0').rstrip('.')

    def print_node(node: Node, prefix: str = "", is_last: bool = True):
        connector = "└─ " if is_last else "├─ "
        line = f"{prefix}{connector}{node.item} (Needed: {format_float(node.needed)}"
        if node.source not in ["base", "base_direct", "stock", "unresolved_loop", "zero_needed"]:
            line += f", Produced: {format_float(node.produced)}"
        line += f") [{node.source}]"
        print(line)

        new_prefix = prefix + ("    " if is_last else "│   ")
        child_count = len(node.children)
        for i, child in enumerate(node.children):
            print_node(child, new_prefix, i == child_count - 1)

    for root_node in nodes:
        print(f"\nTree for: {root_node.item} (Needed: {format_float(root_node.needed)})")
        child_count = len(root_node.children)
        for i, child in enumerate(root_node.children):
            print_node(child, "", i == child_count - 1)

# --- main ---
def main() -> None:
    available_resources_main = defaultdict(float)
    print("Welcome! Enter items and quantities (e.g., 'Iron Ingot, 5; Alloy Plate, 2').")
    get_all_items()
    get_base_resources()
    print("Available items:", ", ".join(get_all_items()))
    print("Type 'quit' to exit.")

    while True:
        user_input = input("\nEnter items: ").strip()
        if user_input.lower() == 'quit': break
        if not user_input: continue

        result = process_input(user_input, available_resources_main)

        if isinstance(result, str):
            print(f"Error: {result}")
        else:
            inputs, categorized_outputs, updated_available_resources, recipe_trees = result

            print_recipe_tree(recipe_trees)

            print("\n--- Calculation Result ---")
            print("\nTotal base resources needed:")
            if inputs:
                for resource, amount in sorted(inputs.items()):
                    int_amount = math.ceil(amount)
                    print(f"  {resource}: {int(int_amount)}")
            else: print("  None")

            print("\nOutputs:")
            has_output = False
            if categorized_outputs["intermediate"]:
                has_output = True
                print("  Intermediate products:")
                for resource, amount in sorted(categorized_outputs["intermediate"].items()):
                    if abs(amount - round(amount)) < 1e-9: print(f"    {resource}: {int(round(amount))}")
                    else: print(f"    {resource}: {amount:.4f}".rstrip('0').rstrip('.'))
            if categorized_outputs["finished"]:
                has_output = True
                print("  Finished products:")
                for resource, amount in sorted(categorized_outputs["finished"].items()):
                    int_amount = math.ceil(amount)
                    print(f"    {resource}: {int(int_amount)}")
            if categorized_outputs["byproduct"]:
                print("  Byproducts (remaining resources):")
                for resource, amount in sorted(categorized_outputs["byproduct"].items()):
                    if abs(amount - round(amount)) < 1e-9: print(f"    {resource}: {int(round(amount))}")
                    else: print(f"    {resource}: {amount:.4f}".rstrip('0').rstrip('.'))
            if not has_output and not categorized_outputs["byproduct"]: print("  None produced or remaining.")

            available_resources_main = defaultdict(float, updated_available_resources)
        print("-" * 20)

if __name__ == "__main__":
    main()
