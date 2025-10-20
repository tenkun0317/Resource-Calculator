# -*- coding: utf-8 -*-
import json
from typing import Dict, List, Tuple, Optional, Set, TypedDict

EPSILON = 1e-9

class RouteInfo(TypedDict):
    index: int
    inputs: Dict[str, float]
    outputs: Dict[str, float]

class RecipeManager:
    """Manages loading, caching, and accessing recipe data."""
    def __init__(self, file_path: str):
        self.recipes = self._load_recipes_from_json(file_path)
        self._all_items_cache: Optional[List[str]] = None
        self._base_resources_cache: Optional[Set[str]] = None

    def _load_recipes_from_json(self, file_path: str) -> List[Tuple[Dict[str, float], Dict[str, float]]]:
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

    def get_all_items(self) -> List[str]:
        """Returns a sorted list of all unique items mentioned in recipes."""
        if self._all_items_cache is None:
            all_items: Set[str] = set()
            for inputs, outputs in self.recipes:
                all_items.update(inputs.keys())
                all_items.update(outputs.keys())
            self._all_items_cache = sorted(list(all_items))
        return self._all_items_cache

    def get_base_resources(self) -> Set[str]:
        """Returns a set of base resources (items that can be inputs but not outputs)."""
        if self._base_resources_cache is None:
            all_items = set(self.get_all_items())
            all_outputs: Set[str] = set()
            for _, outputs in self.recipes:
                all_outputs.update(outputs.keys())
            self._base_resources_cache = all_items - all_outputs
        return self._base_resources_cache

    def find_recipes_for(self, item: str) -> List[RouteInfo]:
        """Finds all recipes that produce the given item."""
        possible_routes: List[RouteInfo] = []
        for i, (recipe_inputs, recipe_outputs) in enumerate(self.recipes):
            if item in recipe_outputs and recipe_outputs[item] > EPSILON:
                possible_routes.append({
                    "index": i,
                    "inputs": recipe_inputs,
                    "outputs": recipe_outputs
                })
        return possible_routes
