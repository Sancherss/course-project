import json
from pathlib import Path
import subprocess
import sys
from experiment_manager.config import ExperimentConfig
from experiment_manager.runner import ROOT,run_experiment,execute
from experiment_manager.report import summarize


def test_isolated_generation_no_overwrite_and_paths_with_spaces(tmp_path):
    project=tmp_path/'project with spaces';project.mkdir()
    (project/'upstream').mkdir()
    (project/'upstream/FIDO2Verif').symlink_to(ROOT/'upstream/FIDO2Verif',target_is_directory=True)
    fake=tmp_path/'fake verifier with spaces'
    fake.write_text(f'#!{sys.executable}\nprint("RESULT not attacker(test_secret) is true.")\n')
    fake.chmod(0o700)
    config=ExperimentConfig(id='test',description='Harness test with fake verifier, not a model result',scenario='reg_client',ctap='getToken',property='S-pintok')
    sentinel=project/'LOG';sentinel.mkdir();(sentinel/'keep').write_text('preserve')
    before=subprocess.check_output(['git','-C',str(ROOT/'upstream/FIDO2Verif'),'status','--porcelain'])
    from dataclasses import replace
    configs=[config,replace(config,precise_actions=True)]
    paths=[run_experiment(c,str(fake),'fake-test-only',root=project) for c in configs]
    assert paths[0]!=paths[1]
    assert (sentinel/'keep').read_text()=='preserve'
    for p in paths:
        meta=json.loads((p/'metadata.json').read_text())
        assert meta['status']=='PROVED' and meta['proverif_version']=='fake-test-only'
        assert meta['input_sha256'] and (p/'model.pv').is_file()
        assert meta['command'][0]==str(fake)
        assert (p/'FIDO2.pvl').read_bytes()==(ROOT/'upstream/FIDO2Verif/FIDO2.pvl').read_bytes()
    assert json.loads((paths[1]/'metadata.json').read_text())['command'][1:4]==['-set','preciseActions','true']
    after=subprocess.check_output(['git','-C',str(ROOT/'upstream/FIDO2Verif'),'status','--porcelain'])
    assert before==after==b''
    a=summarize(project/'experiments/raw',project/'experiments/processed')
    b=summarize(project/'experiments/raw',project/'experiments/processed')
    assert a!=b and len(json.loads((a/'summary.json').read_text()))==2


def test_timeout_and_missing_executable_are_recorded(tmp_path):
    out,err=tmp_path/'out',tmp_path/'err'
    code,timed_out,duration=execute([sys.executable,'-c','import time; time.sleep(2)'],tmp_path,out,err,0.05)
    assert timed_out and code!=0 and duration<2
    code,timed_out,_=execute([str(tmp_path/'absent')],tmp_path,out,err,1)
    assert code==127 and not timed_out and err.read_text()
