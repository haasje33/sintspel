#!/usr/bin/env python3
"""Sinterklaas Party Challenge — zero third-party dependencies; LAN-only party server.
Run: python server.py. Everything stays on the computer running the server.
"""
import json
import mimetypes
import os
import random
import re
import secrets
import socket
import sys
import threading
import time
import unicodedata
import uuid
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE = Path(__file__).resolve().parent
STATIC = BASE / 'static'
AUDIO = BASE / 'audio'
DATA = BASE / 'party-state.json'
ADMIN = BASE / '.host-key'
PORT = int(os.environ.get('PARTY_PORT', '8765'))
RNG = random.SystemRandom()
LOCK = threading.RLock()

CATEGORIES = [
    {'id':'hitster','name':'Hitster','icon':'🎵','kind':'music','color':'#f27fa0','desc':'Raad het muziekjaar'},
    {'id':'schatting','name':'Schat & gok','icon':'🎯','kind':'estimate','color':'#f8bb60','desc':'Wie zit er het dichtstbij?'},
    {'id':'creatief','name':'Party & Co','icon':'💬','kind':'creative','color':'#a29bff','desc':'De grappigste reactie wint'},
    {'id':'wie','name':'Wie van ons?','icon':'👀','kind':'who','color':'#f29fce','desc':'Stem op een van jullie'},
    {'id':'pictionary','name':'Pictionary','icon':'🎨','kind':'performance','color':'#7adacf','desc':'Teken en raad'},
    {'id':'uitbeelden','name':'Uitbeelden','icon':'🎭','kind':'performance','color':'#ffc76c','desc':'Geen woorden toegestaan'},
    {'id':'taboe','name':'Verboden woord','icon':'🤫','kind':'performance','color':'#9aca84','desc':'Omschrijf zonder verboden woorden'},
    {'id':'yahtzee','name':'Yahtzee-sprint','icon':'🎲','kind':'physical','color':'#afc5ff','desc':'Speel met echte dobbelstenen'},
    {'id':'rummikub','name':'Rummikub-race','icon':'🧩','kind':'physical','color':'#ff9d8a','desc':'Slim combineren'},
    {'id':'kaarten','name':'Kaartenduel','icon':'🃏','kind':'physical','color':'#f2d281','desc':'Een beetje lef en geluk'},
    {'id':'levensweg','name':'Levensweg','icon':'🚗','kind':'creative','color':'#b6a2ef','desc':'Belachelijke levenskeuzes'},
]
CAT = {item['id']:item for item in CATEGORIES}
ESTIMATES = [
    ('Hoeveel seconden zitten er in een dag?',86400,'86.400 seconden'),
    ('Hoeveel vakjes heeft een traditioneel schaakbord?',64,'64 vakjes'),
    ('Hoeveel dagen telt een schrikkeljaar?',366,'366 dagen'),
    ('Hoeveel minuten zitten er in één week?',10080,'10.080 minuten'),
    ('Hoeveel kaarten zitten er in een standaard kaartspel zonder jokers?',52,'52 kaarten'),
    ('Hoeveel letters heeft het Griekse alfabet?',24,'24 letters'),
    ('Hoeveel officiële provincies heeft Nederland?',12,'12 provincies'),
    ('Hoeveel toetsen heeft een standaard concertvleugel?',88,'88 toetsen'),
    ('Hoeveel centimeters zitten er in een mijl (ongeveer)?',160934,'Ongeveer 160.934 centimeter'),
    ('Hoeveel harten heeft een octopus?',3,'3 harten'),
    ('Hoeveel dobbelsteenogen heb je maximaal bij vijf dobbelstenen?',30,'30 ogen'),
    ('Hoeveel milliliter zit er in drie liter?',3000,'3.000 milliliter'),
    ('Hoeveel kilometer is een marathon (afronden op hele km)?',42,'42 kilometer'),
    ('Hoeveel zijden hebben drie gewone dobbelstenen samen?',18,'18 zijden'),
    ('Hoeveel landen grenzen direct aan Nederland over land, Europees Nederland?',2,'België en Duitsland (2)'),
    ('Hoeveel maanden van het jaar hebben precies 30 dagen?',4,'April, juni, september, november (4)'),
    ('Hoeveel uren zitten er in een niet-schrikkeljaar?',8760,'8.760 uren'),
    ('Hoeveel snaren heeft een gebruikelijke gitaar?',6,'6 snaren'),
    ('Hoeveel vakjes heeft een standaard sudoku?',81,'81 vakjes'),
    ('Hoeveel sterren staan op de vlag van de Verenigde Staten?',50,'50 sterren'),
    ('Hoeveel botten heeft een gemiddeld volwassen mens?',206,'Ongeveer 206 botten'),
    ('Hoeveel minuten zitten er in tweeënhalve dag?',3600,'3.600 minuten'),
    ('Hoeveel centimeter is de diameter van een cirkel met straal 7 cm?',14,'14 cm'),
    ('Hoeveel kaarten heeft iedereen bij klaverjassen aan het begin?',8,'8 kaarten'),
    ('Hoeveel poten hebben vier spinnen samen?',32,'32 poten'),
    ('Hoeveel Nederlandse letters komen vóór de M in het alfabet?',12,'12 letters'),
    ('Hoeveel vlakken heeft een gewone zeszijdige dobbelsteen?',6,'6 vlakken'),
    ('Hoeveel minuten zitten er in 2 uur en 45 minuten?',165,'165 minuten'),
    ('Hoeveel dagen zitten er in twee niet-schrikkeljaren?',730,'730 dagen'),
    ('Hoeveel procent is een kwart?',25,'25 procent'),
]
CREATIVE = [
    'Sinterklaas moet één nieuwe regel invoeren voor het uitpakken. Welke?',
    'Je moet je pepernotenmerk verkopen met een belachelijke reclameslogan. Welke?',
    'Je geeft de stoomboot een nieuwe naam. Hoe heet die?',
    'Wat is het slechtste excuus om te laat te zijn op pakjesavond?',
    'Bedenk een nieuwe functie voor de staf van Sinterklaas.',
    'Welke afschuwelijke combinatie zou je in een nieuwe chocoladeletter stoppen?',
    'Je hebt €10 miljoen maar mag alleen iets nutteloos kopen. Wat koop je?',
    'Hoe heet jouw autobiografie als deze geschreven wordt door een zeer boze kat?',
    'Welk volstrekt nutteloos vak zou verplicht moeten worden op school?',
    'Sinterklaas is influencer geworden. Wat is zijn allereerste post?',
    'Bedenk de meest dramatische productnaam voor een simpele boterham.',
    'Je mag één huishoudelijk apparaat een stem geven. Welk apparaat en wat zegt het?',
    'Je krijgt een eigen standbeeld. Welke absurde houding neem je aan?',
    'Welke nieuwe feestdag zou je invoeren en wat vieren we dan?',
    'Wat zegt een pepernoot vlak voordat hij wordt opgegeten?',
    'Welk cadeau zou je een miljoenair geven die alles al heeft?',
]
LIFE = [
    'Je krijgt een nieuwe baan: officiële pepernotentester. Waarom ben jij onmisbaar?',
    'Je wint een levenslange voorraad van één onhandig product. Wat kies je?',
    'Je wordt burgemeester van een dorp met drie inwoners. Wat is je eerste wet?',
    'Je mag voor één dag van beroep ruilen met een beroemd persoon. Wie, en wat gaat mis?',
    'Je huis krijgt een verplichte nieuwe kamer die niemand nodig heeft. Welke?',
    'Je wordt wereldkampioen in een compleet nutteloze sport. Welke sport?',
    'Je krijgt een persoonlijke assistent, maar die is een pratende goudvis. Wat laat je doen?',
    'Je moet je carrière voortaan uitleggen met één gênante functietitel. Welke?',
    'Je erft een kasteel, maar één ruimte is vervloekt. Welke en waarom?',
    'Je mag één bizarre regel toevoegen aan het familiekerstdiner. Welke?',
]
WHO = [
    'Wie van ons zou het langst overleven op een onbewoond eiland?',
    'Wie zou het snelst per ongeluk een geheim verklappen?',
    'Wie zou het meest geloofwaardig kunnen doen alsof die beroemd is?',
    'Wie geeft het vaakst advies waar niemand om gevraagd heeft?',
    'Wie zou het eerst een boek schrijven over zijn of haar eigen leven?',
    'Wie zou het beste een boevenbende kunnen leiden?',
    'Wie zou in een realityshow de meeste chaos veroorzaken?',
    'Wie zou het makkelijkst een verkeerd cadeau heel enthousiast ontvangen?',
    'Wie zou de meeste plannen maken zonder ze ooit uit te voeren?',
    'Wie zou de slechtste reisleider zijn, en toch zeggen dat alles goed gaat?',
    'Wie zou het snelst vrienden worden met een onbekende in de trein?',
    'Wie zou het snelst een huishoudelijk apparaat kapotmaken door de handleiding te negeren?',
]
DRAW = [
    ('rollator', ['loophulp']), ('luchtballon',[]), ('kerstboom',[]), ('sneeuwpop',[]),
    ('robotstofzuiger',['stofzuigerrobot']), ('pindakaas',[]), ('brandweerauto',[]),
    ('tuinkabouter',[]), ('achtbaan',[]), ('vogelverschrikker',[]), ('zonnebril',[]),
    ('verrekijker',[]), ('strandstoel',[]), ('skelter',[]), ('wasmachine',[]),
    ('vuilniswagen',[]), ('fietspomp',[]), ('paraplu',[]), ('winkelwagen',[]),
    ('schoorsteen',[]), ('sinterklaas',[]), ('schommel',[]), ('hangmat',[]),
]
MIME = [
    ('tandenpoetsen', ['tanden poetsen']), ('skiën',['skien','skien']),
    ('stofzuigen',[]),('vissen',[]),('golfen',[]),('strijken',[]),('vliegeren',[]),
    ('cadeau inpakken',['cadeau inpakken']),('slapen',[]),('roeien',[]),
    ('accordeon spelen',[]),('boksen',[]),('koekjes bakken',[]),('grasmaaien',[]),
    ('trampoline springen',[]),('fietsen',[]),('schaken',[]),('gitaar spelen',[]),
    ('een sneeuwpop maken',['sneeuwpop maken']),('typen',[]),('dansen',[]),
]
TABOO = [
    ('Sinterklaas',['baard','cadeau','stoomboot'],[]),
    ('telefoon',['bellen','scherm','app'],['mobiel']),
    ('koelkast',['koud','eten','keuken'],[]),
    ('verjaardag',['taart','leeftijd','feest'],[]),
    ('ziekenhuis',['dokter','ziek','bed'],[]),
    ('vakantie',['reizen','hotel','vrij'],[]),
    ('koffie',['drinken','bonen','cafeïne'],[]),
    ('fiets',['wielen','trappen','stuur'],[]),
    ('supermarkt',['boodschappen','winkel','kassa'],[]),
    ('paraplu',['regen','nat','open'],[]),
    ('olifant',['slurf','groot','dier'],[]),
    ('vliegtuig',['vliegen','lucht','piloot'],[]),
    ('bioscoop',['film','popcorn','scherm'],[]),
    ('kerstboom',['december','lichtjes','versieren'],[]),
    ('bril',['ogen','zien','glazen'],[]),
    ('auto',['rijden','wielen','motor'],[]),
    ('wasmachine',['kleren','wassen','trommel'],[]),
    ('bibliotheek',['boeken','lenen','stil'],[]),
    ('pannenkoek',['beslag','stroop','bakken'],[]),
    ('afstandbediening',['televisie','knoppen','zappen'],['afstandsbediening']),
]
PHYSICAL = {
    'yahtzee': [
        {'title':'De Yahtzee-sprint','task':'Iedereen krijgt precies 3 worpen met 5 dobbelstenen. Na elke worp mag je stenen apart leggen. Doel: de hoogste SOM van alle 5 stenen na je laatste worp.','rules':'De grootste som wint. Bij gelijkspel: één dobbelsteen per gelijkstaande speler.'},
        {'title':'De dubbeltjesjacht','task':'Iedereen krijgt maximaal 3 worpen met 5 dobbelstenen. Je probeert zo veel mogelijk dezelfde ogen te verzamelen.','rules':'Meeste gelijke dobbelstenen wint. Bij gelijk aantal: hoogste dobbelsteenwaarde wint, dan één beslissingsworp.'},
        {'title':'De 6-jesjacht','task':'Iedereen gooit maximaal drie keer met vijf dobbelstenen; zessen mag je apart leggen.','rules':'De meeste zessen wint; bij gelijkstand wint de hoogste som van alle vijf eindstenen.'},
    ],
    'rummikub': [
        {'title':'Rummikub: één tafel, vier breinen','task':'Leg 18 willekeurige Rummikubstenen OPEN op tafel. Niemand mag ze aanraken. Iedereen krijgt 90 seconden om op papier zo veel mogelijk geldige combinaties (rijtjes of groepjes van minstens 3) te noteren, zonder een steen dubbel te gebruiken.','rules':'Tel het totaal aantal gebruikte stenen in geldige combinaties. De meeste wint; bij gelijkstand telt de hoogste som van de gebruikte cijfers.'},
        {'title':'De langste Rummikub-rij','task':'Trek 20 willekeurige Rummikubstenen en leg ze open neer. Alle vier zoeken binnen 60 seconden de LANGSTE geldige oplopende reeks van dezelfde kleur.','rules':'Langste geldige reeks van minstens 3 wint. Bij gelijkstand wint de reeks met de hoogste eindsom. Geen reeks? Opnieuw leggen.'},
    ],
    'kaarten': [
        {'title':'Eenentwintigen','task':'Gebruik een normaal kaartspel zonder jokers. Iedereen ontvangt twee kaarten, mag daarna om de beurt een kaart bijpakken of passen. Aas = 1 of 11, plaatjes = 10.','rules':'Wie het dichtst bij 21 komt zonder eroverheen te gaan, wint. Gelijk? Eén kaart trekken, hoogste wint.'},
        {'title':'Hoge-kaartenstrijd','task':'Iedereen krijgt 5 dichte kaarten. Kies ongezien één kaart om weg te leggen en draai daarna de overige vier open.','rules':'Hoogste som (boer 11, vrouw 12, heer 13, aas 14) wint. Gelijk? Hoogste afzonderlijke kaart, daarna een beslissingskaart.'},
        {'title':'Hoger of lager','task':'Trek voor iedereen één startkaart. Iedere speler voorspelt voor de VOLGENDE 5 kaarten of die hoger of lager zijn dan de vorige. Aas = hoog.','rules':'Meeste juiste voorspellingen wint. Bij gelijke kaart telt de voorspelling als fout. Gelijkspel? Extra kaart.'},
    ]
}


def normalize(value):
    value = ''.join(c for c in unicodedata.normalize('NFD', str(value).lower()) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+','',value)


def init_state():
    return {
        'room':str(RNG.randrange(1000,10000)), 'version':0, 'mode':'setup',
        'players':[{'id':f'p{i+1}','name':name,'received':0,'target':0,'wins':0,'token':None}
                   for i,name in enumerate(['Moeder','Speler 2','Speler 3','Speler 4'])],
        'bag':[], 'recent':[], 'spin':None, 'game':None, 'gift':None,
        'history':[], 'music':[], 'used':{}, 'started_at':None,
    }


def load_state():
    try:
        s = json.loads(DATA.read_text(encoding='utf-8'))
        if not isinstance(s,dict) or len(s.get('players',[])) != 4:
            raise ValueError('Corrupt state')
        return s
    except (OSError, ValueError, TypeError):
        return init_state()

S = load_state()
if ADMIN.exists():
    ADMIN_KEY = ADMIN.read_text(encoding='utf-8').strip()
else:
    ADMIN_KEY = secrets.token_urlsafe(24)
    ADMIN.write_text(ADMIN_KEY,encoding='utf-8')
    try: ADMIN.chmod(0o600)
    except OSError: pass


def save():
    S['version'] += 1
    path = DATA.with_suffix('.tmp')
    path.write_text(json.dumps(S,ensure_ascii=False,indent=2),encoding='utf-8')
    path.replace(DATA)


def player(token):
    return next((p for p in S['players'] if token and p['token']==token),None)


def by_id(pid):
    return next((p for p in S['players'] if p['id']==pid),None)


def eligible():
    alive = [p for p in S['players'] if not p['target'] or p['received'] < p['target']]
    if not alive:return []
    fewest=min(p['received'] for p in alive)
    return [p['id'] for p in alive if p['received']==fewest]


def sample_bank(name,bank,n):
    used=set(S['used'].get(name,[]))
    options=[i for i in range(len(bank)) if i not in used]
    if len(options)<n:
        options=list(range(len(bank)))
        used=set()
    picked=RNG.sample(options,min(n,len(options)))
    S['used'][name]=list(used.union(picked))
    return [bank[i] for i in picked]


def choose_category():
    if not S['bag']:
        S['bag']=[c['id'] for c in CATEGORIES]
        RNG.shuffle(S['bag'])
    recent=S['recent'][-2:]
    # Avoid three physically demanding or creative categories in a row when alternatives exist.
    candidate_indices=list(range(len(S['bag'])))
    if len(recent)==2:
        last_kinds=[CAT[x]['kind'] for x in recent]
        if last_kinds[0]==last_kinds[1]:
            others=[i for i in candidate_indices if CAT[S['bag'][i]]['kind'] != last_kinds[0]]
            if others:candidate_indices=others
    idx=RNG.choice(candidate_indices)
    selected=S['bag'].pop(idx)
    S['recent'].append(selected)
    return selected


def make_game(category):
    kind=CAT[category]['kind']
    points={p['id']:0 for p in S['players']}
    game={'category':category,'kind':kind,'title':CAT[category]['name'], 'phase':'answer',
          'round':0,'points':points,'submissions':{},'votes':{},'round_result':None,'questions':[],
          'started_at':time.time(),'deadline':None}
    if kind=='estimate':
        game['questions']=[{'question':q,'answer':a,'explain':e} for q,a,e in sample_bank('estimate',ESTIMATES,3)]
    elif kind=='music':
        tracks = list(S['music'])
        RNG.shuffle(tracks)
        while len(tracks)<3:
            tracks.append(None)
        game['questions']=[{'question':'Welk jaar kwam dit nummer uit?',
                            'audio':m['id'] if m else None,
                            'answer':m['year'] if m else None,
                            'artist':m['artist'] if m else '',
                            'song':m['title'] if m else '',
                            'explain':('Eigen muziekbestand' if m else 'Scan een fysieke Hitster-kaart met de officiële app')}
                           for m in tracks[:3]]
    elif kind=='creative':
        bank=LIFE if category=='levensweg' else CREATIVE
        game['questions']=[{'question':q} for q in sample_bank(category,bank,2)]
    elif kind=='who':
        game['questions']=[{'question':q} for q in sample_bank('who',WHO,3)]
    elif kind=='performance':
        bank= DRAW if category=='pictionary' else MIME if category=='uitbeelden' else TABOO
        prompts=sample_bank(category,bank,4)
        order=[p['id'] for p in S['players']]
        RNG.shuffle(order)
        game['questions']=[{'performer':p,'answer':str(item[0]),
                            'aliases':item[1] if category!='taboe' else item[2],
                            'forbidden':item[1] if category=='taboe' else []}
                           for p,item in zip(order,prompts)]
        game['deadline']=time.time()+85
    elif kind=='physical':
        picked=RNG.choice(PHYSICAL[category])
        game['questions']=[picked]
        game['phase']='manual'
    return game


def update_music_points(g,year,artist):
    q=g['questions'][g['round']]
    answer=q['answer'] if q['answer'] is not None else year
    if answer is None:raise ValueError('Vul eerst het juiste jaartal in.')
    answer=int(answer)
    if answer<1800 or answer>2100:raise ValueError('Jaartal moet tussen 1800 en 2100 zijn.')
    q['answer']=answer
    if artist.strip() and not q['artist']:q['artist']=artist.strip()
    guesses=[]
    for pid,v in g['submissions'].items():
        try: guesses.append((pid,abs(int(v['year'])-answer),int(v['year']),v.get('artist','')))
        except (KeyError,ValueError,TypeError):continue
    min_diff=min((x[1] for x in guesses),default=None)
    scored={}
    for pid,diff,yr,artist_guess in guesses:
        pts=(3 if diff==min_diff else 0)+(2 if diff==0 else 0)
        if q['artist'] and normalize(artist_guess)==normalize(q['artist']):pts+=1
        g['points'][pid]+=pts
        scored[pid]={'guess':yr,'difference':diff,'artist':artist_guess,'points':pts}
    g['round_result']={'answer':answer,'artist':q['artist'],'song':q['song'],'scores':scored}
    g['phase']='reveal'


def update_estimate_points(g):
    q=g['questions'][g['round']]
    scores=[]
    for pid,v in g['submissions'].items():
        try: scores.append((pid,abs(float(v)-q['answer']),float(v)))
        except (ValueError,TypeError):continue
    distances=sorted(set(v[1] for v in scores))
    scored={}
    for pid,diff,guess in scores:
        pts=3 if diff==distances[0] else 1 if len(distances)>1 and diff==distances[1] else 0
        g['points'][pid]+=pts
        scored[pid]={'guess':guess,'difference':diff,'points':pts}
    g['round_result']={'answer':q['answer'],'explain':q['explain'],'scores':scored}
    g['phase']='reveal'


def update_creative_points(g):
    tally={pid:0 for pid in g['points']}
    for chosen in g['votes'].values():
        if chosen in tally:tally[chosen]+=1
    for pid,pts in tally.items():g['points'][pid]+=pts
    g['round_result']={'answers':g['submissions'],'votes':tally}
    g['phase']='reveal'


def update_who_points(g):
    tally={pid:0 for pid in g['points']}
    for chosen in g['votes'].values():
        if chosen in tally:tally[chosen]+=1
    max_votes=max(tally.values(),default=0)
    majorities=[pid for pid,n in tally.items() if n==max_votes and max_votes>0]
    for voter,target in g['votes'].items():
        if target in majorities:g['points'][voter]+=1
    g['round_result']={'votes':tally,'majorities':majorities}
    g['phase']='reveal'


def update_performance_points(g):
    q=g['questions'][g['round']]
    successes={}
    for pid,submission in g['submissions'].items():
        if submission.get('correct'):
            g['points'][pid]+=2
            successes[pid]=submission.get('guess')
    if successes:g['points'][q['performer']]+=len(successes)
    g['round_result']={'answer':q['answer'],'correct':successes,
                       'forbidden':q['forbidden']}
    g['phase']='reveal'
    g['deadline']=None


def finish_game(g,winner=None):
    highest=max(g['points'].values(),default=0)
    top=[pid for pid,pts in g['points'].items() if pts==highest]
    if winner is not None:top=[winner]
    if len(top)==1:
        by_id(top[0])['wins']+=1
    S['gift']={'winner':top[0] if len(top)==1 else None,
               'tied':top if len(top)>1 else [],'category':g['category'],
               'score':highest,'finished_at':time.time()}
    S['mode']='gift'
    S['history'].append({'type':'game','category':g['category'],'points':deepcopy(g['points']),
                         'winner':top[0] if len(top)==1 else None})
    S['game']=None


def sanitized(view, token=''):
    me=player(token)
    is_admin=view=='host'
    out={
       'version':S['version'],'mode':S['mode'],'room':S['room'],
       'players':[{k:v for k,v in p.items() if k!='token'} | {'joined':bool(p['token'])}
                  for p in S['players']],
       'categories':CATEGORIES,'spin':S['spin'], 'eligible':eligible(),
       'gift':deepcopy(S['gift']), 'last_games':[h for h in S['history'] if h['type']=='game'][-8:],
       'gifts_given':len([h for h in S['history'] if h['type']=='gift']),
       'music_count':len(S['music']),'games_played':len([h for h in S['history'] if h['type']=='game']),
       'me':me['id'] if me else None,
       'history_count':len(S['history']),'started_at':S['started_at'],
       'join_url':f'http://{lan_ip()}:{PORT}/play', 'screen_url':f'http://{lan_ip()}:{PORT}/screen',
    }
    g=S['game']
    if g:
        q=g['questions'][g['round']]
        safe={'category':g['category'],'kind':g['kind'],'title':g['title'],'phase':g['phase'],
              'round':g['round']+1,'total':len(g['questions']),
              'points':g['points'],'deadline':g['deadline'],
              'submitted':[pid for pid in g['submissions']],
              'voted':[pid for pid in g['votes']],
              'result':g['round_result'] if g['phase']=='reveal' else None}
        if g['kind']=='physical':
            safe['question']=q
        else:
            safe['question']=q.get('question') or 'Raad het woord!'
        if g['kind']=='music':
            safe['source']='audio' if q['audio'] else 'hitster'
            safe['audio_url']=('/media/'+q['audio']) if q['audio'] else None
        if g['kind']=='performance':
            safe['performer']=q['performer']
            if (me and me['id']==q['performer']) or g['phase']=='reveal':
                safe['private_word']=q['answer']
                safe['forbidden']=q['forbidden']
            if me and me['id']!=q['performer']:
                safe['my_correct']=bool(g['submissions'].get(me['id'],{}).get('correct'))
        if g['kind']=='creative' and g['phase'] in ('vote','reveal'):
            safe['options']=[{'id':pid,'text':v,'mine':bool(me and me['id']==pid)}
                             for pid in g.get('option_order',list(g['submissions']))
                             for v in [g['submissions'][pid]]]
        if me:
            safe['my_submission']=g['submissions'].get(me['id'])
            safe['my_vote']=g['votes'].get(me['id'])
        out['game']=safe
    else:out['game']=None
    if is_admin:
        out['audio_files']=[{'id':m['id'],'title':m['title'],'artist':m['artist'],'year':m['year']} for m in S['music']]
    return out


class Handler(BaseHTTPRequestHandler):
    server_version='SinterklaasParty/1.0'
    def log_message(self, fmt, *args):
        if not self.path.startswith('/api/state'):
            print('%s %s' % (self.address_string(),fmt % args))

    def jsonout(self,value,status=200):
        raw=json.dumps(value,ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers()
        self.wfile.write(raw)

    def serve_file(self,path,filename=None):
        if not path.is_file():
            self.send_error(404);return
        kind=mimetypes.guess_type(filename or str(path))[0] or 'application/octet-stream'
        content=path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type',kind+('; charset=utf-8' if kind.startswith('text/') else ''))
        self.send_header('Content-Length',str(len(content)))
        self.send_header('Cache-Control','no-cache' if kind.startswith('text/') else 'private, max-age=3600')
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        parsed=urlparse(self.path)
        q=parse_qs(parsed.query)
        path=parsed.path
        if path=='/api/state':
            is_admin=(q.get('key',[''])[0]==ADMIN_KEY)
            view='host' if is_admin else 'player'
            with LOCK:self.jsonout(sanitized(view,q.get('token',[''])[0]));return
        if path=='/api/health':
            self.jsonout({'ok':True,'room':S['room']});return
        if path=='/favicon.ico':
            self.send_response(204);self.end_headers();return
        if path.startswith('/media/'):
            mid=path.removeprefix('/media/')
            if not re.fullmatch(r'[0-9a-f]{32}\.(mp3|wav|m4a|ogg)',mid):
                self.send_error(404);return
            self.serve_file(AUDIO / mid);return
        files={'/':'index.html','/host':'index.html','/screen':'index.html','/play':'index.html',
               '/app.js':'app.js','/style.css':'style.css'}
        if path in files:
            self.serve_file(STATIC / files[path]);return
        if path=='/qr.png':
            try:
                import zlib, struct
                target=q.get('url',[''])[0]
                if not target.startswith('http://') or len(target)>250:raise ValueError()
                # Bundled, BSD-licensed, pure-Python QR matrix generator.
                sys.path.insert(0,str(BASE/'vendor'))
                import qrcode
                qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4)
                qr.add_data(target);qr.make(fit=True)
                matrix=qr.get_matrix()
                scale=4;width=len(matrix)*scale;height=len(matrix)*scale
                rows=[]
                for row in matrix:
                    raw=bytes([0])+b''.join(bytes([0 if bit else 255])*scale for bit in row)
                    rows.extend([raw]*scale)
                def chunk(name,data):
                    return struct.pack('>I',len(data))+name+data+struct.pack('>I',zlib.crc32(name+data)&0xffffffff)
                data=(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,0,0,0,0))+
                      chunk(b'IDAT',zlib.compress(b''.join(rows),9))+chunk(b'IEND',b''))
                self.send_response(200)
                self.send_header('Content-Type','image/png')
                self.send_header('Content-Length',str(len(data)))
                self.send_header('Cache-Control','private, max-age=600')
                self.end_headers();self.wfile.write(data)
            except Exception as e:
                print('QR render error',repr(e));self.send_error(404)
            return
        self.send_error(404)

    def do_POST(self):
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length>22*1024*1024:raise ValueError('Bestand te groot (maximaal 20 MB).')
            path=urlparse(self.path).path
            if path=='/api/upload':
                if self.headers.get('X-Admin-Key')!=ADMIN_KEY:raise PermissionError('Alleen de host kan bestanden toevoegen.')
                data=self.rfile.read(length)
                self.upload_audio(data)
                return
            if length>1024*1024:raise ValueError('Verzoek te groot.')
            payload=json.loads(self.rfile.read(length).decode('utf-8'))
            with LOCK:
                if path=='/api/claim':result=self.claim(payload)
                elif path=='/api/submit':result=self.submit(payload)
                elif path=='/api/admin':
                    if self.headers.get('X-Admin-Key')!=ADMIN_KEY:raise PermissionError('Alleen de host kan dit doen.')
                    result=self.admin(payload)
                else:raise ValueError('Onbekende actie.')
                self.jsonout({'ok':True,'data':result,'version':S['version']})
        except PermissionError as e:self.jsonout({'error':str(e)},403)
        except (ValueError,KeyError,TypeError,IndexError) as e:self.jsonout({'error':str(e)},400)
        except Exception as e:
            print('Unexpected error',repr(e))
            self.jsonout({'error':'Er ging iets mis op de server.'},500)

    def claim(self,a):
        if str(a.get('room',''))!=S['room']:raise ValueError('Onjuiste spelcode.')
        p=by_id(a.get('player',''))
        if not p:raise ValueError('Onbekende speler.')
        token=a.get('token','')
        if p['token'] and p['token']!=token:raise ValueError('Deze plek is al bezet. Vraag de host om hem vrij te maken.')
        if not p['token']:
            p['token']=secrets.token_urlsafe(24)
            save()
        return {'token':p['token'],'player':p['id']}

    def submit(self,a):
        p=player(a.get('token',''))
        if not p:raise PermissionError('Meld je eerst aan.')
        if S['mode']!='game' or not S['game']:raise ValueError('Er loopt nu geen spel.')
        g=S['game']; phase=g['phase'];pid=p['id'];kind=g['kind']
        if kind=='estimate' and phase=='answer':
            if pid in g['submissions']:raise ValueError('Je hebt al geantwoord.')
            raw=str(a.get('value','')).strip().replace(',','.')
            if not raw or len(raw)>20:raise ValueError('Vul een getal in.')
            try:v=float(raw)
            except ValueError:raise ValueError('Vul een geldig getal in.')
            if not -1e10<v<1e10:raise ValueError('Getal buiten bereik.')
            g['submissions'][pid]=v
        elif kind=='music' and phase=='answer':
            if pid in g['submissions']:raise ValueError('Je hebt al geantwoord.')
            year=int(str(a.get('year','0')))
            if not 1800<=year<=2100:raise ValueError('Vul een jaartal tussen 1800 en 2100 in.')
            artist=str(a.get('artist','')).strip()[:80]
            g['submissions'][pid]={'year':year,'artist':artist}
        elif kind=='creative' and phase=='answer':
            if pid in g['submissions']:raise ValueError('Je hebt al geantwoord.')
            val=str(a.get('value','')).strip()
            if len(val)<2 or len(val)>200:raise ValueError('Typ een antwoord van 2–200 tekens.')
            g['submissions'][pid]=val
        elif kind=='creative' and phase=='vote':
            target=a.get('value','')
            if target not in g['submissions'] or target==pid:raise ValueError('Stem op iemand anders.')
            if pid in g['votes']:raise ValueError('Je hebt al gestemd.')
            g['votes'][pid]=target
        elif kind=='who' and phase=='answer':
            target=a.get('value','')
            if not by_id(target):raise ValueError('Kies een speler.')
            if pid in g['votes']:raise ValueError('Je hebt al gestemd.')
            g['votes'][pid]=target
        elif kind=='performance' and phase=='answer':
            q=g['questions'][g['round']]
            if pid==q['performer']:raise ValueError('De uitvoerder mag niet raden.')
            if g['submissions'].get(pid,{}).get('correct'):raise ValueError('Je hebt het al goed.')
            guess=str(a.get('value','')).strip()[:100]
            if not guess:raise ValueError('Typ een gok.')
            correct=normalize(guess) in [normalize(w) for w in [q['answer']]+q.get('aliases',[])]
            g['submissions'][pid]={'guess':guess,'correct':correct}
            # No correctness scoring until reveal; can guess again on mistake.
        else:raise ValueError('Deze actie kan nu niet.')
        save()
        return {'accepted':True,'correct':correct if kind=='performance' else None}

    def admin(self,a):
        action=a.get('action','')
        if action=='configure':
            if S['mode']!='setup':raise ValueError('De instellingen kunnen alleen vóór het spel worden gewijzigd.')
            entries=a.get('players',[])
            if len(entries)!=4:raise ValueError('Vul vier spelers in.')
            names=[];targets=[]
            for entry in entries:
                name=str(entry.get('name','')).strip()[:28]
                target=int(entry.get('target',0))
                if not name:raise ValueError('Iedere speler heeft een naam nodig.')
                if not 0<=target<=99:raise ValueError('0 tot 99 cadeaus per persoon.')
                names.append(name);targets.append(target)
            if len(set(normalize(n) for n in names))!=4:raise ValueError('Gebruik vier verschillende namen.')
            if any(targets) and not all(targets):raise ValueError('Vul voor iedereen een aantal cadeaus in, of laat ze allemaal op 0.')
            for p,name,target in zip(S['players'],names,targets):
                p['name']=name;p['target']=target
            save();return {'configured':True}
        if action=='start':
            if S['mode']!='setup':raise ValueError('Het spel is al begonnen.')
            S['mode']='wheel';S['started_at']=time.time()
            save();return {'started':True}
        if action=='release_seat':
            p=by_id(a.get('player',''))
            if not p:raise ValueError('Onbekende speler.')
            p['token']=None;save();return {'released':p['id']}
        if action=='spin':
            if S['mode']!='wheel':raise ValueError('Eerst het vorige spel afronden.')
            chosen=choose_category()
            S['mode']='spinning'
            S['spin']={'category':chosen,'stamp':uuid.uuid4().hex,'at':time.time()}
            save();return {'category':chosen}
        if action=='start_game':
            if S['mode']!='spinning':raise ValueError('Het rad draait niet.')
            S['game']=make_game(S['spin']['category'])
            S['mode']='game';save();return {'game':S['game']['category']}
        if action=='open_vote':
            g=S['game']
            if S['mode']!='game' or not g or g['kind']!='creative' or g['phase']!='answer':raise ValueError('Niet beschikbaar.')
            if len(g['submissions'])<2:raise ValueError('Wacht op minstens 2 antwoorden.')
            g['option_order']=list(g['submissions'].keys());RNG.shuffle(g['option_order'])
            g['phase']='vote';save();return {'phase':'vote'}
        if action=='reveal':
            g=S['game']
            if S['mode']!='game' or not g:raise ValueError('Er is geen lopend spel.')
            if g['phase']=='reveal':raise ValueError('Al onthuld.')
            if g['kind']=='estimate' and g['phase']=='answer':update_estimate_points(g)
            elif g['kind']=='music' and g['phase']=='answer':
                year=a.get('year','')
                y=int(year) if str(year).strip() else None
                update_music_points(g,y,str(a.get('artist','')))
            elif g['kind']=='creative' and g['phase']=='vote':update_creative_points(g)
            elif g['kind']=='who' and g['phase']=='answer':update_who_points(g)
            elif g['kind']=='performance' and g['phase']=='answer':update_performance_points(g)
            else:raise ValueError('Niet in de onthulfase.')
            save();return {'phase':'reveal'}
        if action=='next':
            g=S['game']
            if S['mode']!='game' or not g or g['phase']!='reveal':raise ValueError('Er is nog niets onthuld.')
            if g['round']+1==len(g['questions']):
                finish_game(g)
            else:
                g['round']+=1;g['phase']='answer';g['submissions']={};g['votes']={}
                g['round_result']=None
                if g['kind']=='performance':g['deadline']=time.time()+85
                else:g['deadline']=None
            save();return {'advanced':True}
        if action=='physical_result':
            g=S['game'];pid=a.get('winner','')
            if S['mode']!='game' or not g or g['kind']!='physical':raise ValueError('Dit is geen fysiek spel.')
            if not by_id(pid):raise ValueError('Kies een winnaar.')
            g['points'][pid]=1
            finish_game(g,pid)
            save();return {'winner':pid}
        if action=='choose_winner':
            gift=S['gift'];pid=a.get('winner','')
            if S['mode']!='gift' or not gift or gift['winner'] is not None:raise ValueError('Geen gelijkspel om op te lossen.')
            if pid not in gift['tied']:raise ValueError('Kies een speler met gelijke stand.')
            gift['winner']=pid;gift['tied']=[]
            by_id(pid)['wins']+=1
            for event in reversed(S['history']):
                if event['type']=='game':event['winner']=pid;break
            save();return {'winner':pid}
        if action=='give_gift':
            gift=S['gift'];pid=a.get('recipient','')
            if S['mode']!='gift' or not gift or not gift['winner']:raise ValueError('Er moet eerst een winnaar bekend zijn.')
            if pid not in eligible():raise ValueError('Deze speler heeft deze cadeauronde al iets ontvangen of is klaar.')
            by_id(pid)['received']+=1
            S['history'].append({'type':'gift','recipient':pid,'winner':gift['winner'],
                                 'category':gift['category'],'at':time.time()})
            S['gift']=None
            if any(p['target'] for p in S['players']) and not eligible():
                S['mode']='finished'
            else:S['mode']='wheel'
            save();return {'recipient':pid}
        if action=='undo_gift':
            if S['mode'] not in ('wheel','finished'):raise ValueError('Kan nu niet ongedaan worden gemaakt.')
            if not S['history'] or S['history'][-1]['type']!='gift':raise ValueError('Geen recente cadeau-uitdeling.')
            gift=S['history'].pop()
            recipient=by_id(gift['recipient']);recipient['received']=max(0,recipient['received']-1)
            S['gift']={'winner':gift['winner'],'tied':[],'category':gift['category'],'score':0}
            S['mode']='gift';save();return {'undone':True}
        if action=='finish':
            if S['mode'] not in ('wheel','gift','finished'):raise ValueError('Eerst deze minigame afronden.')
            S['mode']='finished';save();return {'finished':True}
        if action=='reset':
            code=str(a.get('confirmation',''))
            if code!='RESET':raise ValueError('Typ RESET om te bevestigen.')
            music=deepcopy(S['music'])
            S.clear();S.update(init_state());S['music']=music
            save();return {'reset':True}
        if action=='delete_audio':
            mid=a.get('id','')
            m=next((m for m in S['music'] if m['id']==mid),None)
            if not m:raise ValueError('Audio niet gevonden.')
            S['music'].remove(m)
            try:(AUDIO/m['id']).unlink()
            except OSError:pass
            save();return {'deleted':True}
        raise ValueError('Onbekende hostactie.')

    def upload_audio(self,raw):
        # Browser posts FormData as multipart; limited to a single ≤20MB audio file.
        from email.parser import BytesParser
        from email.policy import default
        header=self.headers.get('Content-Type','')
        if not header.startswith('multipart/form-data;'):raise ValueError('Gebruik een audiobestand.')
        msg=BytesParser(policy=default).parsebytes((f'Content-Type: {header}\r\nMIME-Version: 1.0\r\n\r\n').encode()+raw)
        fields={}
        for part in msg.iter_parts():
            disp=part.get('Content-Disposition','')
            name=part.get_param('name',header='content-disposition')
            if name:fields[name]=part
        file=fields.get('audio')
        if not file:raise ValueError('Geen audiobestand gekozen.')
        title=fields.get('title').get_content().strip()[:100] if fields.get('title') else ''
        artist=fields.get('artist').get_content().strip()[:100] if fields.get('artist') else ''
        year=int(fields.get('year').get_content().strip()) if fields.get('year') else 0
        if not 1800<=year<=2100:raise ValueError('Ongeldig jaartal.')
        if not title or not artist:raise ValueError('Titel en artiest zijn verplicht.')
        filename=file.get_filename() or 'audio.mp3'
        ext=Path(filename).suffix.lower()
        if ext not in ('.mp3','.wav','.ogg','.m4a'):raise ValueError('Alleen MP3, WAV, OGG of M4A.')
        payload=file.get_payload(decode=True)
        if not payload or len(payload)>20*1024*1024:raise ValueError('Audio moet kleiner zijn dan 20 MB.')
        AUDIO.mkdir(exist_ok=True)
        mid=uuid.uuid4().hex+ext
        (AUDIO/mid).write_bytes(payload)
        with LOCK:
            S['music'].append({'id':mid,'title':title,'artist':artist,'year':year})
            save()
        self.jsonout({'ok':True,'title':title})


def lan_ip():
    override=os.environ.get('PARTY_IP','').strip()
    if override:return override
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255',1));return s.getsockname()[0]
    except OSError:return '127.0.0.1'
    finally:s.close()


def main():
    host=lan_ip()
    print('\n'+'='*62)
    print('  🎁  SINTERKLAAS PARTY CHALLENGE')
    print('='*62)
    print('  Host / laptop : http://127.0.0.1:%s/host?key=%s' % (PORT,ADMIN_KEY))
    print('  TV-scherm     : http://%s:%s/screen' % (host,PORT))
    print('  Telefoons     : http://%s:%s/play' % (host,PORT))
    print('  Spelcode      : %s' % S['room'])
    print('\n  Alle apparaten op dezelfde wifi. Stop met Ctrl+C.')
    print('  Data staat lokaal: party-state.json en audio/.')
    print('='*62+'\n')
    ThreadingHTTPServer(('0.0.0.0',PORT),Handler).serve_forever()

if __name__=='__main__':
    main()
