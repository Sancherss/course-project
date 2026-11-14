from __future__ import annotations
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from .parser import parse_output

COLUMNS = ['run_id','experiment_id','scenario','ctap','property','entities','fields','token_binding','diagnostic',
           'status','exit_code','timed_out','duration_seconds','proverif_version','commit','reason','raw_directory']

def summarize(raw_root: Path, output: Path) -> Path:
    rows = []
    for metadata in sorted(raw_root.glob('*/metadata.json')):
        d = json.loads(metadata.read_text()); c = d.get('config', {})
        if 'status' not in d:  # baseline script predates the manager
            result = parse_output((metadata.parent/'stdout.txt').read_text(errors='replace'),
                                  (metadata.parent/'stderr.txt').read_text(errors='replace'),
                                  exit_code=d['exit_code'], timed_out=d['timed_out'])
            d.update(result.to_dict())
        row = {k:d.get(k) for k in COLUMNS}
        for k in ('scenario','ctap','property','entities','fields','token_binding','diagnostic'): row[k]=c.get(k)
        row['raw_directory'] = str(metadata.parent.relative_to(raw_root.parent.parent))
        rows.append(row)
    output.mkdir(parents=True,exist_ok=True)
    # New directory per summary invocation; no historical summaries overwritten.
    destination = output / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    destination.mkdir(exist_ok=False)
    (destination/'summary.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    with (destination/'summary.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=COLUMNS);writer.writeheader();writer.writerows(rows)
    def cell(x: object) -> str: return str(x).replace('|','\\|').replace('\n',' ')
    lines=['# Actual run summary','', 'Each row is one execution; ERROR/UNKNOWN are not demonstrated attacks.', '',
           '| Run | Scenario / property | Entities | Binding | Status | Seconds |', '|---|---|---|---|---|---|']
    for row in rows:
        lines.append('| '+' | '.join(map(cell,[row['run_id'],f"{row['scenario']} / {row['property']}",row['entities'],row['token_binding'],row['status'],round(row['duration_seconds'],4)]))+' |')
    (destination/'summary.md').write_text('\n'.join(lines)+'\n')
    return destination
