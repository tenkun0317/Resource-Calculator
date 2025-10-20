# -*- coding: utf-8 -*-
from typing import Dict, List, Optional, Tuple

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
