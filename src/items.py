"""
Holds information about items, their uses, and their interactions.
Some sort of crafting system might be interesting in the future?
"""


class Item:
    def __init__(self, name, weight):
        self.name, self.names = name
        self.weight = weight