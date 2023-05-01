import random

from .constants import CARDS
from .enums import DeckColor
from .metadata import RESOURCES_DIR
from .models import Card


class Deck():
    # Override this in subclasses
    LIMIT = 0

    def __init__(self):
        self.cards = []

    def __len__(self):
        return len(self.cards)

    def __iter__(self):
        # Sort the cards by their number first, to make comparisons possible
        self.cards.sort(key=lambda x: x.ID)
        return iter(self.cards)

    def __eq__(self, value):
        it = iter(self)
        for other in value:
            try:
                mine = next(it)
            except StopIteration:
                return False
            if int(other) != int(mine):
                return False
        try:
            next(it)
            return False
        except StopIteration:
            return True

    def __contains__(self, key):
        return self.count(key) > 0

    def clear(self):
        self.cards.clear()

    def count(self, value):
        found = 0
        for card in self.cards:
            if value in (card, int(card), str(card)):
                found += 1
        return found

    def pop(self, index):
        return self.cards.pop(index)

    def remove(self, value):
        for index, card in enumerate(self.cards):
            if value in (card, int(card), str(card)):
                return self.cards.pop(index)
        raise ValueError(value)

    def append(self, value):
        if not isinstance(value, Card):
            value = CARDS[value]
        if len(self.cards) >= self.LIMIT:
            raise IndexError(self.LIMIT)
        self.cards.append(value)

    def extend(self, iterable):
        for value in iterable:
            self.append(value)

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.cards)


class MainDeck(Deck):
    LIMIT = 60


class SideDeck(Deck):
    LIMIT = 15


class ExtraDeck(Deck):
    LIMIT = 20


class InitialDeck(MainDeck):
    def __init__(self, color: DeckColor):
        super().__init__()
        rule6 = {
            DeckColor.BLACK: 3,
            DeckColor.RED: 6,
            DeckColor.GREEN: 3,
        }
        rule7 = {
            DeckColor.BLACK: 3,
            DeckColor.RED: 3,
            DeckColor.GREEN: 6,
        }
        rule8 = {
            DeckColor.BLACK: 6,
            DeckColor.RED: 3,
            DeckColor.GREEN: 3,
        }
        rules = {1: 11, 2: 1, 3: 1, 4: 1, 5: 2, 6: rule6, 7: rule7, 8: rule8, 9: 9, 10: 2, 11: 1}
        for pool, rule in rules.items():
            if isinstance(rule, dict):
                rule = rule[color]
            self.pick_cards(pool, rule)

    def pick_cards(self, pool_number, quantity):
        poolpath = RESOURCES_DIR / "pools" / "{:02d}.txt".format(pool_number)
        with poolpath.open("r") as fd:
            pool = fd.read().splitlines()
        while quantity > 0:
            card = random.choice(pool)
            self.append(card)
            pool.remove(card)
            quantity -= 1

