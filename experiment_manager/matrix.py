from __future__ import annotations
from pathlib import Path
from .config import load_matrix
from .runner import run_experiment, ROOT

def run_matrix(path: Path, executable: str, version: str, *, only: str | None = None) -> list[Path]:
    configs = load_matrix(path)
    if only:
        configs = [c for c in configs if c.id == only]
        if not configs: raise ValueError(f'No experiment id {only}')
    paths = []
    for c in configs:
        path = run_experiment(c, executable, version)
        paths.append(path)
        print(f'{c.id}: {path.name}', flush=True)
    return paths
