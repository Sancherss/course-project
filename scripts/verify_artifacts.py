#!/usr/bin/env python3
"""Verify saved evidence without re-running any protocol experiment."""
from pathlib import Path
import hashlib
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiment_manager.parser import parse_output
from experiment_manager.upstream import single_session_model
ROOT=Path(__file__).resolve().parents[1]

def main() -> None:
    from check_environment import check
    environment=check()
    assert environment['ok'], environment
    raw=ROOT/'experiments/raw'
    directories=sorted(p for p in raw.iterdir() if p.is_dir())
    library=(ROOT/'upstream/FIDO2Verif/FIDO2.pvl').read_bytes()
    expected_lib=hashlib.sha256(library).hexdigest()
    results=[]
    binary_matches=True
    witnesses=0
    records=[(d,json.loads((d/"metadata.json").read_text())) for d in directories]
    for d in directories:
        meta=json.loads((d/'metadata.json').read_text())
        assert all((d/n).is_file() for n in ('stdout.txt','stderr.txt','command.txt'))
        for name,expected in meta['input_sha256'].items():
            assert hashlib.sha256((d/name).read_bytes()).hexdigest()==expected, d/name
        assert meta['input_sha256']['FIDO2.pvl']==expected_lib
        assert meta['commit']==environment['commit']
        assert meta['proverif_version']=='2.05'
        binary_matches = binary_matches and meta['executable_sha256']==hashlib.sha256(Path(environment['proverif']).read_bytes()).hexdigest()
        if 'config' in meta:
            generated=ROOT/'experiments/generated'/meta['run_id']
            for name in ('model.pv','FIDO2.pvl'):assert (generated/name).read_bytes()==(d/name).read_bytes()
        result=parse_output((d/'stdout.txt').read_text(),(d/'stderr.txt').read_text(),exit_code=meta['exit_code'],timed_out=meta['timed_out'])
        if meta.get('config',{}).get('single_session_witness'):
            config=meta['config']
            bounded=(d/'model.pv').read_text()
            originals=[source for source,other in records if not other.get('config',{}).get('single_session_witness')
                       and all(other.get('config',{}).get(k)==config[k] for k in ('scenario','ctap','property','entities','fields'))]
            assert originals and any(single_session_model((source/'model.pv').read_text())==bounded for source in originals)
            stdout=(d/'stdout.txt').read_text()
            assert result.status=='ATTACK_OR_FALSE' and 'A trace has been found.' in stdout
            assert 'assuming the following hypothesis' not in stdout
            assert all(q.query.startswith('not event(Server_Finish_') for q in result.queries)
            witnesses+=1
        results.append((meta['run_id'],result.status.value))
    snapshot=ROOT/(ROOT/'evidence/final-summary-location.txt').read_text().strip()
    summary=json.loads((snapshot/'summary.json').read_text())
    assert {r['run_id']:r['status'] for r in summary}==dict(results), 'Snapshot does not reflect raw directories; run summary and update pointer'
    for name,expected in json.loads((ROOT/'evidence/sha256.json').read_text()).items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected, name
    print(json.dumps({'complete_raw_runs':len(directories),'confirmed_single_session_witnesses':witnesses,'all_input_hashes_match':True,
                      'identical_upstream_libraries':True,'summary_matches_raw':True,'upstream_clean':True,'local_binary_matches_recorded':binary_matches},indent=2))

if __name__=='__main__':main()
