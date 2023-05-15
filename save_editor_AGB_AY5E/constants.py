from .models import Card, Duelist, BoosterPack, load_dataset


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

# Constants for the various offsets inside the savegame.
OFFSET_HEADER           = 0x0000 # u8[8]
OFFSET_STATS_CARDS      = 0x0008 # u32[821]
OFFSET_PADDING_1        = 0x0CDC # ?
OFFSET_CARDS_MAIN       = 0x2008 # u16[60]
OFFSET_CARDS_SIDE       = 0x2080 # u16[15]
OFFSET_CARDS_EXTRA      = 0x209E # u16[20]
OFFSET_NB_CARDS_TOTAL   = 0x20C6 # u16
OFFSET_NB_CARDS_MAIN    = 0x20C8 # u16
OFFSET_NB_CARDS_SIDE    = 0x20CA # u16
OFFSET_NB_CARDS_EXTRA   = 0x20CC # u16
OFFSET_PADDING_2        = 0x20CE # u16
OFFSET_STATS_DUELISTS   = 0x20D0 # u32[25]
OFFSET_PADDING_3        = 0x2134 # ?
OFFSET_DAYS_ELAPSED     = 0x2150 # u16
OFFSET_STATIC           = 0x2152
OFFSET_LAST_PACK        = 0x2154 # u16
OFFSET_PUB_VICTORIES    = 0x2156 # u16
OFFSET_LAST_DUELIST     = 0x2158 # u16
OFFSET_PADDING_4        = 0x215A # ?
OFFSET_NAT_CHAMPIONSHIP = 0x215E # u8
OFFSET_PADDING_5        = 0x215F # u8
OFFSET_NAT_VICTORIES    = 0x2162 # s8
OFFSET_PADDING_6        = 0x2163 # u8
OFFSET_GAME_ID          = 0x2166 # char[8]
OFFSET_CHECKSUM         = 0x216E # u16
OFFSET_FINAL_PADDING    = 0x2170
OFFSET_EOF              = 0x8000

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
