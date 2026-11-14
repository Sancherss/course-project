from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import re
import yaml

PIN = '2d8eaf326117bd7e4706c48b2d24e27b4a006fa6'
TARGETS = ('reg_client', 'reg_server', 'auth_client_em', 'auth_client_sim', 'auth_client_gen',
           'auth_server_em', 'auth_server_sim', 'auth_server_gen')
CTAPS = ('noCTAP', 'setPIN', 'chgPIN', 'getToken')
COMMON = {'S-pintok', 'S-cntr', 'S-creid', 'S-skau'}

@dataclass(frozen=True)
class ExperimentConfig:
    id: str
    description: str
    scenario: str
    ctap: str
    property: str
    entities: tuple[int, ...] = ()
    fields: tuple[str, ...] = ()
    changed_assumption: str = 'No additional roles or field leaks'
    expected_comparison: str = 'No preassigned result'
    timeout_seconds: float = 60
    diagnostic: bool = False
    token_binding: str = 'upstream'
    precise_actions: bool = False
    single_session_witness: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', self.id):
            raise ValueError('Invalid experiment id')
        if self.scenario not in TARGETS or self.ctap not in CTAPS:
            raise ValueError('Unsupported upstream scenario/CTAP type')
        allowed = set(COMMON)
        if self.scenario.startswith('reg_'): allowed |= {'S-skat', 'A5', 'A6'}
        else: allowed |= {'A1'}
        if 'server' in self.scenario: allowed |= {'S-wk'}
        if self.scenario.endswith(('_sim', '_gen')): allowed |= {'S-tr', 'A2'}
        # Explicit diagnostic query, not represented as an upstream CLI option.
        if self.diagnostic: allowed |= {'D-finish'}
        if self.property not in allowed: raise ValueError('Property not supported for scenario')
        if any(type(i) is not int or not 0 <= i < 5 for i in self.entities) or len(set(self.entities)) != len(self.entities):
            raise ValueError('Entity indexes must be unique integers in 0..4')
        allowed_fields = {'wk', 'skat'} if self.scenario.startswith('reg_') else {'wk', 'skau', 'authcntr', 'creid'}
        if not set(self.fields) <= allowed_fields or len(set(self.fields)) != len(self.fields):
            raise ValueError('Unsupported/duplicate leaked fields')
        if type(self.timeout_seconds) not in (int, float) or not 0 < self.timeout_seconds <= 3600:
            raise ValueError('timeout_seconds must be in (0, 3600]')
        if type(self.diagnostic) is not bool or type(self.single_session_witness) is not bool:
            raise ValueError('Diagnostic switches must be boolean')
        if self.single_session_witness and not (self.diagnostic and self.property == 'D-finish'):
            raise ValueError('Single-session mode is restricted to reachability witnesses')
        if type(self.precise_actions) is not bool: raise ValueError('precise_actions must be boolean')
        if self.token_binding != 'upstream':
            raise ValueError('Unsupported token binding')

    @classmethod
    def from_dict(cls, data: dict) -> 'ExperimentConfig':
        d = dict(data)
        for key in ('entities', 'fields'):
            if key in d:
                if not isinstance(d[key], (list, tuple)): raise ValueError(f'{key} must be a list')
                d[key] = tuple(d[key])
        return cls(**d)

    def to_dict(self) -> dict:
        return asdict(self)


def load_matrix(path: Path) -> list[ExperimentConfig]:
    data = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('upstream_commit') != PIN:
        raise ValueError('Matrix must pin the researched upstream commit')
    if not isinstance(data.get('experiments'), list) or not data['experiments']:
        raise ValueError('Matrix must contain experiments')
    configs = [ExperimentConfig.from_dict(x) for x in data['experiments']]
    if len({c.id for c in configs}) != len(configs): raise ValueError('Duplicate experiment ids')
    return configs
