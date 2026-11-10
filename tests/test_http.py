#!/usr/bin/env python3
"""Integration smoke test; server must be running at localhost:8765."""
import json
from pathlib import Path
import urllib.request

BASE='http://127.0.0.1:8765'
ROOT=Path(__file__).resolve().parents[1]
KEY=(ROOT/'.host-key').read_text().strip()

def call(path,data=None,host=False):
    headers={'Content-Type':'application/json'}
    if host:headers['X-Admin-Key']=KEY
    r=urllib.request.Request(BASE+path,json.dumps(data or {}).encode(),headers,method='POST')
    with urllib.request.urlopen(r,timeout=8) as x:return json.load(x)

def get(token=None):
    with urllib.request.urlopen(BASE+'/api/state?'+(('token='+token) if token else ''),timeout=8) as x:return json.load(x)

def admin(action,**kwargs):return call('/api/admin',{'action':action,**kwargs},True)

def run_game(tokens):
    s=get();assert s['mode']=='wheel',s['mode']
    admin('spin');s=get();assert s['mode']=='spinning';category=s['spin']['category']
    admin('start_game');s=get();g=s['game'];kind=g['kind']
    for _ in range(g['total']):
        s=get();g=s['game'];
        if kind=='physical':
            admin('physical_result',winner='p1')
            break
        if kind=='performance':
            performer=g['performer']
            own=get(tokens[performer])['game']
            assert own['private_word']
            assert 'private_word' not in get()['game']
            for pid,token in tokens.items():
                if pid!=performer:call('/api/submit',{'token':token,'value':own['private_word']})
            admin('reveal')
        elif kind=='estimate':
            # No answer is leaked to public state; test uses bank value in state file.
            disk=json.loads((ROOT/'party-state.json').read_text())
            q=disk['game']['questions'][disk['game']['round']]
            assert 'answer' not in g
            for pid,token in tokens.items():call('/api/submit',{'token':token,'value':q['answer']+int(pid[-1])})
            admin('reveal')
        elif kind=='music':
            for pid,token in tokens.items():call('/api/submit',{'token':token,'year':1986+int(pid[-1]),'artist':'Test'})
            if g['source']=='hitster':admin('reveal',year=1988,artist='Test')
            else:admin('reveal')
        elif kind=='creative':
            for pid,token in tokens.items():call('/api/submit',{'token':token,'value':'Onzin antwoord '+pid})
            admin('open_vote')
            for pid,token in tokens.items():
                target='p2' if pid=='p1' else 'p1'
                call('/api/submit',{'token':token,'value':target})
            admin('reveal')
        elif kind=='who':
            for pid,token in tokens.items():call('/api/submit',{'token':token,'value':'p1'})
            admin('reveal')
        assert get()['game']['phase']=='reveal'
        admin('next')
    s=get();assert s['mode']=='gift',s['mode']
    if s['gift']['tied']:
        admin('choose_winner',winner=s['gift']['tied'][0]);s=get()
    assert s['gift']['winner']
    eligible=s['eligible'];assert eligible
    admin('give_gift',recipient=eligible[0]);
    s=get();counts=[p['received'] for p in s['players']]
    assert max(counts)-min(counts)<=1 or any(p['target'] for p in s['players']),(category,counts)
    print(category,'✓',counts)
    return category


def main():
    # Missing/invalid host link must not silently behave as an authenticated host.
    assert get()['host_authorized'] is False
    with urllib.request.urlopen(BASE+'/api/state?key='+KEY,timeout=8) as response:
        assert json.load(response)['host_authorized'] is True
    with urllib.request.urlopen(BASE+'/host',timeout=8) as response:
        assert response.geturl().endswith('/host?key='+KEY)
        assert response.status==200
    print('PASS: host authentication and localhost shortcut')
    s=get()
    if s['mode']!='setup':admin('reset',confirmation='RESET')
    admin('configure',players=[{'name':x,'target':3} for x in ['Ma','Eén','Twee','Drie']])
    tokens={}
    for p in get()['players']:
        result=call('/api/claim',{'room':get()['room'],'player':p['id']})
        tokens[p['id']]=result['data']['token']
    assert all(x['joined'] for x in get()['players'])
    admin('start')
    # Regression: choose Hitster manually, then cancel without prizes or wins.
    before=get()
    assert before['mode']=='wheel'
    admin('start_selected',category='hitster')
    during=get()
    assert during['mode']=='game' and during['game']['category']=='hitster'
    assert during['game']['total']==3
    admin('cancel_game')
    after=get()
    assert after['mode']=='wheel' and after['gifts_given']==0
    assert after['games_played']==0 and all(p['wins']==0 for p in after['players'])
    print('PASS: direct Hitster selection and safe cancellation')
    selected=[run_game(tokens) for _ in range(12)]
    s=get()
    assert s['mode']=='finished'
    assert [p['received'] for p in s['players']]==[3,3,3,3]
    assert len(set(selected[:11]))==11,selected
    print('PASS: 11 kinds, 12 gifts, unique no-repeat cycle, equal distribution')
    # test UNDO before final wheel, reset and targets with uneven amounts
    admin('reset',confirmation='RESET')
    admin('configure',players=[{'name':x,'target':n} for x,n in zip(['Ma','Een','Twee','Drie'],[2,1,2,1])])
    tokens={p['id']:call('/api/claim',{'room':get()['room'],'player':p['id']})['data']['token'] for p in get()['players']}
    admin('start')
    for i in range(6):run_game(tokens)
    assert [p['received'] for p in get()['players']]==[2,1,2,1]
    assert get()['mode']=='finished'
    admin('undo_gift')
    assert get()['mode']=='gift'
    assert sum(p['received'] for p in get()['players'])==5
    admin('give_gift',recipient=get()['eligible'][0])
    assert get()['mode']=='finished'
    print('PASS: unequal personal quotas, final scene, undo gift')
    admin('reset',confirmation='RESET')
    print('Reset successful; server ready for first use.')

if __name__=='__main__':main()
