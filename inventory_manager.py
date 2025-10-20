# -*- coding: utf-8 -*-
import json
from collections import defaultdict
from typing import Dict

INVENTORY_FILE = 'inventory.json'

def load_inventory() -> defaultdict[str, float]:
    """Loads the inventory from the JSON file."""
    try:
        with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
            # The keys are item names (str), and values are quantities (float).
            data: Dict[str, float] = json.load(f)
            return defaultdict(float, data)
    except (FileNotFoundError, json.JSONDecodeError):
        return defaultdict(float)

def save_inventory(inventory: Dict[str, float]):
    """Saves the inventory to the JSON file."""
    with open(INVENTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, indent=2, sort_keys=True)
