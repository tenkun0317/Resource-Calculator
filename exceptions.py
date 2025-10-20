# -*- coding: utf-8 -*-

class CalculatorError(Exception):
    """Base exception for this application."""
    pass

class ItemNotFoundError(CalculatorError):
    """Raised when an item is not found in recipes."""
    def __init__(self, item_name):
        self.item_name = item_name
        super().__init__(f"Item '{item_name}' not found, and no close matches found.")

class InvalidInputError(CalculatorError):
    """Raised for malformed user input."""
    pass
