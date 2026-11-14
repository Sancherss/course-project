from __future__ import annotations
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from .parser import parse_output

COLUMNS = ['run_id','experiment_id','scenario','ctap','property','entities','fields','token_binding','diagnostic','precise_actions','single_session_witness',
           'status','interpretation','exit_code','timed_out','duration_seconds','proverif_version','commit','reason','raw_directory']

def interpret_result(data: dict, stdout: str) -> str:
    """Keep logical RESULT status distinct from the meaning of reachability tests."""
    status = data.get('status')
    config = data.get('config', {})
    if status == 'ERROR': return 'PROCESS_ERROR'
    if status == 'UNKNOWN': return 'INCONCLUSIVE'
    if config.get('diagnostic') and config.get('property') == 'D-finish':
        if status == 'PROVED': return 'FINISH_UNREACHABLE_IN_CHECKED_MODEL'
        queries = data.get('queries', [])
        unconditional_trace = ('A trace has been found.' in stdout
                               and 'assuming the following hypothesis' not in stdout)
        event_query = bool(queries) and all(q['query'].startswith('not event(Server_Finish_') for q in queries)
        if status == 'ATTACK_OR_FALSE' and unconditional_trace and event_query:
            return ('REACHABLE_SINGLE_SESSION_WITNESS' if config.get('single_session_witness')
                    else 'REACHABLE_WITNESS')
        return 'DIAGNOSTIC_WITHOUT_CONFIRMED_WITNESS'
    return 'PROPERTY_PROVED' if status == 'PROVED' else 'PROPERTY_FALSE'


def summarize(raw_root: Path, output: Path) -> Path:
    rows = []
    for metadata in sorted(raw_root.glob('*/metadata.json')):
        d = json.loads(metadata.read_text()); c = d.get('config', {})
        if d.get('generator_exit_code', 0) == 0:
            result = parse_output((metadata.parent/'stdout.txt').read_text(errors='replace'),
                                  (metadata.parent/'stderr.txt').read_text(errors='replace'),
                                  exit_code=d['exit_code'], timed_out=d['timed_out'])
            d.update(result.to_dict())
        d['interpretation'] = interpret_result(d, (metadata.parent/'stdout.txt').read_text(errors='replace'))
        row = {k:d.get(k) for k in COLUMNS}
        for k in ('scenario','ctap','property','entities','fields','token_binding','diagnostic','precise_actions','single_session_witness'): row[k]=c.get(k)
        row['raw_directory'] = str(metadata.parent.relative_to(raw_root.parent.parent))
        rows.append(row)
    output.mkdir(parents=True,exist_ok=True)
    # New directory per summary invocation; no historical summaries overwritten.
    destination = output / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    destination.mkdir(exist_ok=False)
    import hashlib
    (destination/'parser-provenance.json').write_text(json.dumps({'parser_sha256': hashlib.sha256((Path(__file__).parent/'parser.py').read_bytes()).hexdigest(), 'report_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'classification': 'Reparsed from immutable raw stdout/stderr/exit_code/timeout using the current parser; raw metadata retains its original classification.'}, indent=2)+'\n')
    (destination/'summary.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    with (destination/'summary.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=COLUMNS);writer.writeheader();writer.writerows(rows)
    def cell(x: object) -> str: return str(x).replace('|','\\|').replace('\n',' ')
    lines=['# Actual run summary','', 'Each row is one execution; ERROR/UNKNOWN are not demonstrated attacks.', '',
           '| Run | Scenario / property | Entities | Single session | Status | Interpretation | Seconds |', '|---|---|---|---|---|---|---|']
    for row in rows:
        lines.append('| '+' | '.join(map(cell,[row['run_id'],f"{row['scenario']} / {row['property']}",row['entities'],row['single_session_witness'],row['status'],row['interpretation'],round(row['duration_seconds'],4)]))+' |')
    (destination/'summary.md').write_text('\n'.join(lines)+'\n')
    return destination
