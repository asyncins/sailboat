from enum import Enum


class Role(Enum):
    SuperUser = 100
    Developer = 10
    Other = 1
    Anonymous = 0


class Status(Enum):
    On = 1
    Off = 0


class StatusCode(Enum):
    NoAuth = ("no auth", 403)
    MissingParameter = ("missing parameter", 4001)
    IsNotYours = ("is not yours", 4002)
    ParameterError = ("parameter error", 4003)
    UserStatusOff = ("user status off", 4004)
    NotFound = ("not found", 4005)
    JsonDecodeError = ("JSONDecode Error", 4006)
    PathError = ("path error", 4007)
    OperationError = ("operation error", 4008)
    TokenOverdue = ("token overdue", 4009)


