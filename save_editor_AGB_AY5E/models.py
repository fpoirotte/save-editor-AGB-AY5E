import csv

from dataclasses import dataclass
from typing import Union, get_origin, get_args, get_type_hints

from .enums import Attribute, CardType, Level, Limit, MonsterType, Stage, Type
from .metadata import RESOURCES_DIR


def NonEmptyString(value):
    if not value:
        raise ValueError(value)
    return value

def Password(value):
    if not isinstance(value, str) or len(value) != 8 or not value.isdigit():
        raise ValueError(value)
    return value

def EmptyString(value):
    if value:
        raise ValueError(value)
    return None


@dataclass
class Model:
    def __int__(self):
        return self.ID
    __index__ = __int__

    def __str__(self):
        return self.Name


@dataclass(frozen=True)
class Duelist(Model):
    ID: int
    Name: str
    Stage: Stage


@dataclass(frozen=True)
class Card(Model):
    ID: int
    InternalID: int
    Name: str
    CardType: CardType
    MonsterType: Union[MonsterType, EmptyString]
    Attribute: Union[Attribute, EmptyString]
    Type: Union[Type, EmptyString]
    Level: Union[Level, EmptyString]
    ATK: Union[NonEmptyString, EmptyString]
    DEF: Union[NonEmptyString, EmptyString]
    Password: Union[Password, EmptyString]
    Limit: Limit
    Description: str


@dataclass(frozen=True)
class BoosterPack(Model):
    ID: int
    Name: str
    InternalName: str


def load_dataset(filename: str, model: Model):
    hints = get_type_hints(model)
    fields = set(hints)
    none = None.__class__
    fullpath = RESOURCES_DIR / (filename + '.csv')
    with fullpath.open("r", newline="") as fd:
        reader = csv.DictReader(fd, dialect="excel")

        for row in reader:
            assert set(row) == fields
            args = {}
            for field in fields:
                ftype = hints[field]
                if get_origin(ftype) == Union:
                    for typ in get_args(ftype):
                        try:
                            value = None if typ == none else typ(row[field])
                            break
                        except (ValueError, AssertionError):
                            pass
                    else:
                        raise ValueError(row[field])
                else:
                    value = ftype(row[field])
                args[field] = value
            yield model(**args)


if __name__ == '__main__':
    cards = list(load_dataset('cards', Card))
    duelists = list(load_dataset('duelists', Duelist))
    print(cards)
    print(duelists)
#    res = {}
#    for card in cards:
#        name = card.Name.upper().replace('.', '').replace('&', 'AND')
#        for c in (' ', ',', '(', ')', '#',"'",'-'):
#            name = name.replace(c, '_')
#        if name[0].isdigit():
#            name = '_' + name
#        if not name.isidentifier():
#            raise ValueError(name)
#        if name in res:
#            raise RuntimeError(name)
#        res[name] = (card.InternalID, card.ID, card.Name)
#    with open('/tmp/cards.h', 'w') as fd:
#        fd.write("enum card {\n")
#        for ident, value in res.items():
#            fd.write("    {} = {}, // #{:03d}: {}\n".format(ident, *value))
#        fd.write("};\n")
