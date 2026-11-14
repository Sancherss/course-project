from __future__ import annotations
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
import sys
import tempfile
import time
import uuid
from .config import ExperimentConfig, PIN
from .parser import parse_output
from .results import Status

ROOT = Path(__file__).resolve().parents[1]

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def execute(command: list[str], cwd: Path, stdout_path: Path, stderr_path: Path, timeout: float) -> tuple[int, bool, float]:
    start = time.monotonic()
    with stdout_path.open('wb') as out, stderr_path.open('wb') as err:
        try:
            p = subprocess.Popen(command, cwd=cwd, stdout=out, stderr=err, start_new_session=(os.name == 'posix'))
        except OSError as exc:
            err.write((str(exc)+'\n').encode()); return 127, False, time.monotonic()-start
        timed_out = False
        try: p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == 'posix':
                try: os.killpg(p.pid, signal.SIGKILL)
                except ProcessLookupError: pass
            else: p.kill()
            p.wait()
    return p.returncode, timed_out, time.monotonic()-start


def run_experiment(config: ExperimentConfig, executable: str, version: str, *, root: Path = ROOT) -> Path:
    root = root.resolve()
    upstream = root / 'upstream/FIDO2Verif'
    commit = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()
    if commit != PIN or subprocess.check_output(['git', '-C', str(upstream), 'status', '--porcelain'], text=True).strip():
        raise ValueError('Upstream must be clean and pinned')
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+config.id+'-'+uuid.uuid4().hex[:8]
    raw = root / 'experiments/raw' / run_id
    generated = root / 'experiments/generated' / run_id
    raw.mkdir(parents=True, exist_ok=False); generated.mkdir(parents=True, exist_ok=False)
    (raw / 'config.json').write_text(json.dumps(config.to_dict(), ensure_ascii=False, indent=2)+'\n')
    env = dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTHONPATH'] = str(ROOT) + os.pathsep + env.get('PYTHONPATH', '')
    generator_command = [sys.executable, '-m', 'experiment_manager.upstream', str(raw/'config.json'), str(upstream), str(generated)]
    with tempfile.TemporaryDirectory(prefix='fido2-generate-') as scratch:
        try:
            generation = subprocess.run(generator_command, cwd=scratch, env=env, capture_output=True, timeout=30)
        except subprocess.TimeoutExpired as exc:
            generation = subprocess.CompletedProcess(generator_command, 124, exc.stdout or b'', (exc.stderr or b'') + b'Generation timeout\n')
    (raw/'generator_stdout.txt').write_bytes(generation.stdout)
    (raw/'generator_stderr.txt').write_bytes(generation.stderr)
    command = [str(Path(executable).resolve())]
    if config.precise_actions:
        command += ['-set', 'preciseActions', 'true']
    command += ['-lib', 'FIDO2.pvl', 'model.pv']
    (raw/'command.txt').write_text(shlex.join(command)+'\n')
    meta = {'run_id': run_id, 'experiment_id': config.id, 'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'commit': commit, 'manager_commit': subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),
            'config': config.to_dict(), 'command': command, 'cwd': str(raw), 'generator_command': generator_command,
            'generator_exit_code': generation.returncode, 'manager_sources_sha256': {str(p.relative_to(ROOT)): digest(p) for p in sorted((ROOT/'experiment_manager').glob('*.py'))}, 'proverif_version': version, 'os': platform.platform(),
            'python': platform.python_version(), 'executable_sha256': digest(Path(executable)), 'input_sha256': {}}
    if generation.returncode:
        (raw/'stdout.txt').write_text(''); (raw/'stderr.txt').write_bytes(generation.stderr)
        meta.update(exit_code=None, timed_out=False, duration_seconds=0, status=Status.ERROR,
                    reason='Model generation failed', queries=[], warnings=[])
    else:
        for name in ('model.pv', 'FIDO2.pvl'):
            shutil.copy2(generated/name, raw/name); meta['input_sha256'][name] = digest(raw/name)
        code, timed_out, duration = execute(command, raw, raw/'stdout.txt', raw/'stderr.txt', config.timeout_seconds)
        result = parse_output((raw/'stdout.txt').read_text(errors='replace'), (raw/'stderr.txt').read_text(errors='replace'), exit_code=code, timed_out=timed_out)
        meta.update(exit_code=code, timed_out=timed_out, duration_seconds=duration, **result.to_dict())
    (raw/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    return raw
