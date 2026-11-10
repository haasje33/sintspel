#!/usr/bin/env python3
"""Live HTTP smoke test. Run a dedicated server, e.g. PARTY_PORT=8766 python server.py."""
import json,os,sys,urllib.request,urllib.parse
from pathlib import Path
BASE='http://127.0.0.1:'+os.environ.get('PARTY_PORT','8766')
ROOT=Path(__file__).resolve().parents[1]
KEY=(ROOT/'.host-key').read_text(encoding='utf-8').strip()
def api(path,data={},auth=False):
    headers={'Content-Type':'application/json'}
    if auth:headers['X-Admin-Key']=KEY
    req=urllib.request.Request(BASE+path,json.dumps(data).encode('utf-8'),headers,method='POST')
    with urllib.request.urlopen(req,timeout=8) as r:return json.load(r)['data']
def ad(act,**x):return api('/api/admin',dict(action=act,**x),True)
def get(token=None):
    key=('?key='+KEY if token is None else '?token='+token)
    with urllib.request.urlopen(BASE+'/api/state'+key,timeout=8) as r:return json.load(r)
def main():
    try:
        # Join QR works without a host key and retains the player room code.
        join_url='http://127.0.0.1:'+os.environ.get('PARTY_PORT','8766')+'/play?room=1234'
        qr_url=BASE+'/qr.png?url='+urllib.parse.quote(join_url,safe='')
        with urllib.request.urlopen(qr_url,timeout=8) as response:
            assert response.status==200
            assert response.headers.get_content_type()=='image/png'
            assert response.read(8)==b'\\x89PNG\\r\\n\\x1a\\n'
        ad('v2_reset',confirmation='RESET')
        st=get();assert st['host_authorized'] and st['show']['mode']=='setup'
        assert isinstance(st['show'],dict) and st['show']['hitster_count']>=100
        assert len(st['show']['hitster_cards'])==st['show']['hitster_count']
        with urllib.request.urlopen(BASE+'/api/state',timeout=8) as response:
            tv=json.load(response)
        assert isinstance(tv['show'],dict) and tv['show']['mode']=='setup'
        assert 'hitster_cards' not in tv['show']
        ad('v2_configure',players=[{'name':f'Gezin {i}','target':9} for i in range(1,5)])
        tokens={}
        for p in st['players']:
            resp=api('/api/claim',{'room':st['room'],'player':p['id']})
            tokens[p['id']]=resp['token']
            api('/api/submit',{'action':'v2_story','token':resp['token'],'value':'Een verrassend familieverhaal van '+p['id']})
        ad('v2_start')
        ad('v2_direct',category='dice')
        assert get()['show']['game']['category']=='dice'
        for i,pid in enumerate(tokens):
            api('/api/submit',{'action':'v2_answer','token':tokens[pid],'value':[i+1,2,3,4,5]})
        ad('v2_reveal')
        assert get()['show']['game']['phase']=='reveal'
        ad('v2_next')
        assert get()['show']['game']['index']==1
        ad('v2_cancel')
        assert get()['show']['mode']=='wheel'
        assert get()['show']['remaining_gifts']==36
        print('PASS: HTTP host/session, joining, stories, direct game, player answers, reveal and cancel')
    finally:
        ad('v2_reset',confirmation='RESET')
if __name__=='__main__':main()
