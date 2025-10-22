# -*- coding: utf-8 -*-
import math
from copy import deepcopy
import argparse
import sys
from collections import defaultdict
from typing import Dict

from recipe_manager import RecipeManager
from input_parser import process_input
from view import ConsoleView
from exceptions import CalculatorError
from reverse_calculator import reverse_calculate, get_max_craftable_single_item
from inventory_manager import load_inventory, save_inventory

def handle_calculate(args, recipe_manager: RecipeManager, inventory: Dict[str, float]):
    view = ConsoleView()
    try:
        # Construct the same item string format that process_input expects
        item_str = f"{args.item_name},{args.quantity}"
        inputs, categorized_prods, final_available_after_calc, trees = process_input(
            item_str, recipe_manager, inventory
        )
        view.print_recipe_tree(trees)
        view.display_summary(inputs, categorized_prods, final_available_after_calc, recipe_manager)
        save_inventory(final_available_after_calc)
    except CalculatorError as e:
        print(f"Error: {e}")

def handle_add(args, recipe_manager: RecipeManager, inventory: Dict[str, float]):
    try:
        from input_parser import fuzzy_match_item
        item_name = args.item_name
        qty = args.quantity

        all_items = recipe_manager.get_all_items()
        if item_name not in all_items:
            matches = fuzzy_match_item(item_name, all_items)
            if matches:
                print(f"Notice: '{item_name}' not found. Assuming you meant '{matches[0]}'.")
                item_name = matches[0]
            else:
                raise CalculatorError(f"Item '{item_name}' is not a valid item.")
        
        inventory[item_name] += qty
        save_inventory(inventory)
        print(f"Added {qty} of '{item_name}' to inventory.")
        view = ConsoleView()
        view.display_inventory(inventory)

    except (CalculatorError, ValueError) as e:
        print(f"Error: {e}")

def handle_clear(args, inventory: Dict[str, float]):
    if args.item_name:
        if args.item_name in inventory:
            del inventory[args.item_name]
            save_inventory(inventory)
            print(f"Item '{args.item_name}' removed from inventory.")
        else:
            print(f"Item '{args.item_name}' not found in inventory.")
    else:
        inventory.clear()
        save_inventory(inventory)
        print("Inventory cleared.")

def handle_reverse(args, recipe_manager: RecipeManager, inventory: Dict[str, float]):
    view = ConsoleView()
    
    # If --from is used, parse it and override the current inventory for this command
    if args.from_items:
        try:
            inventory = {k: float(v) for k, v in (item.split(',') for item in args.from_items.split(';'))}
        except ValueError:
            print("Error: Invalid format for --from. Expected 'Item1,qty1;Item2,qty2'")
            return

    if args.item_name:
        item_name = args.item_name
        all_items = recipe_manager.get_all_items()
        if item_name not in all_items:
            from input_parser import fuzzy_match_item
            matches = fuzzy_match_item(item_name, all_items)
            if matches:
                print(f"Notice: '{item_name}' not found. Assuming you meant '{matches[0]}'.")
                item_name = matches[0]
            else:
                raise CalculatorError(f"Item '{item_name}' is not a valid item.")

        max_craftable, missing = get_max_craftable_single_item(item_name, inventory, recipe_manager, {})
        craftable_amount = max_craftable - inventory.get(item_name, 0)

        if craftable_amount >= 1 - 1e-9:
            print(f"You can craft {view.format_float(craftable_amount)} of '{item_name}' with the given resources.")
        else:
            print(f"Cannot craft '{item_name}'.")
            if missing:
                print("Missing base resources:")
                for item, qty in missing.items():
                    print(f"  {item}: {view.format_float(qty)}")

    else:
        craftable_items = reverse_calculate(recipe_manager, inventory)
        view.display_reverse_calculation(craftable_items)

def handle_list(inventory: Dict[str, float]):
    view = ConsoleView()
    view.display_inventory(inventory)

def handle_recipe_list(recipe_manager: RecipeManager):
    view = ConsoleView()
    view.display_recipes(recipe_manager.recipes)

def parse_recipe_string(recipe_str: str) -> Tuple[Dict[str, float], Dict[str, float]]:
    """Parses a recipe string like 'in1,1;in2,2 -> out1,1' into input and output dicts."""
    try:
        inputs_str, outputs_str = recipe_str.split('->')
        
        def parse_part(part_str: str) -> Dict[str, float]:
            items = {}
            if not part_str.strip():
                return items
            for item_part in part_str.split(';'):
                parts = [p.strip() for p in item_part.split(',')]
                item_name = parts[0]
                qty = 1.0 if len(parts) == 1 else float(parts[1])
                items[item_name] = qty
            return items

        inputs = parse_part(inputs_str)
        outputs = parse_part(outputs_str)
        if not outputs:
            raise ValueError("Recipe must have at least one output.")
        return inputs, outputs

    except ValueError as e:
        raise CalculatorError(f"Invalid recipe format. Expected 'inputs -> outputs'. Error: {e}")

def handle_recipe_add(args, recipe_manager: RecipeManager):
    try:
        inputs, outputs = parse_recipe_string(args.recipe_string)
        recipe_manager.add_recipe(inputs, outputs)
        print("Recipe added successfully.")
        handle_recipe_list(recipe_manager)
    except CalculatorError as e:
        print(f"Error: {e}")

def handle_recipe_delete(args, recipe_manager: RecipeManager):
    try:
        # argparse provides 1-based index, convert to 0-based
        recipe_manager.delete_recipe(args.index - 1)
        print(f"Recipe at index {args.index} deleted successfully.")
        handle_recipe_list(recipe_manager)
    except (IndexError, CalculatorError) as e:
        print(f"Error: {e}")

def handle_help(parser: argparse.ArgumentParser, subparsers):
    print(parser.format_help())
    for command, sub_parser in subparsers.choices.items():
        print(f"--- {command} ---")
        print(sub_parser.format_help())

def start_interactive_mode(parser: argparse.ArgumentParser, subparsers):
    """Starts the interactive command loop."""
    print("Entering interactive mode. Type 'help' for commands, or 'exit' to quit.")
    while True:
        try:
            user_input = input("> ").strip()
            if user_input.lower() in ['exit', 'quit']:
                break
            if not user_input:
                continue

            # Split the input into arguments for the parser
            args_list = user_input.split()
            args = parser.parse_args(args_list)
            
            recipe_manager = RecipeManager('recipes.json')
            inventory = load_inventory()

            dispatch_command(args, recipe_manager, inventory, parser, subparsers)

        except (CalculatorError, ValueError) as e:
            print(f"Error: {e}")
        except SystemExit: # Argparse calls SystemExit on --help or error
            pass # Ignore and continue loop
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

def dispatch_command(args, recipe_manager, inventory, parser, subparsers):
    """Calls the appropriate handler based on the parsed command."""
    if args.command == 'calculate':
        if args.item_name:
            handle_calculate(args, recipe_manager, inventory)
        else:
            view = ConsoleView()
            view.display_available_items_for_calculation(recipe_manager.get_all_items())
    elif args.command == 'inventory':
        if args.inv_command == 'add':
            handle_add(args, recipe_manager, inventory)
        elif args.inv_command == 'clear':
            handle_clear(args, inventory)
        elif args.inv_command == 'list':
            handle_list(inventory)
    elif args.command == 'reverse':
        handle_reverse(args, recipe_manager, inventory)
    elif args.command == 'recipe':
        if args.recipe_command == 'list':
            handle_recipe_list(recipe_manager)
        elif args.recipe_command == 'add':
            handle_recipe_add(args, recipe_manager)
        elif args.recipe_command == 'delete':
            handle_recipe_delete(args, recipe_manager)
    elif args.command == 'help':
        handle_help(parser, subparsers)
    elif args.command == 'interactive':
        start_interactive_mode(parser, subparsers)

def main() -> None:
    parser = argparse.ArgumentParser(description="Resource Calculator", prog="main.py")
    subparsers = parser.add_subparsers(dest='command')

    # Calculate command
    calc_parser = subparsers.add_parser('calculate', help='Calculate resources for an item. If no item is provided, it lists available items.')
    calc_parser.add_argument('item_name', type=str, nargs='?', help='The name of the item to calculate.')
    calc_parser.add_argument('quantity', type=float, nargs='?', default=1.0, help='The quantity to calculate. Defaults to 1.')

    # Inventory command group
    inv_parser = subparsers.add_parser('inventory', help='Manage your available resources (inventory).')
    inv_subparsers = inv_parser.add_subparsers(dest='inv_command', required=True)
    inv_add_parser = inv_subparsers.add_parser('add', help='Add an item to your inventory.')
    inv_add_parser.add_argument('item_name', type=str, help='The name of the item to add.')
    inv_add_parser.add_argument('quantity', type=float, nargs='?', default=1.0, help='The quantity to add. Defaults to 1.')
    inv_clear_parser = inv_subparsers.add_parser('clear', help='Clear all or a specific item from inventory.')
    inv_clear_parser.add_argument('item_name', type=str, nargs='?', help='Optional: a specific item to remove.')
    inv_list_parser = inv_subparsers.add_parser('list', help='List all items in your inventory.')

    # Reverse command
    reverse_parser = subparsers.add_parser('reverse', help='Show what can be crafted from available resources.')
    reverse_parser.add_argument('item_name', type=str, nargs='?', help='Optional: a specific item to check.')
    reverse_parser.add_argument('--from', dest='from_items', type=str, help='Use a temporary inventory specified in the format "Item1,qty1;Item2,qty2"')

    # Recipe command group
    recipe_parser = subparsers.add_parser('recipe', help='Manage recipes.')
    recipe_subparsers = recipe_parser.add_subparsers(dest='recipe_command', required=True)
    recipe_subparsers.add_parser('list', help='List all available recipes.')
    recipe_add_parser = recipe_subparsers.add_parser('add', help='Add a new recipe. Format: "in1,qty;in2,qty->out1,qty"')
    recipe_add_parser.add_argument('recipe_string', type=str)
    recipe_delete_parser = recipe_subparsers.add_parser('delete', help='Delete a recipe by its index (from \'recipes list\').')
    recipe_delete_parser.add_argument('index', type=int)

    # Help command
    subparsers.add_parser('help', help='Show detailed help for all commands.')

    # Interactive command
    subparsers.add_parser('interactive', help='Enter interactive mode.')

    # If no command is given, it defaults to help
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    recipe_manager = RecipeManager('recipes.json')
    inventory = load_inventory()
    
    dispatch_command(args, recipe_manager, inventory, parser, subparsers)

if __name__ == "__main__":
    main()
