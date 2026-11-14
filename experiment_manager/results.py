from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum

class Status(str, Enum):
    PROVED = 'PROVED'
    ATTACK_OR_FALSE = 'ATTACK_OR_FALSE'
    UNKNOWN = 'UNKNOWN'
    ERROR = 'ERROR'

@dataclass(frozen=True)
class QueryResult:
    query: str
    status: Status
    raw_line: str

@dataclass(frozen=True)
class ParsedResult:
    status: Status
    queries: tuple[QueryResult, ...]
    reason: str
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return asdict(self)
