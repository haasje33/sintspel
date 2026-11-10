"""Sintspel 2.0 game engine. Pure standard-library logic; old QR import remains intact.

Show state belongs to party-state.json. Treat player-controlled submissions as untrusted.
"""
from __future__ import annotations

import copy
import difflib
import random
import re
import secrets
import hashlib
import json
import time
import unicodedata

RNG = random.SystemRandom()
GAMES = [
    {'id':'classic','name':'Hitster Classic','icon':'🎵','color':'#c87d62','type':'music'},
    {'id':'quiz','name':'Hitster Quiz','icon':'🎤','color':'#9c6baf','type':'music'},
    {'id':'quiplash','name':'Quiplash','icon':'💬','color':'#d0a05f','type':'creative'},
    {'id':'three','name':'Wie van de 3?','icon':'🕵️','color':'#6896a8','type':'social'},
    {'id':'dice','name':'Yahtzee-sprint','icon':'🎲','color':'#729c78','type':'physical'},
    {'id':'cards','name':'Kaartenduel','icon':'🃏','color':'#c37086','type':'cards'},
    {'id':'taboo','name':'Verboden woord','icon':'🤫','color':'#bc9561','type':'words'},
]
GAME_IDS = {g['id'] for g in GAMES}
ERAS = [('60s & 70s',1960,1979,1970),('80s & 90s',1980,1999,1990),
        ('00s & 10s',2000,2019,2010),('20s',2020,2029,None)]
TYPES = ['artist','title','year5','year3','boundary']
QUIZ_TYPES = {'artist':'Artiest','title':'Titel','year5':'Jaartal ±5 jaar',
              'year3':'Jaartal ±3 jaar','boundary':'Vóór of vanaf het referentiejaar'}
DIFFICULTY = {'easy':1,'medium':2,'hard':4}
DICE_RULES = [('sum','Hoogste som — één worp'),
              ('pairs','Meeste gelijke dobbelstenen'),
              ('target','Meeste dobbelstenen met het gevraagde cijfer'),
              ('straight','Langste straat')]
QUIPS = [
 'Wat is het allerslechtste excuus om een cadeau niet uit te pakken?',
 'Welke regel zou Sinterklaas invoeren als hij dictator werd?',
 'Wat staat er op een waarschuwingsetiket voor jouw familie?',
 'Wat is de meest onhandige tekst op een chocoladeletter?',
 'Waarom werd de stoomboot de haven uitgezet?',
 'Welke volstrekt nutteloze uitvinding hoort bij jou?',
 'Wat zou je nooit op je verlanglijstje durven zetten?',
 'Welke nieuwe feestdag zou absoluut geen succes worden?',
 'Wat staat er op de achterkant van je denkbeeldige autobiografie?',
 'Waarom zou jij na één dag als hulpsint worden ontslagen?',
 'Wat is de slechtst denkbare naam voor een gezellig café?',
 'Wat is de raarste reden om tijdens het eten de tafel te verlaten?',
 'Welk onderwerp zou het slechtst zijn voor een familiequiz?',
 'Wat is de meest overtuigende leugen over je leeftijd?',
 'Welke zin zou een robot-Sinterklaas absoluut niet moeten zeggen?',
 'Waarvoor zou jouw familie een standbeeld verdienen?',
 'Wat zou er gebeuren als pepernoten konden praten?',
 'Wat is de slechtste openingszin op een familiefeest?',
 'Wat is een belachelijk goede naam voor een schoonmaakproduct?',
 'Waarop zou je niet willen worden beoordeeld in een wedstrijd?',
]
WORDS = [
 ('Sinterklaas',['baard','cadeau','stoomboot'],['sint']),
 ('afstandsbediening',['televisie','knoppen','zappen'],['remote']),
 ('koelkast',['koud','keuken','eten'],[]),
 ('verjaardag',['taart','feest','leeftijd'],[]),
 ('vliegtuig',['lucht','vliegen','piloot'],[]),
 ('fiets',['trappen','stuur','wielen'],[]),
 ('pannenkoek',['stroop','beslag','bakken'],[]),
 ('paraplu',['regen','nat','open'],[]),
 ('bibliotheek',['boeken','lenen','stil'],[]),
 ('wasmachine',['kleren','wassen','trommel'],[]),
 ('tandarts',['tanden','boren','mond'],[]),
 ('vuurwerk',['knallen','nieuwjaar','licht'],[]),
 ('verrekijker',['ver','kijken','ogen'],[]),
 ('zaklamp',['licht','batterij','donker'],[]),
 ('koffiezetapparaat',['koffie','water','filter'],[]),
 ('snelkookpan',['pan','druk','koken'],[]),
 ('brievenbus',['post','brief','deur'],[]),
 ('schommel',['speeltuin','heen en weer','zitten'],[]),
 ('sneeuwpop',['winter','wortel','sneeuw'],[]),
 ('supermarkt',['boodschappen','winkel','kassa'],[]),
 ('rollator',['lopen','wielen','steun'],[]),
 ('stofzuiger',['schoonmaken','vloer','zuigen'],[]),
 ('voetbal',['bal','goal','sport'],[]),
 ('kapper',['haar','knippen','salon'],[]),
]
GROCERIES = [
 'brood','melk','boter','kaas','eieren','appels','bananen','wortels','tomaten','aardappelen',
 'rijst','pasta','suiker','zout','peper','koffie','thee','chocolade','yoghurt','beschuit',
 'jam','honing','pindakaas','hagelslag','sap','sinaasappels','druiven','peren','komkommer',
 'paprika','sla','ui','knoflook','champignons','courgette','bloemkool','broccoli',
 'spinazie','bonen','erwten','mais','tonijn','zalm','kipfilet','worst','gehakt','soep',
 'crackers','koekjes','chips','noten','olijven','augurken','mosterd','mayonaise','ketchup',
 'azijn','olie','bloem','havermout','muesli','ijs','vla','room','tandpasta',
 'shampoo','zeep','afwasmiddel','wasmiddel','toiletpapier','keukenpapier',
]


def norm(s,artist=False):
    s=''.join(c for c in unicodedata.normalize('NFKD',str(s or '').casefold()) if not unicodedata.combining(c))
    s=re.sub(r'\b(and|en)\b|&',' & ',s)
    s=re.sub(r'[^a-z0-9&]+',' ',s).strip()
    s=re.sub(r'\s+',' ',s)
    if artist:s=re.sub(r'^the\s+','',s)
    return s


def same_answer(guess,answer,kind='title',aliases=None):
    """Lenient but not indiscriminate: clear aliases, artist components, small typos."""
    artist=kind=='artist'
    q=norm(guess,artist)
    if not q:return False
    targets=[answer]+list(aliases or [])
    if kind=='title':
        # Documented, widely used alternatives; kept separate from official metadata.
        known={'the best':['simply the best'],'johnny b goode':['johnny be good','johnny b good']}
        targets.extend(known.get(norm(answer),[]))
    if artist:
        for item in list(targets):
            targets.extend(re.split(r'\s+&\s+|\s+(?:feat|featuring|ft)\s+',item,flags=re.I))
    for target in targets:
        t=norm(target,artist)
        if not t:continue
        if q==t:return True
        # Safe exact distinctive substring, never accept one generic word.
        if len(q)>=9 and len(q.split())>=2 and (q in t or t in q):
            if min(len(q),len(t))/max(len(q),len(t))>=0.72:return True
        if len(q)>=6 and len(t)>=6:
            ratio=difflib.SequenceMatcher(None,q,t).ratio()
            threshold=.84 if min(len(q),len(t))>=12 else .88
            if ratio>=threshold and abs(len(q)-len(t))<=max(2,int(max(len(q),len(t))*.23)):
                return True
    return False


def new_show():
    return {'version':2,'mode':'setup','bag':[],'used_hidden':[],'recent':[],
            'game':None,'spin':None,'spin_turn':0,'disabled_games':[],'grocery':{'phase':'pending','items':[],
            'first_after':RNG.choice([1,2]),'recall_after':None,'deadline':None,
            'responses':{},'review':{}},
            'regular_completed':0,'gifts_given':0,'gift':None,'last_gift':None,
            'stories':{},'aliases':{},'round_history':[],'started_at':None,'category_turn':0}


def ensure(s):
    if s.get('show2',{}).get('version')!=2:
        s['show2']=new_show()
    sh=s['show2']
    sh.setdefault('stories',{})
    sh.setdefault('aliases',{})
    sh.setdefault('spin_turn',0)  # Existing saved evenings predate phone wheel turns.
    sh.setdefault('disabled_games',[])
    return sh


def load_packaged_library(s,path):
    """Load the checked QR collection, honoring its metadata over old imports.

    QR payloads are preserved verbatim: physical cards can contain a bare
    ``www.example.com/...`` string rather than an HTTP scheme. A separate
    exclusion list removes known mislinked physical cards from old sessions.
    """
    if not path.is_file():return 0
    try:
        payload=json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError,ValueError,UnicodeError) as exc:
        raise ValueError('De meegeleverde muziekbibliotheek is ongeldig.') from exc
    if isinstance(payload,dict):
        entries=payload.get('cards',[])
        excluded=payload.get('excluded_urls',[])
    elif isinstance(payload,list):
        entries=payload
        excluded=[]
    else:
        raise ValueError('Muziekbibliotheek moet een lijst of kaartenobject zijn.')
    if not isinstance(entries,list) or not isinstance(excluded,list):
        raise ValueError('Muziekbibliotheek heeft ongeldige kaarten of uitsluitingen.')

    def identity(url):
        return re.sub(r'^https?://','',str(url).strip(),flags=re.I).casefold()

    def valid(url):
        # Historical QR payloads use scheme-less www hostnames; do not alter
        # their bytes by prepending https:// during import or QR generation.
        if any(c.isspace() or ord(c)<32 for c in url) or len(url.encode('utf-8'))>1500:
            return False
        if re.match(r'^https?://[^/\s]+/',url,re.I):return True
        return bool(re.match(r'^www\.[a-z0-9.-]+\.[a-z]{2,}/[^\s]+$',url,re.I))

    excluded_keys={identity(x) for x in excluded if isinstance(x,str) and valid(x)}
    existing=s.setdefault('hitster_cards',[])
    existing[:]=[c for c in existing if identity(c.get('url','')) not in excluded_keys]
    indexed={identity(c.get('url','')):c for c in existing if c.get('url')}
    added=0
    for item in entries:
        if not isinstance(item,dict):continue
        url=str(item.get('url','')).strip()
        title=str(item.get('title','')).strip()
        artist=str(item.get('artist','')).strip()
        try:year=int(item.get('year',0))
        except (ValueError,TypeError):continue
        if not valid(url) or not artist or not title or not 1900<=year<=2100 or identity(url) in excluded_keys:
            continue
        key=identity(url)
        if key in indexed:
            # Correct stale years or spelling in earlier local imports.
            indexed[key].update({'url':url,'artist':artist,'title':title,'year':year})
            continue
        stable=hashlib.sha256(url.encode('utf-8')).hexdigest()[:32]
        record={'id':stable,'url':url,'artist':artist,'title':title,'year':year}
        existing.append(record)
        indexed[key]=record
        added+=1
    return added

def player(s,pid):return next((p for p in s['players'] if p['id']==pid),None)
def player_ids(s):return [p['id'] for p in s['players']]
def all_done(s):return all(p['received']>=p['target'] for p in s['players'])
def remaining(s):return sum(max(0,p['target']-p['received']) for p in s['players'])


def available(s,exclude=None):
    options=[p for p in s['players'] if p['received']<p['target'] and p['id']!=exclude]
    if not options:return []
    low=min(p['received'] for p in options)
    return [p['id'] for p in options if p['received']==low]


def used_hidden_card(s):
    return set(ensure(s)['used_hidden'])


def choose_hidden(s,cards):
    sh=ensure(s)
    unseen=[c for c in cards if c['id'] not in sh['used_hidden']]
    if not unseen:
        sh['used_hidden']=[]
        unseen=list(cards)
    c=RNG.choice(unseen)
    sh['used_hidden'].append(c['id'])
    return c


def find_classic(s,level,select=True):
    cards=s.get('hitster_cards',[])
    if len(cards)<3:return None
    sh=ensure(s)
    unseen=[c for c in cards if c['id'] not in sh['used_hidden']]
    if not unseen:unseen=cards
    candidates=[]
    # Rejection sampling is more efficient than all O(N^3) triples for 100+ cards.
    for _ in range(2300):
        h=RNG.choice(unseen)
        r=RNG.sample([c for c in cards if c['id']!=h['id']],2)
        years=sorted([h['year'],r[0]['year'],r[1]['year']])
        if len(set(years))<3:continue
        close=min(abs(h['year']-r[0]['year']),abs(h['year']-r[1]['year']))
        ok={'easy':close>=12,'medium':5<=close<=11,'hard':close<=4}[level]
        if ok:
            candidates.append((h,r))
            if len(candidates)>=18:break
    if not candidates:return None
    if not select:return True
    h,r=RNG.choice(candidates)
    ref=sorted(r,key=lambda c:c['year'])
    pos=['left','middle','right'][sum(c['year']<h['year'] for c in ref)]
    if h['id'] not in sh['used_hidden']:sh['used_hidden'].append(h['id'])
    return {'hidden_id':h['id'],'ref':[{'id':c['id'],'title':c['title'],'artist':c['artist'],'year':c['year']} for c in ref],
            'correct':pos,'year':h['year'],'artist':h['artist'],'title':h['title'],'level':level,
            'answer':{},'grades':{},'points':{},'revealed':False}


def pool_for_era(s,name):
    era=next((e for e in ERAS if e[0]==name),None)
    if not era:return []
    return [c for c in s.get('hitster_cards',[]) if era[1]<=c['year']<=era[2]]


def make_quiz_round(s,era_name):
    cards=pool_for_era(s,era_name)
    if not cards:return None
    h=choose_hidden(s,cards)
    era=next(e for e in ERAS if e[0]==era_name)
    typ=RNG.choice([t for t in TYPES if t!='boundary' or era[3] is not None])
    return {'hidden_id':h['id'],'era':era_name,'question_type':typ,'year':h['year'],
            'artist':h['artist'],'title':h['title'],'boundary':era[3],
            'answer':{},'grades':{},'points':{},'revealed':False}


def make_round(s,cat,i=0,game=None):
    ids=player_ids(s)
    if cat in ('classic','quiz'):
        return {'chooser':ids[(game['turn_start']+i)%4],
                'answer':{},'grades':{},'points':{},'revealed':False}
    if cat=='quiplash':
        return {'prompt':game['prompts'][i],'answer':{},'votes':{},'grades':{},'points':{},'revealed':False}
    if cat=='three':
        return {'investigator':ids[(game['turn_start']+i)%4],'owner':ids[(game['turn_start']+i+1)%4],
                'story':ensure(s)['stories'][ids[(game['turn_start']+i+1)%4]],'questions_used':0,'guess':None,
                'answer':{},'grades':{},'points':{},'revealed':False}
    if cat=='dice':
        kind=game['round_types'][i]
        return {'rule':kind,'target':RNG.randrange(1,7) if kind=='target' else None,
                'answer':{},'grades':{},'points':{},'revealed':False}
    if cat=='cards':
        # Each deal comes from a fresh shuffle, but values must allow both outcomes.
        while True:
            deck=RNG.sample([(v,suit) for v in range(2,15) for suit in 'HDCS'],52)
            first=deck[0]
            second=next(x for x in deck[1:] if abs(x[0]-first[0])>=2)
            third=next(x for x in deck[1:] if x not in (first,second) and x[0] not in (first[0],second[0]))
            fourth=next(x for x in deck[1:] if x not in (first,second,third))
            break
        return {'cards':[{'v':x[0],'s':x[1]} for x in [first,second,third,fourth]],
                'stage':0,'alive':ids[:],'stage_alive':ids[:], 'answers_by_stage':[],
                'answer':{},'grades':{},'points':{},'revealed':False,'deal_finished':False}
    if cat=='taboo':
        v=game['word_order'][i]
        return {'performer':ids[(game['turn_start']+i)%4],
                'word':v[0],'banned':v[1],'aliases':v[2],
                'started_at':None,'deadline':None,'attempts':{},'grades':{},'points':{},'revealed':False}
    raise ValueError('Onbekende spelsoort')


def make_game(s,category):
    if category not in GAME_IDS:raise ValueError('Onbekend spel.')
    sh=ensure(s)
    if category=='three':
        missing=[p['name'] for p in s['players'] if not sh['stories'].get(p['id'],'').strip()]
        if missing:raise ValueError('Vul vóór Wie van de 3? eerst vier persoonlijke weetjes in: '+', '.join(missing))
    if category in ('classic','quiz') and not s.get('hitster_cards'):
        raise ValueError('Importeer eerst muziekkaarten om dit spel te starten.')
    if category=='classic' and len(s.get('hitster_cards',[]))<3:
        raise ValueError('Voor Muziek Classic zijn minstens drie muziekkaarten nodig.')
    game={'category':category,'phase':'choose' if category in ('classic','quiz') else 'answer',
          'round_index':0,'total':8 if category in ('classic','quiz','dice','cards','taboo') else 4,
          'rounds':[],'scores':{pid:0 for pid in player_ids(s)},'started_at':time.time(),
          'turn_start':sh['category_turn'],'pre_used':sh['used_hidden'][:]}
    if category=='quiplash':game['prompts']=RNG.sample(QUIPS,4)
    if category=='dice':game['round_types']=RNG.sample([x for x,_ in DICE_RULES]*2,8)
    if category=='taboo':game['word_order']=RNG.sample(WORDS,8)
    game['rounds'].append(make_round(s,category,0,game))
    sh['category_turn']=(sh['category_turn']+1)%4
    return game


def current(sh):
    g=sh.get('game')
    return (g,g['rounds'][g['round_index']]) if g else (None,None)


def recompute(s):
    g=ensure(s)['game']
    if not g:return
    pids=player_ids(s)
    g['scores']={pid:0 for pid in pids}
    for r in g['rounds']:
        for pid,points in r.get('points',{}).items():g['scores'][pid]+=points


def award_round(s):
    sh=ensure(s);g,r=current(sh);cat=g['category'];ids=player_ids(s)
    pts={pid:0 for pid in ids};grades={}
    if cat=='classic':
        for pid,ans in r['answer'].items():
            correct=ans==r['correct']
            grades[pid]={'guess':ans,'accepted':correct,'auto':correct}
            if correct:pts[pid]=DIFFICULTY[r['level']]
    elif cat=='quiz':
        for pid,ans in r['answer'].items():
            typ=r['question_type']
            if typ in ('title','artist'):
                alias=sh.get('aliases',{}).get(typ+':'+str(r['hidden_id']),[])
                correct=same_answer(ans,r[typ],typ,alias)
            elif typ.startswith('year'):
                try:correct=abs(int(ans)-r['year']) <= (5 if typ=='year5' else 3)
                except (ValueError,TypeError):correct=False
            else:correct=str(ans)==('before' if r['year']<r['boundary'] else 'after')
            grades[pid]={'guess':ans,'accepted':correct,'auto':correct}
            if correct:pts[pid]=1
    elif cat=='quiplash':
        tally={pid:0 for pid in ids}
        for pid,target in r['votes'].items():
            if target in tally and target!=pid:tally[target]+=1
        top=max(tally.values(),default=0)
        if top>0:
            for pid,n in tally.items():
                if n==top:pts[pid]=1
        grades={'vote_counts':tally}
    elif cat=='dice':
        values={pid:v for pid,v in r['answer'].items() if len(v)==5}
        active={}
        for pid,dice in values.items():
            if len(set(dice))==1:
                pts[pid]=3
                grades[pid]={'guess':dice,'accepted':True,'yahtzee':True}
            else:
                active[pid]=dice
                grades[pid]={'guess':dice,'accepted':False,'yahtzee':False}
        if active:
            rule=r['rule'];target=r['target']
            def measure(a):
                if rule=='sum':return (sum(a),)
                if rule=='pairs':return (max(a.count(x) for x in set(a)),)
                if rule=='target':return (a.count(target),)
                if rule=='straight':
                    v=sorted(set(a));best=run=1
                    for i in range(1,len(v)):
                        run=run+1 if v[i]==v[i-1]+1 else 1
                        best=max(run,best)
                    return (best,)
                return (0,)
            ranks={pid:measure(a) for pid,a in active.items()}
            mx=max(ranks.values())
            for pid,rank in ranks.items():
                if rank==mx:
                    pts[pid]+=1
                    grades[pid]['accepted']=True
                grades[pid]['rank']=rank[0]
    elif cat=='taboo':
        guesses=r.get('attempts',{})
        for pid,attempts in guesses.items():
            if pid==r['performer']:continue
            accepted=any(same_answer(a,r['word'],'title',r['aliases']) for a in attempts)
            old=r.get('grades',{}).get(pid,{})
            if old.get('manual') is not None:accepted=old['manual']
            grades[pid]={'guess':attempts[-1] if attempts else '', 'all_attempts':attempts,
                         'accepted':accepted,'auto':accepted,'manual':old.get('manual')}
            if accepted:pts[pid]+=1
        if any(pts.values()):pts[r['performer']]+=1
    elif cat=='cards':
        # At each reveal only stage winners are determined; deal winner is recorded.
        for pid in r.get('deal_winners',[]):pts[pid]=1
    elif cat=='three':
        if r.get('guess'):
            if r['guess']==r['owner']:pts[r['investigator']]=3
            else:
                for pid in ids:
                    if pid!=r['investigator']:pts[pid]=1
    r['points']=pts;r['grades']=grades;r['revealed']=True
    recompute(s)


def gift_start(s,winners,category):
    sh=ensure(s)
    sh['gift']={'winners':winners,'winner_index':0,'choice_index':0,
                'category':category,'awarded':[]}
    sh['last_gift']=None  # Undo must never apply to the preceding game.
    sh['game']=None
    sh['mode']='gift'


def trigger_transition(s):
    sh=ensure(s);gr=sh['grocery']
    if all_done(s):
        sh['mode']='finished';return
    if gr['phase']=='pending' and sh['regular_completed']>=gr['first_after']:
        gr['phase']='alarm_intro';gr['items']=RNG.sample(GROCERIES,20)
        gr['recall_after']=sh['regular_completed']+RNG.randint(2,4)
        sh['mode']='grocery_alarm';return
    if gr['phase']=='waiting' and (sh['regular_completed']>=gr['recall_after'] or remaining(s)<=6):
        gr['phase']='alarm_recall';sh['mode']='grocery_alarm';return
    sh['mode']='wheel'


def gift_next(s):
    sh=ensure(s);gift=sh['gift']
    if not gift:return
    if gift['winner_index']>=len(gift['winners']) or remaining(s)<=0:
        category=gift['category']
        sh['round_history'].append({'category':category,'winners':gift['winners'],
                                    'points':gift.get('scores',{}),'at':time.time()})
        if category!='grocery':sh['regular_completed']+=1
        sh['gift']=None
        trigger_transition(s)


def return_to_wheel(s, disabled=False):
    """Emergency exit for the host, independent of normal game phase guards.

    An unfinished game is replayable and its wheel turn is restored. During
    gifting, only unissued rewards are skipped; physical gifts already given
    remain registered. A faulty groceries event cannot trap the evening.
    """
    sh=ensure(s)
    mode=sh['mode']
    if mode in ('setup','finished'):
        raise ValueError('Het spelrad is niet beschikbaar buiten een lopende spelavond.')
    if mode in ('spinning','game'):
        g=sh.get('game')
        if g:
            category=g['category']
            if category not in sh['bag'] and category not in sh['disabled_games']:
                sh['bag'].append(category)
            sh['used_hidden']=list(g.get('pre_used',sh['used_hidden']))
            if sh['recent'] and sh['recent'][-1]==category:sh['recent'].pop()
        spin=sh.get('spin') or {}
        if not disabled and spin.get('turn_before') is not None:
            sh['spin_turn']=spin['turn_before']
    elif mode=='gift':
        gift=sh.get('gift')
        if gift:
            category=gift['category']
            sh['round_history'].append({'category':category,'winners':gift['winners'],
                       'points':gift.get('scores',{}),'at':time.time(),'gifts_skipped':True})
            if category!='grocery':sh['regular_completed']+=1
    elif mode.startswith('grocery_'):
        gr=sh['grocery']
        # A broken surprise must never trap the evening or retrigger endlessly.
        if gr['phase'] in ('alarm_intro','study'):
            gr['items']=[]
        gr['phase']='complete'
        gr['deadline']=None
    sh['game']=None
    sh['spin']=None
    sh['gift']=None
    sh['last_gift']=None
    sh['mode']='finished' if all_done(s) else 'wheel'
    return {'returned':True,'mode':sh['mode'],'previous_mode':mode}


def gift_requirement(s):
    sh=ensure(s);gift=sh.get('gift')
    if not gift or remaining(s)<=0:return None
    if gift['winner_index']>=len(gift['winners']):return None
    winner=gift['winners'][gift['winner_index']]
    p=player(s,winner)
    if gift['choice_index']==0 and p and p['received']<p['target']:
        return {'winner':winner,'kind':'self','eligible':[winner]}
    options=available(s,exclude=winner)
    if not options:
        options=available(s)  # Last remaining gifts: no other recipient exists.
    return {'winner':winner,'kind':'other' if winner not in options else 'remaining','eligible':options}


def validate_choice(s,pid):
    return pid in player_ids(s)


def admin(s,payload,save):
    sh=ensure(s);act=payload.get('action','')
    def done(ret):save();return ret
    if act=='v2_configure':
        if sh['mode']!='setup':raise ValueError('Instellen kan alleen vóór de spelshow.')
        entries=payload.get('players',[])
        if len(entries)!=4:raise ValueError('Vul vier spelers in.')
        names=[]
        for i,item in enumerate(entries):
            name=str(item.get('name','')).strip()[:28]
            count=int(item.get('target',9))
            if not name or not 1<=count<=99:raise ValueError('Geef vier namen en een aantal cadeaus van 1 tot 99.')
            names.append(name)
            s['players'][i]['name']=name;s['players'][i]['target']=count
        if len({norm(x) for x in names})!=4:raise ValueError('Namen moeten verschillend zijn.')
        return done({'configured':True})
    if act=='v2_story':
        if sh['mode'] not in ('setup','wheel'):raise ValueError('Voer persoonlijke weetjes vóór het spel in.')
        pid=str(payload.get('player',''))
        if not player(s,pid):raise ValueError('Onbekende speler.')
        story=str(payload.get('story','')).strip()
        if not 12<=len(story)<=250:raise ValueError('Het weetje moet tussen 12 en 250 tekens lang zijn.')
        sh['stories'][pid]=story
        return done({'stored':True})
    if act=='v2_start':
        if sh['mode']!='setup':raise ValueError('Spelshow is al begonnen.')
        sh['started_at']=time.time()
        for p in s['players']:
            if p['target']==0:p['target']=9
            p['received']=0;p['wins']=0
        sh['gifts_given']=0
        sh['spin_turn']=0
        sh['disabled_games']=[]
        sh['mode']='wheel'
        return done({'started':True})
    if act in ('v2_spin','v2_direct'):
        if sh['mode']!='wheel':raise ValueError('Wacht tot het volgende spel.')
        enabled=[g['id'] for g in GAMES if g['id'] not in sh['disabled_games']]
        sh['bag']=[g for g in sh['bag'] if g in enabled]
        if not enabled:raise ValueError('Alle minigames zijn uitgeschakeld. Schakel er één opnieuw in.')
        if not sh['bag']:
            sh['bag']=enabled[:];RNG.shuffle(sh['bag'])
        chosen=(RNG.choice(sh['bag']) if act=='v2_spin' else str(payload.get('category','')))
        if chosen not in sh['bag']:raise ValueError('Dit spel is al gespeeld in de huidige cyclus.')
        # Check availability before consuming a wheel position.
        game=make_game(s,chosen)
        before_bag=sh['bag'][:]  # Keep the full wheel visible during animation.
        sh['bag'].remove(chosen)
        sh['recent'].append(chosen)
        sh['game']=game
        old_turn=sh['spin_turn'] if act=='v2_spin' else None
        sh['spin']={'category':chosen,'options':before_bag,'at':time.time(),
                    'turn_before':old_turn}
        if act=='v2_spin':sh['spin_turn']+=1
        sh['mode']='spinning' if act=='v2_spin' else 'game'
        return done({'category':chosen})
    if act=='v2_open_game':
        if sh['mode']!='spinning':raise ValueError('Het spelrad draait niet.')
        sh['mode']='game';return done({'started':True})
    if act in ('v2_cancel','v2_return_wheel'):
        if act=='v2_cancel' and sh['mode'] not in ('game','spinning'):
            raise ValueError('Er loopt geen minigame.')
        return done(return_to_wheel(s))
    if act=='v2_disable_game':
        category=str(payload.get('category') or '')
        if sh['mode'] in ('game','spinning') and sh.get('game'):
            category=sh['game']['category']
        elif sh['mode']=='gift' and sh.get('gift'):
            category=sh['gift']['category']
        if category not in GAME_IDS:raise ValueError('Kies een geldig minigame om uit te schakelen.')
        if sh['mode'] in ('setup','finished'):raise ValueError('Er is geen lopende spelavond.')
        if category not in sh['disabled_games']:sh['disabled_games'].append(category)
        sh['bag']=[g for g in sh['bag'] if g!=category]
        if sh['mode'] in ('game','spinning','gift'):
            return done({'disabled':category,**return_to_wheel(s,disabled=True)})
        return done({'disabled':category,'mode':sh['mode']})
    if act=='v2_enable_game':
        if sh['mode']!='wheel':raise ValueError('Spellen herinschakelen kan vanaf het rad.')
        category=str(payload.get('category') or '')
        if category not in sh['disabled_games']:raise ValueError('Dit minigame is niet uitgeschakeld.')
        sh['disabled_games'].remove(category)
        if category not in sh['bag']:sh['bag'].append(category)
        return done({'enabled':category})
    if act=='v2_choose':
        g,r=current(sh)
        if sh['mode']!='game' or g['phase']!='choose':raise ValueError('Er is nu niets te kiezen.')
        if g['category']=='classic':
            level=payload.get('value')
            if level not in DIFFICULTY:raise ValueError('Ongeldige moeilijkheid.')
            chosen=find_classic(s,level)
            if not chosen:raise ValueError('Er zijn niet genoeg geschikte kaarten voor dit niveau. Kies een ander niveau of voeg kaarten toe.')
        else:
            era=payload.get('value')
            chosen=make_quiz_round(s,era)
            if not chosen:raise ValueError('Geen nummers beschikbaar in deze era.')
        chosen['chooser']=r['chooser']
        g['rounds'][g['round_index']]=chosen
        g['phase']='answer'
        return done({'chosen':True})
    if act=='v2_start_timer':
        g,r=current(sh)
        if sh['mode']!='game' or g['category']!='taboo' or g['phase'] not in ('answer','ready'):
            raise ValueError('Geen woordomschrijving klaar.')
        if r['deadline']:raise ValueError('Timer is al gestart.')
        r['started_at']=time.time();r['deadline']=r['started_at']+60
        return done({'deadline':r['deadline']})
    if act=='v2_count_question':
        g,r=current(sh)
        if sh['mode']!='game' or g['category']!='three' or g['phase']!='answer':raise ValueError('Niet beschikbaar.')
        if r['questions_used']>=10:raise ValueError('De tien vragen zijn gebruikt.')
        r['questions_used']+=1
        return done({'count':r['questions_used']})
    if act=='v2_open_vote':
        g,r=current(sh)
        if sh['mode']!='game' or g['category']!='quiplash' or g['phase']!='answer':raise ValueError('Niet beschikbaar.')
        # Host decides when to continue, including when testing without phones.
        shuffled=RNG.sample(list(r['answer']),len(r['answer']))
        r['option_tokens']={secrets.token_urlsafe(9):pid for pid in shuffled}
        g['phase']='vote'
        return done({'phase':'vote'})
    if act=='v2_reveal':
        g,r=current(sh)
        if sh['mode']!='game' or g['phase'] not in ('answer','vote'):raise ValueError('Niets te onthullen.')
        if g['category']=='quiplash' and g['phase']!='vote':raise ValueError('Eerst stemmen.')
        # Missing answers are not graded as correct; host decides when to reveal.
        if g['category']=='cards':
            if len(r['answer'])<len(r['alive']):
                raise ValueError('Wacht tot alle overgebleven spelers hebben gekozen.')
            card=r['cards'][r['stage']]
            stage=r['stage'];before=r['alive'][:]
            correct=(('red' if card['s'] in 'HD' else 'black') if stage==0 else
                    ('higher' if card['v']>r['cards'][0]['v'] else 'lower') if stage==1 else
                    ('inside' if min(r['cards'][0]['v'],r['cards'][1]['v'])<card['v']<max(r['cards'][0]['v'],r['cards'][1]['v']) else 'outside') if stage==2 else card['s'])
            yes=[pid for pid in before if r['answer'].get(pid)==correct]
            r['answers_by_stage'].append({'stage':stage,'answers':dict(r['answer']),'correct':correct,'survivors':yes})
            if not yes or len(yes)==1 or stage==3:
                # When everyone still playing answered wrongly, all share
                # the win. Absent players must never count as winners.
                r['deal_winners']=(yes if yes else before if len(r['answer'])==len(before) else [])
                r['deal_finished']=True
                award_round(s)
            else:r['stage_alive']=yes
            r['alive']=yes
        else:
            award_round(s)
        g['phase']='reveal'
        return done({'revealed':True})
    if act=='v2_override':
        g,r=current(sh)
        if sh['mode']!='game' or not g or g['category'] not in ('quiz','classic','taboo'):
            raise ValueError('Deze correctie is hier niet beschikbaar.')
        index=int(payload.get('round',g['round_index']))
        if not 0<=index<len(g['rounds']):raise ValueError('Onbekende vraag.')
        target=g['rounds'][index];pid=str(payload.get('player',''))
        if pid not in player_ids(s) or not target.get('revealed') or pid not in target.get('grades',{}):
            raise ValueError('Antwoord nog niet beschikbaar.')
        accepted=bool(payload.get('accepted'))
        grade=target['grades'][pid]
        grade['accepted']=accepted;grade['manual']=accepted
        target['points'][pid]= (DIFFICULTY[target['level']] if g['category']=='classic' else 1) if accepted else 0
        if g['category']=='taboo':
            performer=target['performer']
            target['points'][performer]=int(any(target['grades'].get(p,{}).get('accepted') for p in player_ids(s) if p!=performer))
        if g['category']=='quiz' and accepted and payload.get('remember') and target['question_type'] in ('title','artist'):
            key=target['question_type']+':'+str(target['hidden_id'])
            alias=str(grade.get('guess','')).strip()[:120]
            if alias:
                existing=sh['aliases'].setdefault(key,[])
                if alias not in existing:existing.append(alias)
        recompute(s)
        return done({'corrected':True})
    if act=='v2_next':
        g,r=current(sh)
        if sh['mode']!='game' or g['phase']!='reveal':raise ValueError('Onthul eerst het resultaat.')
        if g['category']=='cards' and not (r.get('deal_finished') or r.get('deal_winners')):
            r['stage']+=1;r['answer']={};g['phase']='answer'
            return done({'advanced':True})
        if g['round_index']+1<g['total']:
            g['round_index']+=1
            g['rounds'].append(make_round(s,g['category'],g['round_index'],g))
            g['phase']='choose' if g['category'] in ('classic','quiz') else 'answer'
        else:
            g['phase']='review'
        return done({'advanced':True})
    if act=='v2_confirm':
        g,r=current(sh)
        if sh['mode']!='game' or g['phase']!='review':raise ValueError('Bevestig na de laatste vraag.')
        highest=max(g['scores'].values())
        winners=[pid for pid,n in g['scores'].items() if n==highest]
        for pid in winners:player(s,pid)['wins']+=1
        gift_start(s,winners,g['category'])
        sh['gift']['scores']=copy.deepcopy(g['scores'])
        return done({'winners':winners})
    if act=='v2_give':
        if sh['mode']!='gift':raise ValueError('Geen cadeau-uitdeling bezig.')
        requirement=gift_requirement(s)
        if requirement is None:raise ValueError('Geen cadeaus meer over.')
        pid=payload.get('recipient','')
        if pid not in requirement['eligible']:raise ValueError('Kies een toegestane ontvanger.')
        sh['last_gift']={'gift':copy.deepcopy(sh['gift']),'players':[p['received'] for p in s['players']],
                         'history_len':len(s.get('history',[])),'completed':sh['regular_completed'],
                         'grocery_phase':sh['grocery']['phase'],'mode':sh['mode']}
        p=player(s,pid);p['received']+=1
        sh['gifts_given']+=1
        sh['gift']['awarded'].append({'winner':requirement['winner'],'recipient':pid})
        s.setdefault('history',[]).append({'type':'gift','winner':requirement['winner'],
                                           'recipient':pid,'category':sh['gift']['category'],'at':time.time()})
        sh['gift']['choice_index']+=1
        if sh['gift']['choice_index']>=2:
            sh['gift']['choice_index']=0;sh['gift']['winner_index']+=1
        gift_next(s)
        return done({'recipient':pid,'remaining':remaining(s)})
    if act=='v2_undo_gift':
        backup=sh.get('last_gift')
        if not backup:raise ValueError('Geen cadeau om terug te draaien.')
        for p,count in zip(s['players'],backup['players']):p['received']=count
        sh['gift']=backup['gift'];sh['mode']='gift'
        sh['regular_completed']=backup['completed']
        sh['grocery']['phase']=backup['grocery_phase']
        sh['gifts_given']-=1
        del s['history'][backup['history_len']:]
        sh['last_gift']=None
        return done({'undone':True})
    if act=='v2_grocery_show':
        gr=sh['grocery']
        if sh['mode']!='grocery_alarm':raise ValueError('Geen alarm actief.')
        if gr['phase']=='alarm_intro':
            gr['phase']='study';gr['deadline']=time.time()+60
            sh['mode']='grocery_study'
        elif gr['phase']=='alarm_recall':
            gr['phase']='recall';gr['deadline']=time.time()+180
            sh['mode']='grocery_recall'
        else:raise ValueError('Onbekende alarmfase.')
        return done({'deadline':gr['deadline']})
    if act=='v2_grocery_close':
        gr=sh['grocery']
        if sh['mode']=='grocery_study':
            if time.time()<gr['deadline']:raise ValueError('De 60 seconden zijn nog niet voorbij.')
            gr['phase']='waiting';gr['deadline']=None
            sh['mode']='wheel'
        elif sh['mode']=='grocery_recall':
            # Host may close recall at any time; missing players receive 0.
            gr['phase']='review';gr['deadline']=None
            gr['review']=grade_grocery(s)
            sh['mode']='grocery_review'
        else:raise ValueError('Geen boodschappenfase bezig.')
        return done({'phase':gr['phase']})
    if act=='v2_grocery_override':
        gr=sh['grocery']
        if sh['mode']!='grocery_review':raise ValueError('Geen uitslag klaar.')
        pid=payload.get('player');guess=str(payload.get('guess',''))
        if pid not in player_ids(s) or guess not in gr['responses'].get(pid,[]):raise ValueError('Antwoord niet gevonden.')
        gr.setdefault('overrides',{})[pid+':'+guess]=bool(payload.get('accepted'))
        gr['review']=grade_grocery(s)
        return done({'corrected':True})
    if act=='v2_grocery_confirm':
        if sh['mode']!='grocery_review':raise ValueError('De uitslag is nog niet klaar.')
        scores={pid:gr['score'] for pid,gr in sh['grocery']['review'].items()}
        hi=max(scores.values())
        winners=[pid for pid,n in scores.items() if n==hi]
        for pid in winners:player(s,pid)['wins']+=1
        sh['grocery']['phase']='complete'
        gift_start(s,winners,'grocery')
        sh['gift']['scores']=scores
        return done({'winners':winners})
    if act=='v2_reset':
        if str(payload.get('confirmation',''))!='RESET':raise ValueError('Typ RESET om opnieuw te beginnen.')
        saved_stories=copy.deepcopy(sh.get('stories',{}))
        saved_aliases=copy.deepcopy(sh.get('aliases',{}))
        s['show2']=new_show()
        s['show2']['stories']=saved_stories
        s['show2']['aliases']=saved_aliases
        for p in s['players']:
            p['received']=0;p['wins']=0
        s['history']=[]
        return done({'reset':True})
    raise ValueError('Onbekende spelshowactie.')


def grade_grocery(s):
    sh=ensure(s);gr=sh['grocery']
    items=gr['items']
    out={}
    for pid in player_ids(s):
        guesses=gr['responses'].get(pid,[])
        used=set();results=[]
        for guess in guesses:
            matched=next((item for item in items if item not in used and same_answer(guess,item,'title')),None)
            correction=gr.get('overrides',{}).get(pid+':'+guess)
            accepted=(matched is not None if correction is None else correction)
            if matched:used.add(matched)
            results.append({'text':guess,'accepted':accepted,'matched':matched,'auto':matched is not None})
        # A manually accepted answer represents one additional item at most.
        out[pid]={'answers':results,'score':sum(v['accepted'] for v in results)}
    return out


def submit(s,payload,pid,save):
    sh=ensure(s);act=payload.get('action','')
    if act=='v2_story':
        if sh['mode'] not in ('setup','wheel'):raise ValueError('Weetjes alleen invoeren vóór het spel.')
        story=str(payload.get('value','')).strip()
        if not 12<=len(story)<=250:raise ValueError('Gebruik 12 tot 250 tekens.')
        sh['stories'][pid]=story
        save();return {'saved':True}
    if act=='v2_grocery_answer':
        gr=sh['grocery']
        if sh['mode']!='grocery_recall' or time.time()>gr['deadline']:
            raise ValueError('De geheugenronde is gesloten.')
        text=str(payload.get('value',''))[:1200]
        answers=[]
        for line in re.split(r'[,\n;]+',text):
            cleaned=line.strip()
            if cleaned and norm(cleaned) not in {norm(x) for x in answers}:
                answers.append(cleaned[:75])
        gr['responses'][pid]=answers[:30]
        save();return {'saved':len(gr['responses'][pid])}
    if act=='v2_spin':
        if sh['mode']!='wheel':raise ValueError('Het rad is nu niet beschikbaar.')
        ids=player_ids(s)
        if not ids or pid!=ids[sh['spin_turn']%len(ids)]:
            raise ValueError('Een andere speler mag nu aan het rad draaien.')
        return admin(s,payload,save)
    if sh['mode']!='game':raise ValueError('Er is geen actieve minigame.')
    g,r=current(sh);cat=g['category']
    if act=='v2_choose':
        if g['phase']!='choose' or r.get('chooser')!=pid:raise ValueError('Een andere speler kiest nu.')
        # Share the same server-side validation as the host.
        return admin(s,payload,save)
    if act=='v2_start_timer':
        if cat!='taboo' or r['performer']!=pid:raise ValueError('Alleen de omschrijver kan starten.')
        return admin(s,payload,save)
    if act=='v2_guess_owner':
        if cat!='three' or g['phase']!='answer' or r['investigator']!=pid or r.get('guess'):
            raise ValueError('Alleen de onderzoeker kan nu raden.')
        val=str(payload.get('value',''))
        if val==pid or val not in player_ids(s):raise ValueError('Kies één van de drie andere spelers.')
        r['guess']=val
        award_round(s)
        g['phase']='reveal'
        save();return {'recorded':True}
    if act=='v2_vote':
        if cat!='quiplash' or g['phase']!='vote':raise ValueError('Je kunt nu niet stemmen.')
        option_token=str(payload.get('value',''))
        val=r.get('option_tokens',{}).get(option_token)
        if val==pid or val not in r['answer']:raise ValueError('Kies het antwoord van iemand anders.')
        r['votes'][pid]=val;save();return {'voted':True}
    if act=='v2_guess':
        if cat!='taboo' or g['phase']!='answer' or not r['deadline'] or time.time()>r['deadline']:
            raise ValueError('De timer is niet actief.')
        if pid==r['performer']:raise ValueError('Jij bent de omschrijver.')
        value=str(payload.get('value','')).strip()[:100]
        if not value:raise ValueError('Typ een antwoord.')
        bucket=r.setdefault('attempts',{}).setdefault(pid,[])
        if len(bucket)<20:bucket.append(value)
        save();return {'correct':same_answer(value,r['word'],'title',r['aliases'])}
    if act=='v2_answer':
        if g['phase']!='answer' or cat not in ('classic','quiz','quiplash','dice','cards'):
            raise ValueError('Nu is geen antwoord mogelijk.')
        if pid in r['answer']:raise ValueError('Je hebt al geantwoord.')
        value=payload.get('value')
        if cat=='classic':
            if value not in ('left','middle','right'):raise ValueError('Kies links, midden of rechts.')
        if cat=='quiz':
            typ=r['question_type']
            if typ=='boundary':
                if value not in ('before','after'):raise ValueError('Kies vóór of vanaf.')
            elif typ in ('year5','year3'):
                try:value=int(str(value).strip())
                except ValueError:raise ValueError('Vul een geldig jaartal in.')
                if not 1900<=value<=2100:raise ValueError('Ongeldig jaartal.')
            else:
                value=str(value or '').strip()[:120]
                if not value:raise ValueError('Vul een titel of artiest in.')
        if cat=='quiplash':
            value=str(value or '').strip()[:240]
            if len(value)<2:raise ValueError('Typ een grappig antwoord.')
        if cat=='dice':
            if not isinstance(value,list) or len(value)!=5 or any(type(x)!=int or not 1<=x<=6 for x in value):
                raise ValueError('Vul precies vijf dobbelsteenwaarden van 1–6 in.')
        if cat=='cards':
            if pid not in r['alive']:raise ValueError('Je ligt al uit dit kaartduel.')
            valid=[('red','black'),('higher','lower'),('inside','outside'),('H','D','C','S')][r['stage']]
            if value not in valid:raise ValueError('Ongeldige kaartkeuze.')
        r['answer'][pid]=value
        save();return {'saved':True}
    raise ValueError('Onbekende speleractie.')


def masked_round(s,g,r,is_admin,pid):
    cat=g['category'];phase=g['phase'];out={}
    always=('chooser','ref','level','era','question_type','boundary','prompt','investigator',
            'story','questions_used','rule','target','stage','alive','started_at','deadline','performer')
    for k in always:
        if k in r:out[k]=copy.deepcopy(r[k])
    if cat=='three' and phase!='review':
        out.pop('owner',None)
        if phase=='reveal':out['guess_skipped']=not bool(r.get('guess'))
    if cat in ('classic','quiz'):
        out['qr_url']='/hitster/qr.png?id='+r['hidden_id'] if r.get('hidden_id') else None
        out['card_id']=r.get('hidden_id')
        if r.get('hidden_id') and (r.get('revealed') or phase=='review'):
            out['correct']={'classic':r.get('correct'),'quiz':r.get('question_type')}.get(cat)
            out['song']={'title':r['title'],'artist':r['artist'],'year':r['year']}
            if cat=='quiz' and r.get('question_type')=='boundary':out['boundary']=r['boundary']
    if cat=='cards':
        visible=(r['stage']+int(phase=='reveal'))
        if r.get('deal_finished') or r.get('deal_winners'):visible=4
        out['cards']=[c if i<visible else None for i,c in enumerate(r['cards'])]
        out['deal_finished']=bool(r.get('deal_finished') or r.get('deal_winners'))
        out['deal_winners']=r.get('deal_winners') if r.get('revealed') else None
        if r['answers_by_stage']:
            out['stage_result']=r['answers_by_stage'][-1] if phase=='reveal' else None
    if cat=='taboo':
        if pid==r['performer'] or is_admin or phase in ('review','reveal'):
            out['word']=r['word'];out['banned']=r['banned']
        out['correct_players']=[p for p,grade in r.get('grades',{}).items() if grade.get('accepted')]
    out['submitted']=list(r.get('answer',{}))
    if cat=='quiplash':
        if phase in ('vote','reveal','review'):
            out['options']=[{'id':tok,'text':r['answer'][owner],'mine':owner==pid} for tok,owner in r.get('option_tokens',{}).items()]
            # Opaque vote tokens preserve anonymity while allowing one vote per player.
        out['voted']=list(r.get('votes',{}))
    if is_admin:
        out['all_answers']=copy.deepcopy(r.get('answer',{}))
        out['all_attempts']=copy.deepcopy(r.get('attempts',{}))
        if cat=='three' and phase=='review':out['owner']=r['owner']
        if cat=='three' and phase=='reveal':out['guess']=r.get('guess')
    if pid:
        out['my_answer']=r.get('answer',{}).get(pid)
        out['my_vote']=r.get('votes',{}).get(pid)
        out['my_attempts']=r.get('attempts',{}).get(pid,[])
        if cat=='three' and pid==r.get('investigator') and r.get('guess'):out['guess']=r['guess']
    if cat=='three' and phase=='review':out['owner']=r['owner'];out['guess']=r.get('guess')
    if r.get('revealed') and (cat!='three' or phase=='review'):
        out['grades']=copy.deepcopy(r.get('grades',{})) if is_admin else {pid:r.get('grades',{}).get(pid)} if pid else {}
        out['points']=copy.deepcopy(r.get('points',{}))
    return out


def view(s,is_admin=False,pid=None):
    sh=ensure(s);v={'version':2,'mode':sh['mode'],'games':GAMES,'bag':list(sh['bag']),
                   'recent':sh['recent'][-7:],'spin':sh['spin'],
                   'disabled_games':list(sh['disabled_games']),
                   'enabled_games':[g['id'] for g in GAMES if g['id'] not in sh['disabled_games']],
                   'spin_player':player_ids(s)[sh['spin_turn']%len(player_ids(s))] if player_ids(s) else None,
                   'regular_completed':sh['regular_completed'],
                   'gifts_given':sh['gifts_given'],'remaining_gifts':remaining(s),
                   'has_story':{p['id']:bool(sh['stories'].get(p['id'])) for p in s['players']},
                   'game':None,'grocery':None,'gift':None}
    if sh.get('game'):
        g=sh['game'];r=g['rounds'][g['round_index']]
        public_scores=(g['scores'] if (is_admin or g['category']!='three' or g['phase']=='review')
                       else {pid:0 for pid in player_ids(s)})
        v['game']={'category':g['category'],'phase':g['phase'],'index':g['round_index'],
                   'total':g['total'],'scores':public_scores,
                   'current':masked_round(s,g,r,is_admin,pid)}
        if g['phase']=='review':
            v['game']['rounds']=[masked_round(s,g,round_,is_admin,pid) for round_ in g['rounds']]
    if sh['mode'].startswith('grocery_'):
        gr=sh['grocery'];v['grocery']={'phase':gr['phase'],'deadline':gr['deadline'],
                                     'responses_count':len(gr['responses'])}
        if gr['phase'] in ('study','review'):
            v['grocery']['items']=list(gr['items'])
        if gr['phase']=='review':
            v['grocery']['review']=copy.deepcopy(gr['review']) if is_admin else {pid:gr['review'].get(pid)} if pid else {}
        if pid:v['grocery']['my_response']=gr['responses'].get(pid,[])
    if sh['mode']=='gift' and sh['gift']:
        gift=sh['gift'];need=gift_requirement(s)
        v['gift']={'winners':gift['winners'],'winner_index':gift['winner_index'],
                   'choice_index':gift['choice_index'],'awarded':gift['awarded'],
                   'category':gift['category'],'scores':gift.get('scores',{}),
                   'requirement':need}
    if is_admin:
        v['stories']=copy.deepcopy(sh['stories']) if sh['mode'] in ('setup','wheel') else {}
        v['hitster_count']=len(s.get('hitster_cards',[]))
        v['hitster_cards']=copy.deepcopy(s.get('hitster_cards',[])) if sh['mode']=='setup' else []
    if sh['mode']=='game' and v['game']['category']=='quiz' and v['game']['phase']=='answer':
        v['suggestions']={'artist':sorted({c['artist'] for c in s.get('hitster_cards',[])},key=str.lower),
                          'title':sorted({c['title'] for c in s.get('hitster_cards',[])},key=str.lower)}
    return v
