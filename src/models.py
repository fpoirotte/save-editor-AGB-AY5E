import csv

import enums
import metadata

from dataclasses import dataclass
from typing import Optional, Union, get_origin, get_args, get_type_hints


class Password:
    def __init__(self, value):
        if not isinstance(value, str) or len(value) != 8 or not value.isdigit():
            raise ValueError(value)
        self.value = value

    def __str__(self):
        return self.value

    __repr__ = __str__


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
    CardType: Optional[enums.CardType]
    MonsterType: Optional[enums.MonsterType]
    Attribute: Optional[enums.Attribute]
    Type: Optional[enums.Type]
    Level: Optional[enums.Level]
    ATK: Optional[int]
    DEF: Optional[int]
    Password: Optional[Password]
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
