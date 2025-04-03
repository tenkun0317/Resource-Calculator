# Resource-Calculator
This is a program that calculates the amount of resources needed. <br>

## Defining Recipes with the `resources` List

The `resources` variable defines all the available crafting recipes in the program. It is structured as a Python `List`.

Each element within this list represents **one specific recipe**.

---

**Structure of a Single Recipe:**

Each recipe within the `resources` list is a `Tuple` containing exactly two elements:

1.  **Input Dictionary:**
    *   The *first* element of the tuple.
    *   A `Dictionary` where:
        *   Keys are the names (string) of the input items required for this recipe.
        *   Values are the quantities (float or int) of each input item needed.
2.  **Output Dictionary:**
    *   The *second* element of the tuple.
    *   A `Dictionary` where:
        *   Keys are the names (string) of the items produced by this recipe.
        *   Values are the quantities (float or int) of each item produced.
    *   A single recipe **can produce multiple different output items** (e.g., a main product and one or more byproducts).

---

## Features to be added
- Display of possible productions from the name and number of resources
- Display list of recipes from resources
- Display list of recipes for products
- Optional recipe tree file output
