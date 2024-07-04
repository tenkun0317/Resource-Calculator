from math import ceil
from collections import defaultdict
from typing import Dict, Union, List, Tuple

from resources import resources as resources

def calculate_resources(items: List[Tuple[str, float]]) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    indent = 0
    available_resources = defaultdict(float)

    def recurse(item: str, qty: float, path: int = 0) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
        nonlocal indent, available_resources
        print("  " * indent + f"Calculating for {item} x {qty:.2f} (Path {path + 1})")
        indent += 1
        inputs = defaultdict(float)
        outputs = defaultdict(float)
        byproducts = defaultdict(float)

        if item in resources:
            recipe_inputs, recipe_outputs = resources[item][path]
            scale_factor = ceil(qty / recipe_outputs[item])

            for input_item, input_qty in recipe_inputs.items():
                required_qty = input_qty * scale_factor
                if available_resources[input_item] >= required_qty:
                    available_resources[input_item] -= required_qty
                    print("  " * indent + f"Using available {input_item}: {required_qty:.2f}")
                else:
                    additional_qty = required_qty - available_resources[input_item]
                    available_resources[input_item] = 0
                    sub_inputs, sub_outputs, sub_byproducts = recurse(input_item, additional_qty)
                    for resource, amount in sub_inputs.items():
                        inputs[resource] += amount
                    for resource, amount in sub_outputs.items():
                        outputs[resource] += amount
                        print("  " * indent + f"Added intermediate resource {resource}: {amount:.2f}")
                    for resource, amount in sub_byproducts.items():
                        byproducts[resource] += amount
                        print("  " * indent + f"Added byproduct resource {resource}: {amount:.2f}")

            for output_item, output_qty in recipe_outputs.items():
                produced_qty = output_qty * scale_factor
                if output_item != item:
                    byproducts[output_item] += produced_qty
                    available_resources[output_item] += produced_qty
                else:
                    outputs[output_item] += qty
                    excess = produced_qty - qty
                    if excess > 0:
                        outputs[output_item] += excess
                        available_resources[output_item] += excess
                        print("  " * indent + f"Added excess {output_item} to available resources: {excess:.2f}")
        else:
            inputs[item] += qty
            outputs[item] += qty
            print("  " * indent + f"Added basic resource {item}: {qty:.2f}")

        indent -= 1

        return inputs, outputs, byproducts

    final_inputs = defaultdict(float)
    final_outputs = defaultdict(float)
    final_byproducts = defaultdict(float)
    for item, number in items:
        print(f"\nProcessing {item} x {number}")
        inputs, outputs, byproducts = recurse(item, number)
        for resource, amount in inputs.items():
            final_inputs[resource] += amount
        for resource, amount in outputs.items():
            final_outputs[resource] += amount
        for resource, amount in byproducts.items():
            final_byproducts[resource] += amount

    if sum(available_resources.values()) > 0:
        print("\nRemaining available resources:")
        for resource, amount in available_resources.items():
            if amount > 0:
                print(f"  {resource}: {amount:.2f}")

    return dict(final_inputs), dict(final_outputs), dict(final_byproducts)

def categorize_products(inputs: Dict[str, float], outputs: Dict[str, float], byproducts: Dict[str, float], requested_items: List[str]) -> Dict[str, Dict[str, float]]:
    categories = {
        "intermediate": {},
        "finished": {},
        "byproduct": {}
    }

    for item in requested_items:
        if item in outputs:
            categories["finished"][item] = outputs[item]

    for item, amount in byproducts.items():
        categories["byproduct"][item] = amount

    for item, amount in outputs.items():
        if item not in requested_items and item not in inputs:
            if item in byproducts:
                if amount > byproducts[item]:
                    categories["intermediate"][item] = amount - byproducts[item]
            else:
                categories["intermediate"][item] = amount

    for category in categories:
        categories[category] = {k: v for k, v in categories[category].items() if v > 0}

    return categories

def process_input(input_str: str) -> Union[Tuple[Dict[str, float], Dict[str, Dict[str, float]]], str]:
    try:
        items = []
        for item_input in input_str.split(';'):
            item, number_str = item_input.rsplit(",", 1)
            item = item.strip()
            number = float(number_str)
            if number <= 0:
                raise ValueError(f"Quantity must be positive for {item}")
            if item not in resources and item not in set(resource for res in resources for res in resources[res] for outputs in res for resource in outputs):
                raise ValueError(f"Unknown item: {item}")
            items.append((item, number))
        inputs, outputs, byproducts = calculate_resources(items)
        categories = categorize_products(inputs, outputs, byproducts, [item for item, _ in items])
        return inputs, categories
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

def main() -> None:
    while True:
        user_input = input("Enter items and quantities (e.g., 'Iron, 5; Gold, 2') or 'quit' to exit: ").strip()
        if user_input.lower() == 'quit':
            break

        result = process_input(user_input)

        if isinstance(result, str):
            print(result)
        else:
            inputs, categorized_outputs = result
            print("\nTotal resources needed:")
            for resource, amount in sorted(inputs.items()):
                print(f"  {resource}: {amount:.2f}")

            print("\nOutputs:")
            for category in ["intermediate", "finished", "byproduct"]:
                if categorized_outputs[category]:
                    print(f"  {category.capitalize()} products:")
                    for resource, amount in sorted(categorized_outputs[category].items()):
                        print(f"    {resource}: {amount:.2f}")
        print()

if __name__ == "__main__":
    main()
