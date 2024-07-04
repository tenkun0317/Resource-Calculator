# Resource-Calculater
This is a program that calculates the amount of resources needed.
A dictionary called resources is needed in a file called resources.py. (The name can be changed internally.)

## Example of how to write a `resources` dictionary
Shown below is an example of a dictionary that defines a recipe for a resource.This dictionary defines the product, the input materials required for its manufacture, and the output materials produced.
```
resources = {
    "Planks": [
        ({"Log": 1}, {"Planks": 4})
    ],
    "Stick": [
        ({"Planks": 2}, {"Stick": 4})
    ],
    "Wooden Pickaxe": [
        ({"Planks": 3, "Stick": 2}, {"Wooden Pickaxe": 1})
    ],
    "Ladder": [
        ({"Stick": 7}, {"Ladder": 3})
    ]
}
```

### Meaning of each key and value
- Key: The name of the product (e.g., `"Planks"`, `"Stick"`, `"Wooden Pickaxe"`, `"Ladder"`).
- Value: a list, where each element is a tuple.
- First element of the tuple: a dictionary of input materials needed to create the product.
- Second element of the tuple: a dictionary representing the output product to be created.

For example, in the case of `Wooden Pickaxe`, the product name is `Wooden Pickaxe`, the input materials are three `Planks` and two `Sticks`, and the output product is one `Wooden Pickaxe`.
You may have any number of both inputs and outputs.

## Features to be added
- Reverse lookup from finished product
