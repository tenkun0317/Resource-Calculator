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

        max_craftable = get_max_craftable_single_item(item_name, inventory, recipe_manager, {})
        craftable_amount = max_craftable - inventory.get(item_name, 0)
        print(f"You can craft {view.format_float(craftable_amount)} of '{item_name}' with your current resources.")
    else:
        craftable_items = reverse_calculate(recipe_manager, inventory)
        view.display_reverse_calculation(craftable_items)

def handle_list(inventory: Dict[str, float]):
    view = ConsoleView()
    view.display_inventory(inventory)

def handle_recipes(recipe_manager: RecipeManager):
    view = ConsoleView()
    view.display_recipes(recipe_manager.recipes)

def handle_help(parser: argparse.ArgumentParser, subparsers):
    """Display a formatted help message with improved layout."""
    print(parser.format_help())
    # for command, sub_parser in subparsers.choices.items():
    #     print(f"--- {command} ---")
    #     print(sub_parser.format_help())

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
    elif args.command == 'add':
        handle_add(args, recipe_manager, inventory)
    elif args.command == 'clear':
        handle_clear(args, inventory)
    elif args.command == 'reverse':
        handle_reverse(args, recipe_manager, inventory)
    elif args.command == 'list':
        handle_list(inventory)
    elif args.command == 'recipes':
        handle_recipes(recipe_manager)
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

    # Add command
    add_parser = subparsers.add_parser('add', help='Add an item to your available resources.')
    add_parser.add_argument('item_name', type=str, help='The name of the item to add.')
    add_parser.add_argument('quantity', type=float, nargs='?', default=1.0, help='The quantity to add. Defaults to 1.')

    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear all or a specific item from available resources.')
    clear_parser.add_argument('item_name', type=str, nargs='?', help='Optional: a specific item to remove.')

    # Reverse command
    reverse_parser = subparsers.add_parser('reverse', help='Show what can be crafted from available resources.')
    reverse_parser.add_argument('item_name', type=str, nargs='?', help='Optional: a specific item to check.')

    # List command
    list_parser = subparsers.add_parser('list', help='List all items in your available resources.')

    # Recipes command
    recipes_parser = subparsers.add_parser('recipes', help='List all available recipes.')

    # Help command
    help_parser = subparsers.add_parser('help', help='Show detailed help for all commands.')

    # Interactive command
    interactive_parser = subparsers.add_parser('interactive', help='Enter interactive mode.')

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
