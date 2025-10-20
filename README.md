日本語: [README_ja.md](README_ja.md)

# Resource Calculator

## Overview

This tool is a powerful command-line application designed to manage resources and calculate crafting requirements for complex item production. It features an interactive mode and a suite of commands for detailed resource planning.

For items with complex crafting trees, it provides a detailed breakdown of which base materials are needed, as well as which intermediate items are produced and consumed.

## Features

-   **Interactive Command-Line Interface**: Engage with the calculator through an interactive session, or use direct commands.
-   **Resource Calculation**: Calculates the total amount of base materials needed to produce requested items, considering your current inventory.
-   **Intermediate Product Tracking**: Tracks and displays intermediate items that are crafted and consumed during the process.
-   **Byproduct and Excess Management**: Includes byproducts from recipes and items produced in excess of the required amount in its calculations.
-   **Persistent Inventory Management**: Maintain a persistent inventory of available resources (stock) across sessions.
    -   **Add Items**: Easily add items and quantities to your inventory.
    -   **Clear Items**: Remove specific items or clear your entire inventory.
    -   **List Inventory**: View all items and their quantities currently in your inventory.
-   **Reverse Crafting Calculation**: Determine what items you can craft and in what quantities based on your current inventory.
-   **Crafting Tree Visualization**: Displays the item dependencies and crafting steps in a human-readable tree format.
-   **Fuzzy Matching**: Infers the correct item name even if the input contains minor typos.
-   **External Recipe File**: Crafting recipes are dynamically loaded from the `recipes.json` file.
-   **Recipe Listing**: View all available crafting recipes directly from the command line.

## How to Use

The application uses a command-line interface with subcommands.

1.  **Run the application**:
    ```sh
    python main.py <command> [arguments]
    ```

2.  **Available Commands**:

    -   **`calculate <item_name> [quantity]`**: Calculates resources needed for an item. If no item is provided, it lists available items.
        -   Example: `python main.py calculate "Astral Sheet" 2`
        -   Example (interactive input): `python main.py calculate` (then enter `Astral Sheet, 2; Mana Crystal`)

    -   **`add <item_name> [quantity]`**: Adds an item to your available resources.
        -   Example: `python main.py add "Rich Air" 10`

    -   **`clear [item_name]`**: Clears all or a specific item from available resources.
        -   Example: `python main.py clear "Mana Crystal"`
        -   Example (clear all): `python main.py clear`

    -   **`reverse [item_name]`**: Shows what can be crafted from available resources. If an item name is provided, it shows the maximum craftable quantity for that specific item.
        -   Example: `python main.py reverse`
        -   Example (specific item): `python main.py reverse "Mana Crystal"`

    -   **`list`**: Lists all items in your available resources.
        -   Example: `python main.py list`

    -   **`recipes`**: Lists all available crafting recipes.
        -   Example: `python main.py recipes`

    -   **`interactive`**: Enters an interactive mode where you can continuously enter commands.
        -   Example: `python main.py interactive`
        -   Inside interactive mode, type `help` for a list of commands, or `exit`/`quit` to leave.

    -   **`help`**: Shows detailed help for all commands.
        -   Example: `python main.py help`

## `recipes.json` File Format

Recipes are defined in the `recipes.json` file in JSON format. The file should be an array of recipe objects.

Each recipe object must have two keys: `inputs` and `outputs`.

-   `inputs`: An object containing key-value pairs of material names and their required quantities.
-   `outputs`: An object containing key-value pairs of the items produced and their quantities.

**Example Recipe:**

```json
[
  {
    "inputs": {
      "Rich Air": 2
    },
    "outputs": {
      "Mana Crystal": 1
    }
  },
  {
    "inputs": {
      "Mana Crystal": 3
    },
    "outputs": {
      "Mana Dust": 2,
      "Liquid Curse": 1,
      "Silica Powder": 1
    }
  }
]
```

## Testing

Unit tests are located in the `tests/` directory. You can run the test suite using a test runner like `pytest` (if installed) or by running individual test files.

Example using `pytest`:

```sh
pytest
```

## Future Improvements (Ideas)

-   **Alternative Recipe Selection**: Allow users to choose between multiple crafting routes for an item.
-   **Graphical User Interface (GUI)**: Develop a more intuitive visual interface.
-   **Advanced Recipe Properties**: Incorporate crafting time, required equipment, and probabilistic production into recipes.
-   **Export Functionality**: Export calculation results to various file formats (CSV, JSON, etc.).
-   **Configuration File**: Externalize settings like the `recipes.json` path.
-   **Batch Processing**: Process a list of calculations from a file and output results to a file.