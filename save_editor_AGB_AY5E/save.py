import itertools
import struct

from datetime import date, timedelta

from .constants import *
from .decks import Deck, ExtraDeck, MainDeck, SideDeck
from .enums import NextNationalChampionshipRound, MonsterType
from .models import BoosterPack, Card, Duelist


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


class Save():
    # In-game date when the game starts.
    STARTING_DATE = date(2001, 1, 1)

    # Because the game stored the number of in-game days since `STARTING_DATE` as a 16-bit value,
    # the maximum theoretical date that can be stored is June 6th, 2180 (=0xFFFF).
    # After that, the date would simply roll back to January 1st, 2001 due to integer overflow.
    # Indeed, this can be seen when trying to look for events past June 2180 in the game's calendar.
    # In reality, the game will stop incrementing the date as soon as December 31st, 2100 is reached.
    MAX_DATE = date(2100, 12, 31)

    def __init__(self, data=None, filename=None):
        self.cardsStats = CardsStats(data[OFFSET_STATS_CARDS:] if data else None)
        self.duelistsStats = DuelistsStats(data[OFFSET_STATS_DUELISTS:] if data else None)
        self.ingameDate = date(self.STARTING_DATE.year, self.STARTING_DATE.month, self.STARTING_DATE.day)
        self.nextNationalChampionshipRound = NextNationalChampionshipRound.ROUND_1
        self.filename = filename
        self.lastPackReceived = PACKS[0]
        self.lastDuelistFought = DUELISTS[0]
        self.publicationVictories = 0
        self.nationalChampionshipVictories = 0

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
            lastPackReceived = struct.unpack('<H', data[OFFSET_LAST_PACK:OFFSET_PUB_VICTORIES])[0]
            self.lastPackReceived = PACKS[lastPackReceived]
            self.publicationVictories = struct.unpack('<H', data[OFFSET_PUB_VICTORIES:OFFSET_LAST_DUELIST])[0]
            lastDuelistFought = struct.unpack('<H', data[OFFSET_LAST_DUELIST:OFFSET_PADDING_4])[0]
            self.lastDuelistFought = DUELISTS[lastDuelistFought]
            nextNationalChampionshipRound = struct.unpack('<B', data[OFFSET_NAT_CHAMPIONSHIP:OFFSET_PADDING_5])[0]
            self.nextNationalChampionshipRound = NextNationalChampionshipRound(nextNationalChampionshipRound)
            self.nationalChampionshipVictories = struct.unpack('<b', data[OFFSET_NAT_VICTORIES:OFFSET_PADDING_6])[0]

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
            'H'         # Static value (3 = game initialized)
            'H'         # ID of last received booster pack
            'H'         # Number of victories since last publication
            'H'         # ID of last duelist fought
            '{}x'       # @FIXME Unknown values, marked as padding #4 for now
            'B'         # Championship progression
            '{}x'       # Padding #5
            'b'         # Number of victories in National Championship
            '{}x'       # Padding #6
            '{}s'       # Game ID
        )
        fmt = fmt.format(
            len(VALUE_HEADER),                                  # Header
            len(cardsStats),                                    # Cards stats + padding #1
            nbMain, (MainDeck.LIMIT - nbMain) * cardSize,       # Main cards
            nbSide, (SideDeck.LIMIT - nbSide) * cardSize,       # Side cards
            nbExtra, (ExtraDeck.LIMIT - nbExtra) * cardSize,    # Extra cards
            OFFSET_STATS_DUELISTS - OFFSET_PADDING_2,           # Padding #2
            len(duelistsStats),                                 # Duelists stats + padding #3
            OFFSET_NAT_CHAMPIONSHIP - OFFSET_PADDING_4,         # Unknown / Padding #4
            OFFSET_NAT_VICTORIES - OFFSET_PADDING_5,            # Padding #5
            OFFSET_GAME_ID - OFFSET_PADDING_6,                  # Padding #6
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
            self.lastPackReceived,
            self.publicationVictories,
            self.lastDuelistFought,
            self.nextNationalChampionshipRound,
            self.nationalChampionshipVictories,
            VALUE_GAME_ID,
        ]

        data = [struct.pack(fmt, *args)]
        data.extend([
            struct.pack('<H', self.checksum(data[0])),
            b'\xFF' * (OFFSET_EOF - OFFSET_FINAL_PADDING),
        ])
        return b''.join(data)

    @classmethod
    def load(cls, fp) -> "Save":
        return cls.loads(fp.read(), fp.name)

    @classmethod
    def loads(cls, s: str, filename=None) -> "Save":
        return cls(s, filename)

    @staticmethod
    def checksum(data) -> int:
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

    def get_ingame_date(self) -> date:
        return self.ingameDate

    def set_ingame_date(self, new_date:date) -> None:
        if new_date < self.STARTING_DATE or new_date > self.MAX_DATE:
            raise ValueError(new_date)
        self.ingameDate = new_date

    def get_next_national_championship_round(self) -> NextNationalChampionshipRound:
        return self.nextNationalChampionshipRound

    def set_next_national_championship_round(self, value: NextNationalChampionshipRound) -> None:
        self.nextNationalChampionshipRound = NextNationalChampionshipRound(value)

    def get_national_championship_victories(self) -> int:
        return self.nationalChampionshipVictories

    def set_national_championship_victories(self, victories: int) -> None:
        self.nationalChampionshipVictories = victories

    def get_cards_stats(self) -> dict:
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

    def get_detailed_cards_stats(self) -> CardsStats:
        return self.cardsStats

    def get_duelists_stats(self) -> dict:
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

    def get_detailed_duelists_stats(self) -> DuelistsStats:
        return self.duelistsStats

    def get_last_pack_received(self) -> BoosterPack:
        return self.lastPackReceived

    def set_last_pack_received(self, pack: BoosterPack) -> None:
        self.lastPackReceived = pack

    def get_last_duelist_fought(self) -> Duelist:
        return self.lastDuelistFought

    def set_last_duelist_fought(self, duelist: Duelist) -> None:
        self.lastDuelistFought = duelist

    def get_victories_since_last_publication(self) -> int:
        return self.publicationVictories

    def set_victories_since_last_publication(self, victories: int) -> None:
        assert 0 <= victories < 0xFFFF
        self.publicationVictories = victories
