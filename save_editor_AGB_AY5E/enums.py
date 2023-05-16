from enum import Enum, IntEnum, auto


class IntStringEnum(IntEnum):
    @classmethod
    def _missing_(cls, value):
        value = int(value)
        for member in cls:
            if value == member.value:
                return member
        return None


class ZeroBasedIntStringEnum(IntStringEnum):
    def _generate_next_value_(name, start, count, last_values):
        return count


class Stage(IntStringEnum):
    STAGE_1 = auto()
    STAGE_2 = auto()
    STAGE_3 = auto()
    STAGE_4 = auto()
    STAGE_5 = auto()


class CardType(Enum):
    MAGIC = "Magic"
    MONSTER = "Monster"
    TICKET = "Ticket"
    TRAP = "Trap"


class MonsterType(Enum):
    EFFECT = "Effect"
    FUSION = "Fusion"
    NORMAL = "Normal"
    RITUAL = "Ritual"
    TOKEN = "Token"


class Attribute(Enum):
    DARK = "DARK"
    EARTH = "EARTH"
    FIRE = "FIRE"
    LIGHT = "LIGHT"
    WATER = "WATER"
    WIND = "WIND"
    DIVINE = "DIVINE"


class Type(Enum):
    AQUA = "Aqua"
    BEAST = "Beast"
    BEAST_WARRIOR = "Beast-Warrior"
    DINOSAUR = "Dinosaur"
    DIVINE_BEAST = "Divine-Beast"
    DRAGON = "Dragon"
    FAIRY = "Fairy"
    FIEND = "Fiend"
    FISH = "Fish"
    INSECT = "Insect"
    MACHINE = "Machine"
    PLANT = "Plant"
    PYRO = "Pyro"
    REPTILE = "Reptile"
    ROCK = "Rock"
    SEA_SERPENT = "Sea Serpent"
    SPELLCASTER = "Spellcaster"
    THUNDER = "Thunder"
    WARRIOR = "Warrior"
    WINGED_BEAST = "Winged Beast"
    ZOMBIE = "Zombie"


class Level(IntStringEnum):
    LEVEL_1 = auto()
    LEVEL_2 = auto()
    LEVEL_3 = auto()
    LEVEL_4 = auto()
    LEVEL_5 = auto()
    LEVEL_6 = auto()
    LEVEL_7 = auto()
    LEVEL_8 = auto()
    LEVEL_9 = auto()
    LEVEL_10 = auto()
    LEVEL_11 = auto()
    LEVEL_12 = auto()


class Limit(ZeroBasedIntStringEnum):
    LIMIT_0 = auto()
    LIMIT_1 = auto()
    LIMIT_2 = auto()
    LIMIT_3 = auto()


class NextNationalChampionshipRound(ZeroBasedIntStringEnum):
    ROUND_1 = auto()
    ROUND_2 = auto()
    SEMI_FINAL = auto()
    FINAL = auto()


class NotebookPage(ZeroBasedIntStringEnum):
    GENERAL = auto()
    CARDS = auto()
    DUELISTS = auto()


class CardColumn(ZeroBasedIntStringEnum):
    ID = auto()
    NAME = auto()
    TRUNK = auto()
    MAIN_EXTRA = auto()
    SIDE = auto()
    PASSWORD = auto()
    USED = auto()
    LIMIT = auto()


class DuelistColumn(ZeroBasedIntStringEnum):
    ID = auto()
    NAME = auto()
    STAGE = auto()
    WON = auto()
    DRAWN = auto()
    LOST = auto()


class DeckColor(IntEnum):
    BLACK = auto()
    RED = auto()
    GREEN = auto()


class Event(Enum):
    WEEKLY_YUGIOH           = "Weekly Yu-Gi-Oh!"
    YUGIOH_MAGAZINE         = "Yu-Gi-Oh! Magazine"
    WEEKEND_DUEL            = "Weekend Duel"
    GRANDPA_QUALIFIERS      = "Grandpa Cup - Qualifiers"
    GRANDPA_FINAL           = "Grandpa Cup - Final (if qualified)"
    NATIONALS_ROUND_1       = "National Championship - 1st Round"
    NATIONALS_ROUND_2       = "National Championship - 2nd Round (if qualified)"
    NATIONALS_SEMI_FINAL    = "National Championship - Semi Final (if qualified)"
    NATIONALS_FINAL         = "National Championship - Final (if qualified)"


class SpecialDuelist(IntEnum):
    SIMON       = 22 # 0x16
    PEGASUS     = 23 # 0x17
    TRUSDALE    = 24 # 0x18
