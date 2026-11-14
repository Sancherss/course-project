"""Disposable subprocess worker calling the original Case.write_file API."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from .config import ExperimentConfig


def generate(config: ExperimentConfig, upstream: Path, destination: Path) -> None:
    # Caller starts this module in an empty temporary cwd. Import side effects stay there.
    for name in ('Reg.pv', 'Auth.pv', 'FIDO2.pvl'):
        shutil.copy2(upstream / name, Path.cwd() / name)
    spec = importlib.util.spec_from_file_location('historical_fido2verif', upstream / 'FIDO2Verif.py')
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    gen = module.Generator(config.scenario)
    query = next((q for q in gen.queries.all_queries if q.name == config.property), None)
    if config.property == 'D-finish':
        if config.scenario.startswith('reg_'):
            statement = 'query u:UserHandle, r:RpID, a:AAGUID, c:bitstring, pkau:spkey; event(Server_Finish_Reg(u,r,a,c,pkau)).\n'
        else:
            statement = 'query u:UserHandle, r:RpID, a:AAGUID, c:bitstring; event(Server_Finish_Auth(u,r,a,c)).\n'
        query = module.Query('D-finish', statement)
    if query is None: raise ValueError('Query absent from upstream classes')
    ctap = next(c for c in gen.ctap.all_types if c.name == config.ctap)
    fields = module.Fields([f'out(cP,{f});\n' for f in config.fields])
    indexes = tuple(sorted(config.entities))
    entities = module.Entities([gen.entities.all_entities[i] for i in indexes], indexes)
    case = module.Case(config.scenario, gen.types.get(0), ctap, query, fields, entities,
                       gen.lines, gen.type_set_row, gen.fields_set_row, gen.entities_ctap_set_row,
                       gen.entities_ctap_set_row_1, gen.entities_noctap_set_row)
    case.write_file(False)  # retain replication; do not call buggy upstream analyze/proverif.
    shutil.copy2(case.query_path, destination / 'model.pv')
    shutil.copy2('FIDO2.pvl', destination / 'FIDO2.pvl')

if __name__ == '__main__':
    config = ExperimentConfig.from_dict(json.loads(Path(sys.argv[1]).read_text()))
    generate(config, Path(sys.argv[2]), Path(sys.argv[3]))
