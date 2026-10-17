"""Local authorization and evidence-scope regressions for the V0 viewer."""
from fastapi.testclient import TestClient
from server import app, AUDIT_FRAMES

c = TestClient(app)


def session(role):
    r = c.post('/api/session', json={'role': role})
    assert r.status_code == 200, r.text
    return r.json()


def action(sid, kind, **kw):
    return c.post(f'/api/session/{sid}/act', json={'kind': kind, **kw})


def test_audit():
    a=session('audit'); sid=a['session']; assert a['length']>=10
    assert action(sid,'set',x=3,y=4).status_code == 403
    f=c.post(f'/api/session/{sid}/frame/11').json()['frame']
    assert f['tick']==31
    assert sum(len(q['event']['effects']) for q in AUDIT_FRAMES if q['event'])>0
    assert all(x['energy']['total']==a['frame']['energy']['total'] for x in AUDIT_FRAMES)
    print('PASS audit immutable timeline, recorded kernel events, conservation')


def test_agent():
    a=session('agent');sid=a['session']
    forbidden_fields={'frame','energy','heat','sources','bonds','particles','hash','tick','events'}
    assert not (forbidden_fields & a.keys())
    assert action(sid,'drop',x=1,y=1).status_code == 403
    assert action(sid,'replace',x=1,y=1).status_code == 403
    assert action(sid,'remove',x=1,y=1).status_code == 403
    assert action(sid,'set',x=5,y=5).json()['actions'][-1]['result'].startswith('refused')
    obs=action(sid,'observe',x=6,y=7).json()
    assert obs['actions'][-1]['result']=='ok'
    assert len(obs['observed'])==1 and obs['observed'][0]['radius']==3
    assert all(abs(p['x']-6)<=3 and abs(p['y']-7)<=3 for p in obs['observed'][0]['particles'])
    exported=c.get(f'/api/session/{sid}/export').json()
    assert not (forbidden_fields & exported.keys())
    print('PASS human agent receives only local paid observation; no god access')


def test_experiment():
    a=session('experiment');sid=a['session']
    assert action(sid,'set',x=3,y=4).status_code == 403
    assert action(sid,'claim',x=3,y=4).status_code == 403
    d=action(sid,'drop',x=1,y=1,species='S',direction='N').json()
    assert d['events'][-1]['environment'] == [['drop',[1,1],'S','N']]
    assert d['frame']['energy']['total']==a['frame']['energy']['total']
    d=action(sid,'remove',x=1,y=1).json()
    assert d['events'][-1]['environment']==[['remove',[1,1]]]
    assert d['frame']['energy']['total']==a['frame']['energy']['total']
    print('PASS experiment clone: only logged boundary ops, no control writes')


if __name__=='__main__':
    test_audit();test_agent();test_experiment()
    print('VIEWER API: PASS')
