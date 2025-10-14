# -*- coding: utf-8 -*-
import math
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

# Assuming Node is defined elsewhere and will be imported, but for now, we can use a forward declaration if needed.
# from main import Node 

EPSILON = 1e-9

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

class ConsoleView:
    """Handles all console output for the application."""

    def format_float(self, value: float) -> str:
        """Formats a float for display, removing trailing zeros and converting to int if possible."""
        if abs(value) < EPSILON:
            return "0"
        if abs(value - round(value)) < EPSILON:
            return str(int(round(value)))
        else:
            return f"{value:.4f}".rstrip('0').rstrip('.')

    def _get_node_sort_priority(self, source_str: Optional[str]) -> int:
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

    def print_recipe_tree(self, nodes: List[Node]):
        """Prints the recipe tree(s) in a human-readable format."""
        print("\n--- Recipe Tree ---")
        if not nodes:
            print("  (No tree generated)")
            return

        def print_node_recursive(node: Node, prefix: str = "", is_last_child: bool = True):
            connector = "└─ " if is_last_child else "├─ "
            line = f"{prefix}{connector}{node.item} (Needed: {self.format_float(node.needed)}"

            source_info = node.source or "unknown"
            if source_info.startswith("recipe_") and node.actual_produced_by_recipe > EPSILON:
                line += f", Produced by recipe: {self.format_float(node.actual_produced_by_recipe)}"
            elif source_info == "stock" and node.produced > EPSILON:
                line += f", Used from Stock: {self.format_float(node.produced)}"
            elif node.produced > EPSILON and not source_info.startswith("recipe_"):
                line += f", Provided: {self.format_float(node.produced)}"

            line += f") [{source_info}]"
            print(line)

            new_prefix = prefix + ("    " if is_last_child else "│   ")

            sorted_children = sorted(
                node.children,
                key=lambda child: (self._get_node_sort_priority(child.source), child.item)
            )

            for i, child_node in enumerate(sorted_children):
                print_node_recursive(child_node, new_prefix, i == len(sorted_children) - 1)

        for root_node in nodes:
            print(f"\nTree for: {root_node.item} (Needed: {self.format_float(root_node.needed)}) [{root_node.source or 'unknown'}]")
            sorted_root_children = sorted(
                root_node.children,
                key=lambda child: (self._get_node_sort_priority(child.source), child.item)
            )
            for i, child_node in enumerate(sorted_root_children):
                print_node_recursive(child_node, "", i == len(sorted_root_children) - 1)

    def display_summary(self, inputs, categorized_prods, final_available_after_calc, recipe_manager):
        print("\n--- Calculation Summary ---")

        print("\nTotal base resources needed for this request:")
        base_resources_found_in_inputs = False
        for res, amt in sorted(inputs.items()):
            if res in recipe_manager.get_base_resources():
                print(f"  {res}: {self.format_float(math.ceil(amt))}")
                base_resources_found_in_inputs = True
        if not base_resources_found_in_inputs:
            print("  None")

        print("\nProducts Breakdown:")
        output_category_printed = False
        if categorized_prods.get("finished"):
            output_category_printed = True
            print("  Finished products (Requested & Produced):")
            for res, amt in sorted(categorized_prods["finished"].items()):
                print(f"    {res}: {self.format_float(amt)}")

        if categorized_prods.get("intermediate"):
            output_category_printed = True
            print("  Intermediate products (Crafted & Consumed):")
            for res, amt in sorted(categorized_prods["intermediate"].items()):
                print(f"    {res}: {self.format_float(amt)}")

        if categorized_prods.get("byproduct"):
            output_category_printed = True
            print("  Byproducts / Excess (Remaining non-base items):")
            for res, amt in sorted(categorized_prods["byproduct"].items()):
                print(f"    {res}: {self.format_float(amt)}")

        if not output_category_printed and not inputs:
            print("  No specific products generated or resources needed/remaining from this request.")
        elif not output_category_printed and inputs:
            print("  Only base inputs were consumed; no complex products generated or remaining.")

        session_available_resources = defaultdict(float, final_available_after_calc)

        print("\nUpdated available resources for next calculation (includes byproducts/excess from this run):")
        has_any_available_resources = False
        for item, amount in sorted(session_available_resources.items()):
            if amount > EPSILON:
                print(f"  {item}: {self.format_float(amount)}")
                has_any_available_resources = True
        if not has_any_available_resources:
            print("  None")

    def display_welcome_message(self, recipe_manager):
        print("Welcome to the Resource Calculator!")
        print("Enter items and quantities (e.g., 'Planks, 5; Stick, 2' or 'Wooden Pickaxe').")

        recipe_manager.get_all_items()
        recipe_manager.get_base_resources()

        print("Available items:", ", ".join(recipe_manager.get_all_items()))
        print("Base resources:", ", ".join(sorted(list(recipe_manager.get_base_resources()))))
        print("Type 'quit' to exit.")
