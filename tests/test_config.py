from pathlib import Path
import pytest
from experiment_manager.config import ExperimentConfig,load_matrix
ROOT=Path(__file__).resolve().parents[1]

def base(**kw):
    data=dict(id='x',description='test',scenario='reg_client',ctap='getToken',property='S-pintok')
    data.update(kw);return ExperimentConfig(**data)

@pytest.mark.parametrize('kw',[{'id':'../escape'},{'scenario':'real-site'},{'ctap':'newCTAP'},
                              {'property':'S-wk'},{'entities':(True,)},{'entities':(1,1)},
                              {'fields':('PIN',)},{'timeout_seconds':0},{'token_binding':'invented'}])
def test_reject_unsupported_parameters(kw):
    with pytest.raises(ValueError):base(**kw)

def test_actual_matrix_has_twelve_controlled_comparisons():
    configs=load_matrix(ROOT/'experiments/configs/matrix.yaml')
    assert len(configs)==12
    assert {c.entities for c in configs}=={(),(1,),(2,)}
    assert all(c.ctap=='getToken' and c.fields==() for c in configs)

def test_reject_duplicate_ids(tmp_path):
    from experiment_manager.config import PIN
    p=tmp_path/'matrix.yaml'
    p.write_text(f'upstream_commit: {PIN}\nexperiments:\n'+''.join('  - {id: x, description: t, scenario: reg_client, ctap: getToken, property: S-pintok}\n' for _ in range(2)))
    with pytest.raises(ValueError,match='Duplicate'):load_matrix(p)
