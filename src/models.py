import csv

import enums
import metadata

from dataclasses import dataclass
from typing import Union, get_origin, get_args, get_type_hints


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
    Stage: enums.Stage


@dataclass(frozen=True)
class Card(Model):
    ID: int
    Name: str
    CardType: enums.CardType
    MonsterType: Union[enums.MonsterType, EmptyString]
    Attribute: Union[enums.Attribute, EmptyString]
    Type: Union[enums.Type, EmptyString]
    Level: Union[enums.Level, EmptyString]
    ATK: Union[NonEmptyString, EmptyString]
    DEF: Union[NonEmptyString, EmptyString]
    Password: Union[Password, EmptyString]
    Limit: enums.Limit


def load_dataset(filename: str, model: Model):
    hints = get_type_hints(model)
    fields = set(hints)
    none = None.__class__
    fullpath = metadata.RESOURCES_DIR / (filename + '.csv')
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
    print(list(load_dataset('cards', Card)))
    print(list(load_dataset('duelists', Duelist)))
