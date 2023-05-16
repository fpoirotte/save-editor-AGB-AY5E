import itertools
import struct

from .constants import CARDS, DUELISTS
from .decks import Deck, ExtraDeck, MainDeck, SideDeck
from .enums import MonsterType


def splitter(data, size):
    index = 0
    length = len(data)
    while index + size <= length:
        yield data[index:index+size]
        index += size


class CardStats():
    PACKER = struct.Struct('<I')

    def __init__(self, card, data=None):
        self.card = card
        value = self.PACKER.unpack(data)[0] if data else 0
        self.password = bool(value & 0x20000)
        self.copiesTrunk = value & 0x3FF
        self.copiesMainExtra = (value >> 10) & 0x3
        self.copiesSide = (value >> 12) & 0x3
        self.validate()

    def validate(self):
        used = self.copiesMainExtra + self.copiesSide
        assert used <= self.card.Limit.value

    def __int__(self):
        return self.copiesTrunk + self.copiesMainExtra + self.copiesSide

    def __repr__(self):
        fmt = "<CardStats<{}> (Trunk: {}, Main: {}, Side: {})"
        return fmt.format(self.card, self.copiesTrunk, self.copiesMainExtra, self.copiesSide)

    def __str__(self):
        return str(self.card)

    def __bytes__(self):
        # (u32) counts + flags1
        #     0-9 = # of copies in the trunk
        #     10-11 = # of copies in main deck/extra deck
        #     12-13 = # of copies in side deck
        #     14-16 = ?
        #     17 = 1 if password has been used already, 0 otherwise
        #     18-31 = ?
        return self.PACKER.pack(
            (self.copiesTrunk & 0x3FF) |
            ((self.copiesMainExtra & 0x3) << 10) |
            ((self.copiesSide & 0x3) << 12) |
            (int(bool(self.password)) << 17)
        )


class CardsStats():
    def __init__(self, data=None):
        it = itertools.repeat(None) if not data else splitter(data, CardStats.PACKER.size)
        self.cards = [CardStats(card, next(it)) for card in CARDS.values()]

    def reset_deck(self, deck: Deck):
        self.cards = [CardStats(card) for card in CARDS.values()]
        for card in deck:
            self.cards[card.ID].copiesMainExtra += 1

    def move_to_trunk(self):
        moved = 0
        for card in self.cards:
            copies = card.copiesMainExtra
            card.copiesMainExtra = 0
            card.copiesTrunk += copies
            moved += copies

            copies = card.copiesSide
            card.copiesSide = 0
            card.copiesTrunk += copies
            moved += copies
        return moved

    def __iter__(self):
        return iter(self.cards)

    def __int__(self):
        return sum(card.copiesTrunk for card in self.cards)

    def __getitem__(self, key):
        return self.cards[int(CARDS[key])]

    def as_decks(self):
        main = MainDeck()
        extra = ExtraDeck()
        side = SideDeck()

        for card in self.cards:
            target = extra if card.card.MonsterType == MonsterType.FUSION else main
            for i in range(card.copiesMainExtra):
                target.append(card.card)
            for i in range(card.copiesSide):
                side.append(card.card)
        return main, extra, side

    def __bytes__(self):
        return b''.join(bytes(value) for value in self)


class DuelistStats():
    PACKER = struct.Struct('<I')

    def __init__(self, duelist, data=None):
        self.duelist = duelist
        value = self.PACKER.unpack(data)[0] if data else 0
        self.won = value & 0x7FF
        self.drawn = (value >> 11) & 0x7FF
        self.lost = (value >> 22) & 0x3FF

    def __str__(self):
        return str(self.duelist)

    def __int__(self):
        return ((self.drawn & 0x3FF) << 22) + ((self.lost & 0x7FF) << 11) + (self.won & 0x7FF)

    def __bytes__(self):
        # (u32) stats
        #     0-10  = won
        #     11-21 = lost
        #     22-31 = drawn
        return self.PACKER.pack(
            (self.won & 0x7FF) |
            ((self.lost & 0x7FF) << 11) |
            ((self.drawn & 0x3FF) << 22)
        )


class DuelistsStats():
    def __init__(self, data=None):
        it = itertools.repeat(None) if not data else splitter(data, DuelistStats.PACKER.size)
        self.duelists = [DuelistStats(duelist, next(it)) for duelist in DUELISTS.values()]

    def __iter__(self):
        return iter(self.duelists)

    def __getitem__(self, key):
        return self.duelists[int(DUELISTS[key])-1]

    def __bytes__(self):
        return b''.join(bytes(value) for value in self)

