日本語: [README_ja.md](README_ja.md)

# Resource Calculator

## Overview

This tool is a command-line application that calculates the total resources required to craft specific items based on a defined set of recipes.

For items with complex crafting trees, it provides a detailed breakdown of which base materials are needed, as well as which intermediate items are produced and consumed.

## Features

- **Resource Calculation**: Calculates the total amount of base materials needed to produce the requested items.
- **Intermediate Product Tracking**: Tracks and displays intermediate items that are crafted and consumed during the process.
- **Byproduct and Excess Management**: Includes byproducts from recipes and items produced in excess of the required amount in its calculations.
- **Inventory Utilization**: Maintains a persistent inventory of available resources (stock) across sessions, which is automatically used in subsequent calculations.
- **Crafting Tree Visualization**: Displays the item dependencies and crafting steps in a human-readable tree format.
- **Fuzzy Matching**: Infers the correct item name even if the input contains minor typos.
- **External Recipe File**: Crafting recipes are dynamically loaded from the `recipes.json` file.

## How to Use

1.  Run the `main.py` script from your terminal.
    ```sh
    python main.py
    ```
2.  When the program starts, you will be prompted to enter the items and quantities you wish to calculate.
3.  Enter the required items and press Enter to see the calculation results.
4.  To exit the program, type `quit`.

## Input Format

Enter the items you want to calculate using the following format:

```
ItemName1, Quantity1; ItemName2, Quantity2
```

-   Separate an item name and its quantity with a comma `,`.
-   Separate multiple items with a semicolon `;`.
-   If the quantity is omitted, it defaults to `1`.

**Example Input:**

```
Enter items to calculate (or 'quit'): Astral Sheet, 2; Mana Crystal
```

## Output Format

The calculation result is divided into the following sections:

-   **Recipe Tree**: A tree representing the crafting dependencies and steps. It shows whether each item is sourced from a "recipe," "stock," or is a "base" material.
-   **Total base resources needed**: The total amount of base materials (items that cannot be crafted) required for the entire process.
-   **Products Breakdown**:
    -   **Finished products**: The final items requested by the user.
    -   **Intermediate products**: Items that are crafted and then consumed during the process.
    -   **Byproducts / Excess**: Extra items generated from recipes or any surplus production.
-   **Updated available resources**: A list of all resources available for the next calculation, including any byproducts from the current run.

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

Unit tests are included in `test.py`. You can run the test suite using the following command:

```sh
python test.py
```
