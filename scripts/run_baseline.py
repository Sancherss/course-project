#!/usr/bin/env python3
"""Run the documented upstream unlinkability baseline without upstream Python."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import signal
import subprocess
import time
import uuid
from check_environment import ROOT, check


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proverif')
    parser.add_argument('--timeout', type=float, default=60)
    args = parser.parse_args()
    if not (0 < args.timeout <= 3600):
        parser.error('timeout must be in (0, 3600]')
    env = check(args.proverif)
    if not env['ok']:
        print(json.dumps(env, indent=2)); return 2
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-baseline-' + uuid.uuid4().hex[:8]
    raw = ROOT / 'experiments/raw' / run_id
    raw.mkdir(parents=True, exist_ok=False)
    for name in ('FIDO2.pvl', 'Reg_unlink.pv'):
        shutil.copy2(ROOT / 'upstream/FIDO2Verif' / name, raw / name)
    command = [env['proverif'], '-lib', 'FIDO2.pvl', 'Reg_unlink.pv']
    (raw / 'command.txt').write_text(shlex.join(command) + '\n', encoding='utf-8')
    meta = {'run_id': run_id, 'experiment_id': 'baseline', 'description': 'Upstream P1 registration/getToken/client',
            'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'command': command, 'cwd': str(raw),
            'commit': env['commit'], 'proverif_version': env['proverif_version'], 'python': platform.python_version(),
            'os': platform.platform(), 'timeout_seconds': args.timeout, 'timed_out': False,
            'executable_sha256': hashlib.sha256(Path(env['proverif']).read_bytes()).hexdigest(),
            'input_sha256': {n: hashlib.sha256((raw / n).read_bytes()).hexdigest() for n in ('FIDO2.pvl', 'Reg_unlink.pv')}}
    started = time.monotonic()
    with (raw / 'stdout.txt').open('wb') as out, (raw / 'stderr.txt').open('wb') as err:
        process = subprocess.Popen(command, cwd=raw, stdout=out, stderr=err, start_new_session=(os.name == 'posix'))
        try:
            process.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            meta['timed_out'] = True
            if os.name == 'posix': os.killpg(process.pid, signal.SIGKILL)
            else: process.kill()
            process.wait()
    meta.update(exit_code=process.returncode, duration_seconds=time.monotonic()-started)
    (raw / 'metadata.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'raw_directory': str(raw), 'exit_code': meta['exit_code'], 'duration_seconds': meta['duration_seconds'],
                      'timed_out': meta['timed_out']}, indent=2))
    return 0 if meta['exit_code'] == 0 and not meta['timed_out'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
