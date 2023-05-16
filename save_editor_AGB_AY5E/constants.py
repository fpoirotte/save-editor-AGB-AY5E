from .models import Card, Duelist, BoosterPack, load_dataset


class Offsets:
    """Constants for the various offsets inside the savegame."""
    HEADER           = 0x0000 # u8[8]
    STATS_CARDS      = 0x0008 # u32[821]
    PADDING_1        = 0x0CDC # ?
    CARDS_MAIN       = 0x2008 # u16[60]
    CARDS_SIDE       = 0x2080 # u16[15]
    CARDS_EXTRA      = 0x209E # u16[20]
    NB_CARDS_TOTAL   = 0x20C6 # u16
    NB_CARDS_MAIN    = 0x20C8 # u16
    NB_CARDS_SIDE    = 0x20CA # u16
    NB_CARDS_EXTRA   = 0x20CC # u16
    PADDING_2        = 0x20CE # u8[2]
    STATS_DUELISTS   = 0x20D0 # u32[25]
    PADDING_3        = 0x2134 # ?
    DAYS_ELAPSED     = 0x2150 # u16
    STATIC           = 0x2152 # u16
    LAST_PACK        = 0x2154 # u16
    PUB_VICTORIES    = 0x2156 # u16
    LAST_DUELIST     = 0x2158 # u16
    PADDING_4        = 0x215A # u8[4]
    NAT_CHAMPIONSHIP = 0x215E # u16
    GRANDPA_CUP      = 0x2160 # u16
    NAT_VICTORIES    = 0x2162 # s8
    PADDING_5        = 0x2163 # u8
    ANNOUNCEMENTS    = 0x2164 # u16
    GAME_ID          = 0x2166 # char[8]
    CHECKSUM         = 0x216E # u16
    FINAL_PADDING    = 0x2170
    EOF              = 0x8000


class FrozenModelDict(dict):
    def __init__(self, values):
        def gen(vals):
            for value in vals:
                yield (value.Name, value)
        super().__init__(gen(values))

    def __missing__(self, key):
        for value in self.values():
            if value.ID == key:
                return value
        raise KeyError(key)

    def __delattr__(self, *args, **kwargs):
        raise RuntimeError()

    __setattr__ = __delitem__ = __setitem__ = __delattr__


# A frozen dict for the game's cards.
CARDS = FrozenModelDict(load_dataset('cards', Card))

# A frozen dict for the game's duelists.
DUELISTS = FrozenModelDict(load_dataset('duelists', Duelist))

# A frozen dict for the game's duelists.
PACKS = FrozenModelDict(load_dataset('packs', BoosterPack))

# Technically, the game contains 820 cards, but the last one (Insect Monster Token)
# cannot appear in the player's trunk/decks without cheating, hence this limit.
# Note: there are other cards that can be obtained by defeating Simon at the end
#       of the game, although they are unplayable (eg. Egyptian gods, Ticket cards).
MAX_OBTAINABLE_CARDS = 819

# Number of slots available in the trunk for all the cards combined.
# This counter is stored as a 16-bit number.
MAX_TRUNK_CARDS = 0xFFFF

# Maximum number of copies allowed in the trunk for a given card.
# This counter is stored as a 10-bit number.
MAX_TRUNK_COPIES = 0x3F

# Technically, the number of won/lost duels is stored on 11 bits
# while drawn duels are stored as a 10-bit number.
# However, these numbers are always displayed on 2 digits in the game,
# hence the value set below.
MAX_WON = MAX_LOST = MAX_DRAWN = 99

# Number of bytes used to store the statistics for a single card.
SIZE_CARD_STATS         = 4

# Number of bytes used to store the statistics for a single duelist.
SIZE_DUELIST_STATS      = 4

# Number of bytes used to compute the savegame's checksum.
SIZE_CHECKSUM_INPUT     = 0x10B6

# Various static values.
VALUE_HEADER            = (0, 0, 1, 0)
VALUE_STATIC            = (3, )
VALUE_GAME_ID           = b'DMEX1INT'
