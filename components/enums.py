from enum import Enum


class Role(Enum):
    SuperUser = 100
    Developer = 10
    Other = 1
    Anonymous = 0


class Status(Enum):
    On = 1
    Off = 0
