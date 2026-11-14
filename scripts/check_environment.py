#!/usr/bin/env python3
"""Read-only environment check; never imports the upstream Python module."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PIN = '2d8eaf326117bd7e4706c48b2d24e27b4a006fa6'
FILES = ('FIDO2Verif.py', 'FIDO2.pvl', 'Reg.pv', 'Auth.pv', 'Reg_unlink.pv', 'Auth_unlink.pv')

def resolve_proverif(value: str | None = None) -> str:
    candidate = value or os.environ.get('PROVERIF')
    if candidate:
        resolved = shutil.which(candidate) or (str(Path(candidate).resolve()) if Path(candidate).is_file() else None)
    else:
        local = ROOT / '.tools/proverif/proverif'
        resolved = str(local) if local.is_file() else shutil.which('proverif')
    if not resolved:
        raise FileNotFoundError('ProVerif not found. Set PROVERIF or run scripts/bootstrap_proverif.sh.')
    return str(Path(resolved).resolve())

def proverif_version(executable: str) -> str:
    # -help is handled by OCaml Arg; verified in ProVerif 2.05 src/main.ml.
    p = subprocess.run([executable, '-help'], capture_output=True, text=True, timeout=10)
    match = re.search(r'Pro[Vv]erif\s+([0-9]+(?:\.[0-9]+)+)', p.stdout + p.stderr)
    if not match:
        raise RuntimeError('Cannot determine ProVerif version from -help output')
    return match.group(1)

def check(value: str | None = None, upstream: Path | None = None) -> dict:
    upstream = upstream or ROOT / 'upstream/FIDO2Verif'
    result = {'python': platform.python_version(), 'python_ok': sys.version_info >= (3, 10),
              'os': platform.platform(), 'upstream': str(upstream.resolve()),
              'missing_files': [n for n in FILES if not (upstream / n).is_file()]}
    try:
        result['commit'] = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()
        result['upstream_clean'] = not subprocess.check_output(['git', '-C', str(upstream), 'status', '--porcelain'], text=True).strip()
        result['commit_matches_pin'] = result['commit'] == PIN
        result['proverif'] = resolve_proverif(value)
        result['proverif_version'] = proverif_version(result['proverif'])
        version = tuple(map(int, result['proverif_version'].split('.')))
        result['proverif_version_ok'] = version >= (2, 1)
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        result['error'] = str(exc)
    result['ok'] = bool(result['python_ok'] and not result['missing_files'] and not result.get('error')
                        and result.get('commit_matches_pin') and result.get('upstream_clean')
                        and result.get('proverif_version_ok'))
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proverif')
    args = parser.parse_args()
    result = check(args.proverif)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['ok'] else 1)
