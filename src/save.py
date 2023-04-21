import itertools
import struct

from datetime import date, timedelta

from constants import *
from deck import Deck, MainDeck, ExtraDeck, SideDeck
from enums import NextNationalChampionshipRound, MonsterType
from models import Card


__all__ = ('Save', )


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
        self.copiesTrunk = value & 0x3F
        self.copiesMainExtra = (value >> 10) & 0x3F
        self.copiesSide = (value >> 12) & 0x3F
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
        #     0-9 = nb dans le trunk
        #     10-11 = nb dans le main deck, y.c. fusions
        #     12-13 = nb dans le side deck
        #     14-16 = ?
        #     17 = password used
        #     18-31 = ?
        return self.PACKER.pack(
            (self.copiesTrunk & 0x3F) |
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
            self.cards[card.ID-1].copiesMainExtra += 1

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
        return self.cards[int(CARDS[key])-1]

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
        self.won = value & 0x7F
        self.drawn = (value >> 11) & 0x7F
        self.lost = (value >> 22) & 0x3F

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
            (self.won & 0x7F) |
            ((self.lost & 0x7F) << 11) |
            ((self.drawn & 0x3F) << 22)
        )


class DuelistsStats():
    def __init__(self, data=None):
        it = itertools.repeat(None) if not data else splitter(data, DuelistStats.PACKER.size)
        self.duelists = [DuelistStats(duelist, next(it)) for duelist in DUELISTS]

    def __iter__(self):
        return iter(self.duelists)

    def __getitem__(self, key):
        return self.duelists[int(DUELISTS[key])-1]

    def __bytes__(self):
        return b''.join(bytes(value) for value in self)


class Save():
    """
    0000-000B = header (u32[3] = {0, 1, 0})
    000C-0CDC = cards stats (u32[820])
    0CDD-2007 = 0x00... (padding)
    2008-207F = card IDs for main deck (u16[60])
    2080-209D = card IDs for side deck (u16[15])
    209E-20C5 = card IDs for extra deck / fusions (u16[20])
    20C6-20C7 = number of cards in trunk (u16)
    20C8-20C9 = number of cards in main deck (u16)
    20CA-20CB = number of cards in side deck (u16)
    20CC-20CD = number of cards in extra deck / fusions (u16)
    20CE-20D3 = 0x00... (padding)
    20D4-2133 = duel stats (u32[24])
    2134-214F = ?
    2150-2151 = in-game days (u16)
    2152-2153 = 0x3 (u16 ?)
    2154-2157 = ? (u32 ?)
    2158-215B = ? (u32 ?)
    215C-215D = ? (u16 ?)
    215E-2161 = national championship (u32 ?)
    2162-2165 = 0x00... (padding)
    2166-216D = "DMEX1INT" (Duel Monsters Expert 1 - International version)
    216E-216F = checksum (u16)
    2170-7FFF = 0xFF... (padding)
    """
    STARTING_DATE = date(2001, 1, 1)

    def __init__(self, data=None, filename=None):
        self.cardsStats = CardsStats(data[OFFSET_STATS_CARDS:] if data else None)
        self.duelistsStats = DuelistsStats(data[OFFSET_STATS_DUELISTS:] if data else None)
        self.ingameDate = date(self.STARTING_DATE.year, self.STARTING_DATE.month, self.STARTING_DATE.day)
        self.nextNationalChampionshipRound = NextNationalChampionshipRound.ROUND_1
        self.filename = filename

        if data:
            mainDeck = MainDeck()
            extraDeck = ExtraDeck()
            sideDeck = SideDeck()

            nbTrunkCards, nbMainCards, nbSideCards, nbExtraCards = struct.unpack('<4H', data[OFFSET_NB_CARDS_TOTAL:OFFSET_PADDING_2])
            mainDeck.extend(struct.unpack_from('<{}H'.format(nbMainCards), data[OFFSET_CARDS_MAIN:OFFSET_CARDS_MAIN + 2*nbMainCards]))
            sideDeck.extend(struct.unpack_from('<{}H'.format(nbSideCards), data[OFFSET_CARDS_SIDE:OFFSET_CARDS_SIDE + 2*nbSideCards]))
            extraDeck.extend(struct.unpack_from('<{}H'.format(nbExtraCards), data[OFFSET_CARDS_MAIN:OFFSET_CARDS_EXTRA + 2*nbExtraCards]))

            daysElapsed = struct.unpack('<H', data[OFFSET_DAYS_ELAPSED:OFFSET_STATIC])[0]
            self.ingameDate += timedelta(days=daysElapsed)
            nextNationalChampionshipRound = struct.unpack('<B', data[OFFSET_NAT_CHAMPIONSHIP:OFFSET_PADDING_4])[0]
            self.nextNationalChampionshipRound = NextNationalChampionshipRound(nextNationalChampionshipRound)
            self.validate(data, mainDeck, extraDeck, sideDeck, nbTrunkCards, nbMainCards, nbSideCards, nbExtraCards)

    def dump(self, fp):
        fp.write(self.dumps())
        self.filename = fp.name

    def dumps(self):
        main, extra, side = self.cardsStats.as_decks()
        nbMain = len(main)
        nbExtra = len(extra)
        nbSide = len(side)
        cardsStats = bytes(self.cardsStats).ljust(OFFSET_CARDS_MAIN - OFFSET_STATS_CARDS, b'\x00')
        duelistsStats = bytes(self.duelistsStats).ljust(OFFSET_DAYS_ELAPSED - OFFSET_STATS_DUELISTS, b'\x00')
        cardSize = struct.calcsize('<H')

        fmt = (
            '<'         # Little-endian
            '{}H'       # Header
            '{}s'       # Cards stats
            '{}H{}x'    # Main cards
            '{}H{}x'    # Side cards
            '{}H{}x'    # Extra cards
            '4H'        # Counters for trunk, main, side, extra
            '{}x'       # Padding #2
            '{}s'       # Duelists stats
            'H'         # In-game days elapsed
            '{}H'       # @FIXME Static value ?
            '{}x'       # @FIXME Unknown values, marked as padding for now
            'B'         # Championship progression
            '{}x'       # Padding #4
            '{}s'       # Game ID
        )
        fmt = fmt.format(
            len(VALUE_HEADER),                                  # Header
            len(cardsStats),                                    # Cards stats + padding #2
            nbMain, (MainDeck.LIMIT - nbMain) * cardSize,       # Main cards
            nbSide, (SideDeck.LIMIT - nbSide) * cardSize,       # Side cards
            nbExtra, (ExtraDeck.LIMIT - nbExtra) * cardSize,    # Extra cards
            OFFSET_STATS_DUELISTS - OFFSET_PADDING_2,           # Padding #2
            len(duelistsStats),                                 # Duelists stats + padding #3
            len(VALUE_STATIC),                                  # Static value
            OFFSET_NAT_CHAMPIONSHIP - OFFSET_UNKNOWN,           # Unknown
            OFFSET_GAME_ID - OFFSET_PADDING_4,                  # Padding #4
            len(VALUE_GAME_ID),                                 # Game ID
        )
        args = [
            *VALUE_HEADER,
            cardsStats,
            *main,
            *side,
            *extra,
            int(self.cardsStats),
            len(main),
            len(side),
            len(extra),
            duelistsStats,
            (self.ingameDate - self.STARTING_DATE).days,
            *VALUE_STATIC,
            self.nextNationalChampionshipRound,
            VALUE_GAME_ID,
        ]

        data = [struct.pack(fmt, *args)]
        data.extend([
            struct.pack('<H', self.checksum(data[0])),
            b'\xFF' * (OFFSET_EOF - OFFSET_FINAL_PADDING),
        ])
        return b''.join(data)

    @classmethod
    def load(cls, fp):
        return cls.loads(fp.read(), fp.name)

    @classmethod
    def loads(cls, s, filename=None):
        return cls(s, filename)

    @staticmethod
    def checksum(data):
        chk = sum(struct.unpack_from('<{}H'.format(SIZE_CHECKSUM_INPUT), data)) & 0xFFFF
        chk = (chk ^ 0xFFFF) + 1
        return chk

    def validate(self, data, mainDeck, extraDeck, sideDeck, nbTrunkCards, nbMainCards, nbSideCards, nbExtraCards):
        # Make sure the save data has the proper length
        assert len(data) == OFFSET_EOF

        # ... the save is for this game
        assert data[OFFSET_GAME_ID:OFFSET_CHECKSUM] == VALUE_GAME_ID

        # ... we have a proper checksum
        assert struct.unpack('<H', data[OFFSET_CHECKSUM:OFFSET_FINAL_PADDING])[0] == self.checksum(data)

        # ... the header is correct
        assert struct.unpack_from('<{}H'.format(len(VALUE_HEADER)), data) == VALUE_HEADER

        # ... and so is the final padding
        assert data.count(b'\xFF', OFFSET_FINAL_PADDING) == (OFFSET_EOF - OFFSET_FINAL_PADDING)

        # ... the stats & actual decks agree
        main, extra, side = self.cardsStats.as_decks()
        assert main == mainDeck
        assert extra == extraDeck
        assert side == sideDeck

        # ... the numbers add up
        assert nbTrunkCards == int(self.cardsStats)
        assert nbMainCards == len(main)
        assert nbExtraCards == len(extra)
        assert nbSideCards == len(side)

    def get_ingame_date(self):
        return self.ingameDate

    def set_ingame_date(self, new_date):
        if new_date < self.STARTING_DATE:
            raise ValueError(new_date)
        self.ingameDate = new_date

    def get_next_national_championship_round(self):
        return self.nextNationalChampionshipRound

    def set_next_national_championship_round(self, value):
        self.nextNationalChampionshipRound = NextNationalChampionshipRound(value)

    def get_cards_stats(self):
        res = {
            "total": 0,
            "unique": 0,
            "trunk": 0,
            "main": 0,
            "extra": 0,
            "side": 0,
            "unique_max": MAX_OBTAINABLE_CARDS,
            "trunk_max": MAX_TRUNK_CARDS,
            "main_max": MainDeck.LIMIT,
            "extra_max": ExtraDeck.LIMIT,
            "side_max": SideDeck.LIMIT,
        }
        for card in self.cardsStats:
            target = "extra" if card.card.MonsterType == MonsterType.FUSION else "main"
            copies = int(card)
            res["total"] += copies
            if copies:
                res["unique"] += 1
            res["trunk"] += card.copiesTrunk
            res[target] += card.copiesMainExtra
            res["side"] += card.copiesSide
        return res

    def get_detailed_cards_stats(self):
        return self.cardsStats

    def get_duelists_stats(self):
        res = {
            "total": 0,
            "won": 0,
            "drawn": 0,
            "lost": 0,
        }
        outcomes = ("won", "lost", "drawn")
        for duelist in self.duelistsStats:
            for outcome in outcomes:
                value = getattr(duelist, outcome)
                res["total"] += value
                res[outcome] += value
        return res

    def get_detailed_duelists_stats(self):
        return self.duelistsStats
