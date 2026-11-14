from pathlib import Path
import pytest
from experiment_manager.parser import parse_output
from experiment_manager.results import Status
F = Path(__file__).parent/'fixtures'

@pytest.mark.parametrize('name,expected',[('baseline',Status.PROVED),('secret-true',Status.PROVED),
                                         ('secret-unknown',Status.UNKNOWN),('correspondence-false',Status.ATTACK_OR_FALSE)])
def test_actual_proverif_outputs(name,expected):
    result=parse_output((F/f'{name}.stdout.txt').read_text(),(F/f'{name}.stderr.txt').read_text())
    assert result.status==expected
    assert result.queries

def test_trace_with_hypothesis_is_not_an_attack():
    # Real R02 output includes "A trace has been found, assuming ...".
    output=(F/'secret-unknown.stdout.txt').read_text()
    assert 'assuming the following hypothesis' in output
    assert parse_output(output).status==Status.UNKNOWN

@pytest.mark.parametrize('output',['a trace has been found. false true', 'Verification summary: true',
                                  'RESULT unknown new output.', 'PARTIAL RESULT not attacker(x) is true.'])
def test_no_guessing_from_words_or_unrecognized_output(output):
    assert parse_output(output).status==Status.UNKNOWN

@pytest.mark.parametrize('kwargs',[{'exit_code':1},{'stderr':'Error: unknown identifier x'},{'stdout':'Error: syntax error'}])
def test_errors_override_proof(kwargs):
    args={'stdout':'RESULT not attacker(secret) is true.\n'};args.update(kwargs)
    assert parse_output(**args).status==Status.ERROR

def test_timeout_is_unknown_even_with_partial_proof():
    assert parse_output('RESULT not attacker(x) is true.',exit_code=-9,timed_out=True).status==Status.UNKNOWN

def test_diagnostic_false_means_query_false_not_automatic_security_attack():
    result=parse_output('RESULT not event(Server_Finish_Reg(u,r,a,c,k)) is false.\n')
    assert result.status==Status.ATTACK_OR_FALSE
    assert result.queries[0].query.startswith('not event(')

def test_conflicting_results_rejected():
    assert parse_output('RESULT not attacker(x) is true.\nRESULT not attacker(x) is false.').status==Status.ERROR


def test_serialized_statuses_are_plain_strings_for_csv_and_markdown():
    result=parse_output((F/'secret-true.stdout.txt').read_text()).to_dict()
    assert type(result['status']) is str and result['status']=='PROVED'
    assert all(type(q['status']) is str for q in result['queries'])
