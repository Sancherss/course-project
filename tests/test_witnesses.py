"""Regression checks against actual generated models and replayable verifier traces."""
from pathlib import Path
import json
import pytest
from experiment_manager.config import ExperimentConfig
from experiment_manager.parser import parse_output
from experiment_manager.report import interpret_result
from experiment_manager.upstream import single_session_model
ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('witness,original',[
    ('W-reg-E0','D-reg_client-E0'),('W-reg-E2','D-reg_client-E2'),('W-auth-E0','D-auth_client_em-E0')])
def test_positive_witness_embeds_by_restoring_the_single_root_replication(witness,original):
    raw=ROOT/'experiments/raw'
    def find(id):
        return next(p.parent for p in raw.glob('*/metadata.json') if json.loads(p.read_text())['experiment_id']==id)
    bounded,unbounded=find(witness),find(original)
    b=(bounded/'model.pv').read_text();u=(unbounded/'model.pv').read_text()
    assert single_session_model(u)==b
    assert b.replace('system(G,skat', '!system(G,skat',1)==u  # root call, not the typed definition
    assert (bounded/'FIDO2.pvl').read_bytes()==(unbounded/'FIDO2.pvl').read_bytes()
    stdout=(bounded/'stdout.txt').read_text()
    result=parse_output(stdout,(bounded/'stderr.txt').read_text())
    data=json.loads((bounded/'metadata.json').read_text());data.update(result.to_dict())
    assert result.status=='ATTACK_OR_FALSE'
    assert 'assuming the following hypothesis' not in stdout
    assert interpret_result(data,stdout)=='REACHABLE_SINGLE_SESSION_WITNESS'


def test_bounded_mode_cannot_be_used_to_report_an_unbounded_security_proof():
    with pytest.raises(ValueError,match='restricted'):
        ExperimentConfig(id='invalid',description='invalid',scenario='reg_client',ctap='getToken',property='A6',single_session_witness=True)


def test_reject_unexpected_replication_layout():
    with pytest.raises(ValueError):single_session_model('process 0')
    with pytest.raises(ValueError):single_session_model('!system(a)|!system(b)')


def test_hypothetical_diagnostic_trace_is_not_a_confirmed_witness():
    data={'status':'ATTACK_OR_FALSE','config':{'diagnostic':True,'property':'D-finish'},
          'queries':[{'query':'not event(Server_Finish_Reg(u,r,a,c,k))'}]}
    assert interpret_result(data,'A trace has been found, assuming the following hypothesis: x')=='DIAGNOSTIC_WITHOUT_CONFIRMED_WITNESS'
