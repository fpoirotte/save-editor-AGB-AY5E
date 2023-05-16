import struct

from datetime import date, timedelta

from .constants import DUELISTS, PACKS
from .constants import MAX_OBTAINABLE_CARDS, MAX_TRUNK_CARDS
from .constants import Offsets, SIZE_CHECKSUM_INPUT
from .constants import VALUE_GAME_ID, VALUE_HEADER, VALUE_STATIC
from .decks import ExtraDeck, MainDeck, SideDeck
from .enums import Announcements, NextNationalChampionshipRound, MonsterType
from .models import BoosterPack, Duelist
from .stats import CardsStats, DuelistsStats


class Save():
    # In-game date when the game starts.
    STARTING_DATE = date(2001, 1, 1)

    # Because the game stores the number of in-game days since `STARTING_DATE` as a 16-bit value,
    # the maximum theoretical date that can be stored is June 6th, 2180 (=0xFFFF).
    # After that, the date would simply roll back to January 1st, 2001 due to integer overflow.
    # Indeed, this can be seen when trying to look for events past June 2180 in the game's calendar.
    # In reality, the game will stop incrementing the date as soon as December 31st, 2100 is reached.
    MAX_DATE = date(2100, 12, 31)

    def __init__(self, data=None, filename=None):
        self.cardsStats = CardsStats(data[Offsets.STATS_CARDS:] if data else None)
        self.duelistsStats = DuelistsStats(data[Offsets.STATS_DUELISTS:] if data else None)
        self.ingameDate = date(self.STARTING_DATE.year, self.STARTING_DATE.month, self.STARTING_DATE.day)
        self.nextNationalChampionshipRound = NextNationalChampionshipRound.ROUND_1
        self.filename = filename
        self.lastPackReceived = PACKS[0]
        self.lastDuelistFought = DUELISTS[0]
        self.publicationVictories = 0
        self.nationalChampionshipVictories = 0
        self.grandpaCupQualification = False
        self.announcements = Announcements.NONE

        if data:
            mainDeck = MainDeck()
            extraDeck = ExtraDeck()
            sideDeck = SideDeck()

            nbTrunkCards, nbMainCards, nbSideCards, nbExtraCards = struct.unpack('<4H', data[Offsets.NB_CARDS_TOTAL:Offsets.PADDING_2])
            mainDeck.extend(struct.unpack_from('<{}H'.format(nbMainCards), data[Offsets.CARDS_MAIN:Offsets.CARDS_MAIN + 2*nbMainCards]))
            sideDeck.extend(struct.unpack_from('<{}H'.format(nbSideCards), data[Offsets.CARDS_SIDE:Offsets.CARDS_SIDE + 2*nbSideCards]))
            extraDeck.extend(struct.unpack_from('<{}H'.format(nbExtraCards), data[Offsets.CARDS_MAIN:Offsets.CARDS_EXTRA + 2*nbExtraCards]))

            daysElapsed = struct.unpack('<H', data[Offsets.DAYS_ELAPSED:Offsets.STATIC])[0]
            self.ingameDate += timedelta(days=daysElapsed)
            lastPackReceived = struct.unpack('<H', data[Offsets.LAST_PACK:Offsets.PUB_VICTORIES])[0]
            self.lastPackReceived = PACKS[lastPackReceived]
            self.publicationVictories = struct.unpack('<H', data[Offsets.PUB_VICTORIES:Offsets.LAST_DUELIST])[0]
            lastDuelistFought = struct.unpack('<H', data[Offsets.LAST_DUELIST:Offsets.PADDING_4])[0]
            self.lastDuelistFought = DUELISTS[lastDuelistFought]

            nextNationalChampionshipRound = struct.unpack('<H', data[Offsets.NAT_CHAMPIONSHIP:Offsets.GRANDPA_CUP])[0]
            self.nextNationalChampionshipRound = NextNationalChampionshipRound(nextNationalChampionshipRound)
            grandpaCupQualification = struct.unpack('<H', data[Offsets.GRANDPA_CUP:Offsets.NAT_VICTORIES])[0]
            self.grandpaCupQualification = bool(grandpaCupQualification)
            self.nationalChampionshipVictories = struct.unpack('<b', data[Offsets.NAT_VICTORIES:Offsets.PADDING_5])[0]

            announcements = struct.unpack('<H', data[Offsets.ANNOUNCEMENTS:Offsets.GAME_ID])[0]
            self.announcements = Announcements(announcements)

            self.validate(data, mainDeck, extraDeck, sideDeck, nbTrunkCards, nbMainCards, nbSideCards, nbExtraCards)

    def dump(self, fp) -> None:
        fp.write(self.dumps())
        self.filename = fp.name

    def dumps(self) -> bytes:
        main, extra, side = self.cardsStats.as_decks()
        nbMain = len(main)
        nbExtra = len(extra)
        nbSide = len(side)
        cardSize = struct.calcsize('<H')

        # The calls to ljust() allow us to pad the stats with NUL bytes
        # to match the game's expectations.
        cardsStats = bytes(self.cardsStats).ljust(Offsets.CARDS_MAIN - Offsets.STATS_CARDS, b'\x00')
        duelistsStats = bytes(self.duelistsStats).ljust(Offsets.DAYS_ELAPSED - Offsets.STATS_DUELISTS, b'\x00')

        fmt = (
            '<'         # Little-endian
            '{}H'       # Header
            '{}s'       # Cards stats (+ padding #1)
            '{}H{}x'    # Main cards
            '{}H{}x'    # Side cards
            '{}H{}x'    # Extra cards
            '4H'        # Counters for trunk, main, side, extra
            '2x'        # Padding #2
            '{}s'       # Duelists stats (+ padding #3)
            'H'         # In-game days elapsed
            'H'         # Static value (3 = game initialized)
            'H'         # ID of last received booster pack
            'H'         # Number of victories since last publication
            'H'         # ID of last duelist fought
            '4x'        # Padding #4
            'H'         # National Championship qualification
            'H'         # Grandpa Cup qualification
            'b'         # Number of victories in National Championship
            'x'         # Padding #5
            'H'         # Announcements
            '{}s'       # Game ID
        )
        fmt = fmt.format(
            len(VALUE_HEADER),                                  # Header
            len(cardsStats),                                    # Cards stats + padding #1
            nbMain, (MainDeck.LIMIT - nbMain) * cardSize,       # Main cards
            nbSide, (SideDeck.LIMIT - nbSide) * cardSize,       # Side cards
            nbExtra, (ExtraDeck.LIMIT - nbExtra) * cardSize,    # Extra cards
            len(duelistsStats),                                 # Duelists stats + padding #3
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
            int(self.grandpaCupQualification),
            self.nationalChampionshipVictories,
            self.announcements,
            VALUE_GAME_ID,
        ]

        data = [struct.pack(fmt, *args)]
        data.extend([
            struct.pack('<H', self.checksum(data[0])),
            b'\xFF' * (Offsets.EOF - Offsets.FINAL_PADDING),
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

    def validate(self, data, mainDeck, extraDeck, sideDeck, nbTrunkCards, nbMainCards, nbSideCards, nbExtraCards) -> None:
        # Make sure the save data has the proper length
        assert len(data) == Offsets.EOF

        # ... the save is for this game
        assert data[Offsets.GAME_ID:Offsets.CHECKSUM] == VALUE_GAME_ID

        # ... we have a proper checksum
        assert struct.unpack('<H', data[Offsets.CHECKSUM:Offsets.FINAL_PADDING])[0] == self.checksum(data)

        # ... the header is correct
        assert struct.unpack_from('<{}H'.format(len(VALUE_HEADER)), data) == VALUE_HEADER

        # ... and so is the final padding
        assert data.count(b'\xFF', Offsets.FINAL_PADDING) == (Offsets.EOF - Offsets.FINAL_PADDING)

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

    def get_elapsed_days(self) -> int:
        return (self.ingameDate - self.STARTING_DATE).days

    def get_next_national_championship_round(self) -> NextNationalChampionshipRound:
        return self.nextNationalChampionshipRound

    def set_next_national_championship_round(self, value: NextNationalChampionshipRound) -> None:
        self.nextNationalChampionshipRound = NextNationalChampionshipRound(value)

    def get_national_championship_victories(self) -> int:
        return self.nationalChampionshipVictories

    def set_national_championship_victories(self, victories: int) -> None:
        self.nationalChampionshipVictories = victories

    def get_grandpa_cup_qualification(self) ->  bool:
        return self.grandpaCupQualification

    def set_grandpa_cup_qualification(self, qualified: bool) -> None:
        self.grandpaCupQualification = qualified

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

    def get_announcements(self) -> Announcements:
        return self.announcements

    def set_announcements(self, announcements: Announcements) -> None:
        self.announcements = Announcements(announcements)
