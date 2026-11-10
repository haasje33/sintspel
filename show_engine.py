"""Sintspel 2.0: seven wheel games and one scheduled surprise game.
This engine stores only JSON-serializable state; callers serialize under the server lock.
"""
import random
import re
import time
import unicodedata
from collections import Counter
from copy import deepcopy
from difflib import SequenceMatcher

R = random.SystemRandom()
WHEEL = [
    {"id":"classic","name":"Muziektijdlijn","icon":"🎵","color":"#B75B50"},
    {"id":"quiz","name":"Muziekquiz","icon":"🎤","color":"#A86D35"},
    {"id":"quiplash","name":"Quiplash","icon":"💬","color":"#7159A5"},
    {"id":"who3","name":"Wie van de 3?","icon":"🕵️","color":"#407F95"},
    {"id":"yahtzee","name":"Yahtzee-sprint","icon":"🎲","color":"#388568"},
    {"id":"cards","name":"Kaartenduel","icon":"🃏","color":"#A64C6D"},
    {"id":"taboo","name":"Verboden woord","icon":"🤫","color":"#65823C"},
]
ERAS = [
    {"id":"6070","name":"60s & 70s","low":1960,"high":1979,"boundary":1970},
    {"id":"8090","name":"80s & 90s","low":1980,"high":1999,"boundary":1990},
    {"id":"0010","name":"00s & 10s","low":2000,"high":2019,"boundary":2010},
    {"id":"20s","name":"20s","low":2020,"high":2029,"boundary":None},
]
QUIZ_TYPES = ["artist","title","year5","year3","before"]
QUESTIONS = [
    "Wat is het slechtste excuus om niet naar pakjesavond te komen?",
    "Welke onzinnige nieuwe wet zou Sinterklaas invoeren?",
    "Wat is de slechtste naam voor een nieuwe snoepwinkel?",
    "Wat staat er op het visitekaartje van een mislukte superheld?",
    "Welke zin wil je absoluut niet horen bij de kapper?",
    "Wat zou een pepernoot zeggen als hij kon praten?",
    "Waarom is de stoomboot dit jaar te laat?",
    "Bedenk een volkomen nutteloze huishoudelijke uitvinding.",
    "Wat is het ergste dat je kunt vinden in een surprise?",
    "Wat zou je zeggen bij de slechtste sollicitatie ooit?",
    "Wat was het slechtste idee van het afgelopen jaar?",
    "Welk bord zou bij de voordeur van het huis van Sinterklaas hangen?",
    "Welke baan bestaat alleen in een heel vreemd sprookjesbos?",
    "Wat is de meest bizarre reden om je buurman te bellen?",
    "Wat zou je met een miljoen chocoladeletters doen?",
    "Welke extra regel moet iedereen volgen tijdens het uitpakken?",
]
TABOO = [
    ("sinterklaas",["baard","mijter","cadeau"],[]),
    ("paraplu",["regen","nat","open"],[]),
    ("stofzuiger",["vloer","schoonmaken","zuigen"],[]),
    ("verjaardag",["taart","feest","leeftijd"],[]),
    ("koelkast",["koud","eten","keuken"],[]),
    ("bioscoop",["film","scherm","popcorn"],[]),
    ("vliegtuig",["vliegen","lucht","piloot"],[]),
    ("pannenkoek",["beslag","stroop","bakken"],[]),
    ("bibliotheek",["boeken","lenen","stil"],[]),
    ("afstandbediening",["televisie","knoppen","zappen"],["remote"]),
    ("winkelwagen",["supermarkt","boodschappen","kar"],[]),
    ("sneeuwpop",["sneeuw","wortel","winter"],[]),
    ("luchtballon",["lucht","mand","vliegen"],[]),
    ("brandweer",["vuur","blussen","wagen"],[]),
    ("tandarts",["tanden","boren","mond"],[]),
    ("verrekijker",["kijken","ver","lenzen"],[]),
    ("pepernoot",["sinterklaas","speculaas","snoep"],[]),
    ("treinstation",["spoor","trein","perron"],[]),
    ("vakantie",["reizen","hotel","vrij"],[]),
    ("fietsbel",["fietsen","rinkelen","stuur"],[]),
]
GROCERIES = [
    "melk","eieren","brood","boter","kaas","koffie","thee","suiker","rijst","pasta",
    "appels","bananen","aardappelen","tomaten","komkommer","wortels","ui","knoflook",
    "yoghurt","havermout","chocolade","beschuit","jam","stroop","mayonaise","mosterd",
    "broccoli","paprika","champignons","citroen","sinaasappels","druiven","sla",
    "gehakt","kipfilet","vissticks","bloem","olie","azijn","zout","peper",
    "koekjes","honing","pindakaas","crackers","rozijnen","ijs","spinazie",
    "frisdrank","vruchtensap","wc-papier","afwasmiddel","zeep","tandpasta","shampoo",
]
ALIASES = {"johnny b goode":["johnny be good"],"the best":["simply the best"]}
def canonical(value):
    s = unicodedata.normalize("NFKD",str(value or "").casefold())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\b(?:and|en)\b|&"," en ",s)
    s = re.sub(r"[^a-z0-9]+"," ",s).strip()
    return re.sub(r"^the ","",s)

def equivalent(guess,answer,aliases=(),kind="title"):
    g,a=canonical(guess),canonical(answer)
    if not g or not a:return False
    valid=[a]+[canonical(x) for x in aliases]+[canonical(x) for x in ALIASES.get(a,[])]
    if kind=="artist":
        # A participant may give any credited artist (not a substring of a single name).
        valid += [canonical(x) for x in re.split(r"\s+(?:and|en|feat\.?|ft\.?|featuring)\s+|[&,;/]+",str(answer),flags=re.I) if x.strip()]
    for x in valid:
        if g==x:return True
        if min(len(g),len(x))>=5 and (abs(len(g)-len(x))<=2 and SequenceMatcher(None,g,x).ratio()>=.81):
            return True
        # A substantial, distinctive phrase may be a sufficient partial answer.
        if len(g)>=9 and (x.startswith(g+" ") or x.endswith(" "+g)) and len(g)>=len(x)*.60:
            return True
    return False

def new(players):
    ids=[p["id"] for p in players]
    return {"version":2,"mode":"setup","wheel_left":[g["id"] for g in WHEEL],
        "cycle":1,"history":[],"played":0,"gifts_given":0,"used_hidden":[],
        "game":None,"gift":None,"surprise":{"status":"waiting","first_after":R.choice([1,2]),
        "later_after":None,"list":[],"deadline":None,"answers":{},"result":None},
        "turn":0,"wins":{pid:0 for pid in ids},"received":{pid:0 for pid in ids},
        "targets":{pid:9 for pid in ids},"overrides":{}}

def ensure(S):
    if not isinstance(S.get("v2"),dict) or S["v2"].get("version")!=2:
        S["v2"]=new(S["players"])
    return S["v2"]

def ids(S):return [p["id"] for p in S["players"]]
def pick_chooser(S,v,offset=0):return ids(S)[(v["turn"]+offset)%len(ids(S))]
def cards(S):
    merged={c["url"]:c for c in S.get("hitster_cards",[]) if c.get("url")}
    for c in S.get("bundled_cards",[]):
        if c.get("url") and c["url"] not in merged:merged[c["url"]]=c
    return list(merged.values())

def hidden_card(S,v,candidates):
    used=set(v["used_hidden"])
    available=[c for c in candidates if c["id"] not in used]
    if not available:
        if not candidates:raise ValueError("Geen geschikte muziekkaarten in de collectie.")
        # Prefer the oldest last-played card when the full collection is exhausted.
        available=sorted(candidates,key=lambda c:v["used_hidden"].index(c["id"]) if c["id"] in used else -1)
        v["used_hidden"]=[]
    card=R.choice(available)
    v["used_hidden"].append(card["id"])
    return card

def chosen_classic(S,v,level):
    bank=cards(S)
    if len(bank)<3:raise ValueError("Voor Muziektijdlijn zijn minstens drie geïmporteerde kaarten nodig.")
    diff={"easy":(10,100),"medium":(4,12),"hard":(1,5)}
    lo,hi=diff[level]
    options=[]
    for c in bank:
        years=[o for o in bank if o["id"]!=c["id"] and o["year"]!=c["year"]]
        pairs=[]
        for i,a in enumerate(years):
            for b in years[i+1:]:
                if a["year"]==b["year"]:continue
                year=[a["year"],b["year"],c["year"]]
                nearest=min(abs(c["year"]-a["year"]),abs(c["year"]-b["year"]))
                if lo<=nearest<=hi and (max(year)-min(year))<= (55 if level=="easy" else 24 if level=="medium" else 10):
                    pairs.append((a,b))
        if pairs:options.append((c,pairs))
    if not options:raise ValueError("Geen geschikte "+level+" combinatie: voeg kaarten uit ontbrekende jaartallen toe.")
    unused=[x for x in options if x[0]["id"] not in v["used_hidden"]] or options
    card,pairs=R.choice(unused)
    a,b=R.choice(pairs)
    if card["id"] not in v["used_hidden"]:v["used_hidden"].append(card["id"])
    refs=sorted((a,b),key=lambda x:x["year"])
    correct="left" if card["year"]<refs[0]["year"] else "right" if card["year"]>refs[1]["year"] else "middle"
    return {"card_id":card["id"],"answer":correct,"correct_card":card,
        "refs":[{"id":r["id"],"artist":r["artist"],"title":r["title"],"year":r["year"]} for r in refs],
        "level":level,"worth":{"easy":1,"medium":2,"hard":4}[level]}

def chosen_quiz(S,v,era):
    e=next((x for x in ERAS if x["id"]==era),None)
    if not e:raise ValueError("Onbekende muziekperiode.")
    bank=[x for x in cards(S) if e["low"]<=int(x["year"])<=e["high"]]
    if not bank:raise ValueError("Geen nummers in deze periode. Importeer eerst meer kaarten.")
    c=hidden_card(S,v,bank)
    types=[x for x in QUIZ_TYPES if x!="before" or e["boundary"] is not None]
    qtype=R.choice(types)
    return {"card_id":c["id"],"answer":c["artist"] if qtype=="artist" else c["title"] if qtype=="title" else c["year"],
        "correct_card":c,"type":qtype,"era":era,"boundary":e["boundary"] if qtype=="before" else None}

def random_deck():
    suits=["♥","♦","♠","♣"]
    pack=[{"suit":s,"rank":r,"name":("A" if r==14 else "K" if r==13 else "Q" if r==12 else "J" if r==11 else str(r))} for s in suits for r in range(2,15)]
    R.shuffle(pack)
    drawn=[]
    while len(drawn)<4:
        c=pack.pop()
        if len(drawn)==1 and c["rank"]==drawn[0]["rank"]:continue
        if len(drawn)==2 and c["rank"] in [drawn[0]["rank"],drawn[1]["rank"]]:continue
        drawn.append(c)
    return drawn

def fresh_game(S,v,category):
    pids=ids(S)
    g={"category":category,"round":0,"rounds":8 if category in ("classic","quiz","yahtzee","cards","taboo") else 4,
       "phase":"choice" if category in ("classic","quiz") else "answer",
       "points":{pid:0 for pid in pids},"submissions":{},"votes":{},"question":None,
       "result":None,"overrides":{},"choosers":pids[:],"started_at":time.time(),"deadline":None}
    if category=="quiplash":
        g["prompts"]=R.sample(QUESTIONS,4);g["question"]={"prompt":g["prompts"][0]}
    if category=="who3":
        g["phase"]="facts";g["facts"]={};g["turns"]=[]
        g["rounds"]=4
    if category=="yahtzee":
        tasks=R.sample(["sum","same","specific","straight"]*2,8)
        g["tasks"]=tasks;g["question"]={"task":tasks[0],"target":R.randrange(1,7) if tasks[0]=="specific" else None}
    if category=="cards":
        g["phase"]="answer";g["duels"]=[]
        g["question"]={"deck":random_deck(),"stage":0,"active":pids[:],"stage_guesses":{},"winners":[]}
    if category=="taboo":
        bank=R.sample(TABOO,8)
        g["words"]=bank;g["question"]={"performer":pick_chooser(S,v),"answer":bank[0][0],"forbidden":bank[0][1],"aliases":bank[0][2]}
        g["phase"]="ready"
    return g

def determine_yahtzee(q,subs):
    task=q["task"];results={};bonuses=set()
    for pid,val in subs.items():
        try:
            dice=[int(x) for x in val["dice"]]
            if len(dice)!=5 or any(d<1 or d>6 for d in dice):continue
        except (KeyError,TypeError,ValueError):continue
        if len(set(dice))==1:bonuses.add(pid);continue
        if task=="sum":score=sum(dice)
        elif task=="same":score=max(Counter(dice).values())
        elif task=="specific":score=dice.count(q["target"])
        else:
            distinct=set(dice)
            score=max((len(set(range(i,j+1))) for i in range(1,7) for j in range(i,7) if set(range(i,j+1)).issubset(distinct)),default=1)
        results[pid]=score
    winners=[p for p,x in results.items() if x==max(results.values())] if results else []
    points={p:(3 if p in bonuses else 1 if p in winners else 0) for p in subs}
    return points,{"bonuses":list(bonuses),"task_winners":winners,"values":results}

def grading(S,v):
    g=v["game"];q=g["question"];cat=g["category"];result={"answers":deepcopy(g["submissions"]),"correct":{},"points":{}}
    inc={p:0 for p in ids(S)}
    if cat=="classic":
        result["reveal"]={"answer":q["answer"],"card":q["correct_card"],"refs":q["refs"]}
        for p,answer in g["submissions"].items():
            correct=answer==q["answer"]
            result["correct"][p]=correct
            inc[p]=q["worth"] if correct else 0
    elif cat=="quiz":
        result["reveal"]={"answer":q["answer"],"card":q["correct_card"],"type":q["type"],"boundary":q["boundary"]}
        for p,answer in g["submissions"].items():
            if q["type"]=="artist":good=equivalent(answer,q["answer"],kind="artist")
            elif q["type"]=="title":good=equivalent(answer,q["answer"])
            elif q["type"] in ("year5","year3"):
                try:good=abs(int(answer)-int(q["answer"]))<= (5 if q["type"]=="year5" else 3)
                except (ValueError,TypeError):good=False
            else:good=answer==("before" if q["answer"]<q["boundary"] else "after")
            result["correct"][p]=good
            inc[p]=1 if good else 0
    elif cat=="quiplash":
        counter=Counter(g["votes"].values())
        mx=max(counter.values(),default=0)
        for p in ids(S):
            inc[p]=1 if mx and counter[p]==mx else 0
        result.update({"reveal":{"prompt":q["prompt"],"votes":dict(counter)},
                       "answers":deepcopy(g["submissions"])})
    elif cat=="yahtzee":
        inc,details=determine_yahtzee(q,g["submissions"])
        result["reveal"]=details
    elif cat=="taboo":
        correct={}
        for p,val in g["submissions"].items():
            good=bool(val.get("correct")) if isinstance(val,dict) else False
            correct[p]=good
            if good:inc[p]=1
        if any(correct.values()):inc[q["performer"]]=1
        result["correct"]=correct
        result["reveal"]={"answer":q["answer"],"forbidden":q["forbidden"],"performer":q["performer"]}
    elif cat=="cards":
        for p in q["winners"]:inc[p]=1
        result["reveal"]={"deck":q["deck"],"winners":q["winners"]}
    result["points"]=inc
    return result

def next_question(S,v):
    g=v["game"];g["round"]+=1;g["submissions"]={};g["votes"]={};g["overrides"]={};g["result"]=None;g["deadline"]=None
    cat=g["category"]
    if cat in ("classic","quiz"):
        g["question"]=None;g["phase"]="choice"
    elif cat=="quiplash":
        g["question"]={"prompt":g["prompts"][g["round"]]};g["phase"]="answer"
    elif cat=="yahtzee":
        t=g["tasks"][g["round"]]
        g["question"]={"task":t,"target":R.randrange(1,7) if t=="specific" else None};g["phase"]="answer"
    elif cat=="cards":
        g["question"]={"deck":random_deck(),"stage":0,"active":ids(S),"stage_guesses":{},"winners":[]};g["phase"]="answer"
    elif cat=="taboo":
        word=g["words"][g["round"]]
        g["question"]={"performer":pick_chooser(S,v,g["round"]),"answer":word[0],"forbidden":word[1],"aliases":word[2]}
        g["phase"]="ready"
    elif cat=="who3":g["phase"]="investigate"

def start_surprise(S,v,stage):
    s=v["surprise"]
    if stage=="memorize":
        s["status"]="memorize";s["list"]=R.sample(GROCERIES,20);s["deadline"]=time.time()+60
        v["mode"]="alarm"
    else:
        s["status"]="recall";s["deadline"]=time.time()+180;s["answers"]={}
        v["mode"]="alarm"

def transition(S,v):
    s=v["surprise"]
    if s["status"]=="waiting" and v["played"]>=s["first_after"]:
        start_surprise(S,v,"memorize");return
    if s["status"]=="hidden" and v["played"]>=s["later_after"]:
        start_surprise(S,v,"recall");return
    v["mode"]="wheel"

def end_game(S,v):
    g=v["game"];points=g["points"];top=max(points.values(),default=0)
    winners=[p for p,x in points.items() if x==top]
    v["wins"].update({p:v["wins"][p]+1 for p in winners})
    v["history"].append({"category":g["category"],"points":deepcopy(points),"winners":winners})
    v["played"]+=1;v["turn"]+=1
    v["game"]=None
    queue=[{"winner":p,"slot":j} for p in winners for j in range(2)]
    v["gift"]={"winners":winners,"queue":queue,"index":0}
    v["mode"]="gift"
    if not queue:transition(S,v)

def end_surprise(S,v):
    s=v["surprise"];answers=s["answers"];products=s["list"]
    points={}
    for p,entries in answers.items():
        matches=set()
        for entry in entries:
            for item in products:
                if item not in matches and equivalent(entry,item):
                    matches.add(item);break
        points[p]=len(matches)
    for p in ids(S):points.setdefault(p,0)
    s["result"]={"points":points,"list":products,"answers":answers}
    s["status"]="review"
    return s["result"]

def public(S,host=False,me=None):
    v=ensure(S)
    pids=ids(S)
    out={"version":v["version"],"state_version":S["version"],"mode":v["mode"],
         "host_authorized":host,"players":[{"id":p["id"],"name":p["name"],
         "joined":bool(p["token"]),"received":v["received"][p["id"]],
         "target":v["targets"][p["id"]],"wins":v["wins"][p["id"]]} for p in S["players"]],
         "room":S["room"],"me":me,"categories":WHEEL,"eras":ERAS,
         "wheel_left":v["wheel_left"],"cycle":v["cycle"],"played":v["played"],
         "gifts_given":v["gifts_given"],"gift":deepcopy(v["gift"]),"history":v["history"][-12:],
         "count_cards":len(cards(S)),"game":None,"surprise":None}
    if host:out["cards"]=cards(S)
    g=v.get("game")
    if g:
        q=g.get("question") or {}
        safe={k:deepcopy(g[k]) for k in ("category","round","rounds","phase","points","deadline")}
        safe["submitted"]=list(g["submissions"])
        safe["voted"]=list(g["votes"])
        safe["my_answer"]=g["submissions"].get(me)
        safe["my_vote"]=g["votes"].get(me)
        safe["chooser"]=pick_chooser(S,v,g["round"])
        safe["question"]={}
        cat=g["category"]
        if cat=="classic":
            if q:safe["question"]={"refs":q["refs"],"card_id":q["card_id"],"level":q["level"],"worth":q["worth"]}
        elif cat=="quiz":
            if q:safe["question"]={"card_id":q["card_id"],"type":q["type"],"era":q["era"],"boundary":q["boundary"]}
            if q and q["type"] in ("artist","title"):
                # Full collection only; do not reveal the currently selected answer.
                safe["suggestions"]=sorted(set(c["artist" if q["type"]=="artist" else "title"] for c in cards(S)))
        elif cat=="quiplash":
            safe["question"]={"prompt":q.get("prompt")}
            if g["phase"] in ("vote","review"):
                safe["options"]=[{"id":p,"text":value} for p,value in g["submissions"].items()]
        elif cat=="who3":
            safe["facts_ready"]=list(g["facts"])
            if g["phase"]!="facts" and g["turns"]:
                t=g["turns"][g["round"]]
                safe["question"]={"investigator":t["investigator"],"fact":t["fact"],"asked":t["asked"],
                      "suspects":[p for p in pids if p!=t["investigator"]]}
                safe["my_answer"]=t.get("guess") if me==t["investigator"] else None
            if g["phase"]=="review":safe["who_reveal"]=g["turns"]
        elif cat=="yahtzee":safe["question"]={"task":q.get("task"),"target":q.get("target")}
        elif cat=="cards":
            stage=q.get("stage",0)
            safe["question"]={"stage":stage,"active":q.get("active",[]),
                 "deck":q.get("deck",[])[:stage],"remaining":4-stage,"winners":q.get("winners",[])}
            safe["my_answer"]=q.get("stage_guesses",{}).get(me)
        elif cat=="taboo":
            safe["question"]={"performer":q.get("performer")}
            if (me==q.get("performer") or host) and g["phase"] in ("ready","answer"):
                safe["private_word"]=q.get("answer")
                safe["forbidden"]=q.get("forbidden")
            if g["phase"]=="review":safe["question"]["word"]=q.get("answer")
        if g["phase"]=="review":safe["result"]=deepcopy(g["result"])
        out["game"]=safe
    s=v["surprise"]
    if v["mode"]=="alarm":
        out["surprise"]={"status":s["status"],"deadline":s["deadline"],
            "list":s["list"] if s["status"]=="memorize" or s["status"]=="review" else None,
            "my_answers":s["answers"].get(me,[]),"submitted":list(s["answers"]),
            "result":deepcopy(s["result"]) if s["status"]=="review" else None}
    return out

def handle(S,a,host=False,me=None):
    v=ensure(S);action=str(a.get("action",""))
    if action=="configure":
        if not host:raise PermissionError("Alleen de host kan dit doen.")
        if v["mode"]!="setup":raise ValueError("De spelavond is al begonnen.")
        names=a.get("names",[])
        if not isinstance(names,list) or len(names)!=4 or any(not str(n).strip() for n in names):
            raise ValueError("Vul vier namen in.")
        for p,name in zip(S["players"],names):
            p["name"]=str(name).strip()[:28]
        targets=a.get("targets",[9]*4)
        if not isinstance(targets,list) or len(targets)!=4 or any(int(x)<1 or int(x)>99 for x in targets):
            raise ValueError("Vul voor iedere speler het aantal cadeaus in.")
        v["targets"]={p["id"]:int(x) for p,x in zip(S["players"],targets)}
        return {"configured":True}
    if action=="start":
        if not host or v["mode"]!="setup":raise ValueError("Niet toegestaan.")
        v["mode"]="wheel";return {"started":True}
    if action=="reset":
        if not host or a.get("confirmation")!="RESET":raise ValueError("Typ RESET om te bevestigen.")
        S["v2"]=new(S["players"])
        return {"reset":True}
    if action=="start_game":
        if not host or v["mode"]!="wheel":raise ValueError("Geen spelkeuze mogelijk.")
        cat=a.get("category")
        if cat not in v["wheel_left"]:raise ValueError("Dit spel is in deze cyclus al gespeeld.")
        v["wheel_left"].remove(cat)
        v["game"]=fresh_game(S,v,cat)
        v["mode"]="game"
        return {"category":cat}
    if action=="cancel_game":
        if not host or v["mode"]!="game":raise ValueError("Geen minigame om te annuleren.")
        cat=v["game"]["category"]
        if cat not in v["wheel_left"]:v["wheel_left"].append(cat)
        v["game"]=None;v["mode"]="wheel"
        return {"cancelled":True}
    if action=="finish_evening":
        if not host:raise PermissionError("Alleen de host.")
        v["mode"]="finished";return {"finished":True}
    if action in ("alarm_continue","alarm_score","alarm_confirm"):
        if not host or v["mode"]!="alarm":raise ValueError("Geen alarm actief.")
        s=v["surprise"]
        if action=="alarm_continue" and s["status"]=="memorize":
            if time.time()<s["deadline"]:raise ValueError("De kijktijd loopt nog.")
            s["status"]="hidden";s["later_after"]=v["played"]+R.choice([2,3,4])
            v["mode"]="wheel";return {"hidden":True}
        if action=="alarm_score" and s["status"]=="recall":
            if time.time()<s["deadline"] and not a.get("early"):raise ValueError("De tijd loopt nog.")
            return end_surprise(S,v)
        if action=="alarm_confirm" and s["status"]=="review":
            points=s["result"]["points"];mx=max(points.values())
            winners=[p for p in ids(S) if points[p]==mx]
            v["history"].append({"category":"groceries","points":points,"winners":winners})
            for p in winners:v["wins"][p]+=1
            s["status"]="done"
            v["gift"]={"winners":winners,"queue":[{"winner":p,"slot":j} for p in winners for j in range(2)],"index":0}
            v["mode"]="gift"
            return {"winners":winners}
        raise ValueError("Onjuiste alarmfase.")
    if action=="gift":
        if not host or v["mode"]!="gift":raise ValueError("Geen cadeau-uitdeling actief.")
        gift=v["gift"];idx=gift["index"]
        if idx>=len(gift["queue"]):raise ValueError("Alle cadeaus zijn al gekozen.")
        item=gift["queue"][idx];winner=item["winner"]
        pid=a.get("recipient")
        if pid not in ids(S):raise ValueError("Ongeldige ontvanger.")
        if v["received"][pid]>=v["targets"][pid]:raise ValueError("Deze speler heeft alle cadeaus.")
        self_due=v["received"][winner]<v["targets"][winner]
        if item["slot"]==0 and self_due and pid!=winner:
            raise ValueError("Het eerste cadeau is voor de winnaar zelf.")
        if item["slot"]==1 and pid==winner:
            raise ValueError("Het tweede cadeau is voor iemand anders.")
        if (item["slot"]==1 or not self_due):
            candidates=[p for p in ids(S) if p!=winner and v["received"][p]<v["targets"][p]]
            if candidates:
                fewest=min(v["received"][p] for p in candidates)
                if pid not in [p for p in candidates if v["received"][p]==fewest]:
                    raise ValueError("Kies iemand anders met de laagste cadeaustand.")
        v["received"][pid]+=1;v["gifts_given"]+=1;gift["index"]+=1
        v["history"].append({"category":"gift","winner":winner,"recipient":pid})
        if all(v["received"][p]>=v["targets"][p] for p in ids(S)):
            v["mode"]="finished"
        elif gift["index"]>=len(gift["queue"]):
            v["gift"]=None
            if not v["wheel_left"]:
                v["wheel_left"]=[g["id"] for g in WHEEL];v["cycle"]+=1
            transition(S,v)
        return {"recipient":pid}
    if action=="save_fact":
        if not me or v["mode"]!="game" or v["game"]["category"]!="who3" or v["game"]["phase"]!="facts":
            raise ValueError("Geen feitjesronde.")
        fact=str(a.get("text","")).strip()[:300]
        if len(fact)<8:raise ValueError("Typ een bijzonder feit van minimaal 8 tekens.")
        v["game"]["facts"][me]=fact
        return {"saved":True}
    if action=="submit_groceries":
        if not me or v["mode"]!="alarm" or v["surprise"]["status"]!="recall":raise ValueError("Geen boodschappenronde.")
        if time.time()>v["surprise"]["deadline"]:raise ValueError("De tijd is om.")
        raw=a.get("items",[])
        if not isinstance(raw,list):raise ValueError("Ongeldige boodschappen.")
        v["surprise"]["answers"][me]=[str(x).strip()[:80] for x in raw[:40] if str(x).strip()]
        return {"saved":True}
    if v["mode"]!="game" or not v["game"]:raise ValueError("Er loopt geen minigame.")
    g=v["game"];q=g["question"] or {};cat=g["category"];phase=g["phase"];pids=ids(S)
    if action=="select":
        if not me or me!=pick_chooser(S,v,g["round"]) or phase!="choice":raise ValueError("Niet aan de beurt.")
        if cat=="classic":
            value=str(a.get("value",""))
            if value not in ("easy","medium","hard"):raise ValueError("Ongeldige moeilijkheid.")
            g["question"]=chosen_classic(S,v,value)
        elif cat=="quiz":
            g["question"]=chosen_quiz(S,v,str(a.get("value","")))
        else:raise ValueError("Geen keuze nodig.")
        g["phase"]="answer";return {"selected":True}
    if action=="start_timer":
        if not me or phase!="ready" or cat!="taboo" or q.get("performer")!=me:raise ValueError("Alleen de omschrijver kan de timer starten.")
        g["phase"]="answer";g["deadline"]=time.time()+60;return {"deadline":g["deadline"]}
    if action=="submit":
        if not me or phase!="answer":raise ValueError("Je kunt nu niet antwoorden.")
        if cat=="taboo":
            if me==q["performer"]:raise ValueError("De omschrijver speelt niet mee als rader.")
            guess=str(a.get("value","")).strip()[:120]
            if not guess:raise ValueError("Typ een gok.")
            if g["submissions"].get(me,{}).get("correct"):raise ValueError("Je hebt het woord al goed.")
            good=equivalent(guess,q["answer"],q.get("aliases",()))
            g["submissions"][me]={"text":guess,"correct":good}
            return {"correct":good}
        if me in g["submissions"]:raise ValueError("Je hebt al geantwoord.")
        value=a.get("value")
        if cat=="yahtzee":
            if not isinstance(value,list) or len(value)!=5 or any(not str(d).isdigit() or int(d)<1 or int(d)>6 for d in value):
                raise ValueError("Vul vijf dobbelstenen van 1 t/m 6 in.")
            g["submissions"][me]={"dice":[int(x) for x in value]}
        elif cat=="classic":
            if value not in ("left","middle","right"):raise ValueError("Kies links, midden of rechts.")
            g["submissions"][me]=value
        elif cat=="quiz":
            if not str(value).strip():raise ValueError("Vul je antwoord in.")
            g["submissions"][me]=str(value).strip()[:130]
        elif cat=="quiplash":
            text=str(value).strip()
            if len(text)<2 or len(text)>200:raise ValueError("Typ 2 tot 200 tekens.")
            g["submissions"][me]=text
        elif cat=="cards":
            if me not in q["active"]:raise ValueError("Je bent in dit duel uitgeschakeld.")
            if q.get("stage_guesses",{}).get(me):raise ValueError("Je hebt al voorspeld.")
            return card_guess(g,me,value)
        else:raise ValueError("Ongeldige actie.")
        return {"saved":True}
    if action=="vote":
        if not me or cat!="quiplash" or phase!="vote":raise ValueError("Er wordt nu niet gestemd.")
        target=a.get("value")
        if target==me or target not in g["submissions"]:raise ValueError("Kies het antwoord van een ander.")
        g["votes"][me]=target
        return {"voted":True}
    if action=="guess_who":
        if not me or cat!="who3" or phase!="investigate":raise ValueError("Niet in de onderzoekfase.")
        turn=g["turns"][g["round"]]
        if turn["investigator"]!=me:raise ValueError("Je bent niet de onderzoeker.")
        choice=a.get("value")
        if choice not in [p for p in pids if p!=me]:raise ValueError("Kies een van de drie anderen.")
        turn["guess"]=choice
        return {"guessed":True}
    if not host:raise PermissionError("Alleen de host kan dit doen.")
    if action=="who_start" and cat=="who3" and phase=="facts":
        if len(g["facts"])!=4:raise ValueError("Wacht tot iedereen een feit heeft ingevuld.")
        order=pids[:];R.shuffle(order)
        # Every fact has one non-owner investigator.
        g["turns"]=[{"investigator":order[i],"owner":order[(i+1)%4],
            "fact":g["facts"][order[(i+1)%4]],"asked":0,"guess":None} for i in range(4)]
        g["phase"]="investigate";return {"started":True}
    if action=="who_question" and cat=="who3" and phase=="investigate":
        t=g["turns"][g["round"]]
        t["asked"]=min(10,t["asked"]+1)
        return {"asked":t["asked"]}
    if action=="who_next" and cat=="who3" and phase=="investigate":
        t=g["turns"][g["round"]]
        if not t.get("guess"):raise ValueError("De onderzoeker moet iemand aanwijzen.")
        if t["guess"]==t["owner"]:g["points"][t["investigator"]]+=3
        else:
            for p in pids:
                if p!=t["investigator"]:g["points"][p]+=1
        if g["round"]+1==4:
            g["phase"]="review";g["result"]={"reveal":g["turns"],"points":g["points"]}
        else:g["round"]+=1
        return {"advanced":True}
    if action=="open_vote" and cat=="quiplash" and phase=="answer":
        if len(g["submissions"])<2:raise ValueError("Wacht op minstens twee antwoorden.")
        g["phase"]="vote";return {"open":True}
    if action=="review" and phase in ("answer","vote","ready"):
        if cat=="quiplash" and phase!="vote":raise ValueError("Stemmen eerst openen.")
        if cat=="cards" and q["stage"]<4 and len(q["active"])>1:raise ValueError("Kaartduel nog niet afgelopen.")
        g["result"]=grading(S,v)
        g["phase"]="review"
        return {"review":True}
    if action=="override" and phase=="review":
        pid=a.get("player")
        if pid not in pids or cat not in ("quiz","classic","taboo"):raise ValueError("Geen te corrigeren antwoord.")
        if pid not in g["submissions"]:raise ValueError("Geen antwoord van deze speler.")
        result=g["result"]
        currently=result["correct"].get(pid,False)
        good=bool(a.get("correct",not currently))
        result["correct"][pid]=good
        result["points"][pid]=(q.get("worth",1) if good else 0)
        if cat=="taboo":
            # Correcting a guess can also change the performer's point.
            result["points"][q["performer"]]=int(any(result["correct"].values()))
        return {"correct":good}
    if action=="confirm" and phase=="review":
        if cat!="who3":
            for p,points in g["result"]["points"].items():g["points"][p]+=points
        if g["round"]+1>=g["rounds"]:
            end_game(S,v)
            return {"finished":True}
        next_question(S,v)
        return {"next":True}
    raise ValueError("Deze actie past niet bij de huidige spelstand.")

def card_guess(g,player,value):
    q=g["question"];stage=q["stage"];pack=q["deck"]
    allowed=[("red","black"),("higher","lower"),("inside","outside"),("♥","♦","♠","♣")][stage]
    if value not in allowed:raise ValueError("Ongeldige kaartvoorspelling.")
    q["stage_guesses"][player]=value
    return {"saved":True}

def card_advance(S):
    v=ensure(S);g=v["game"]
    if not g or g["category"]!="cards" or g["phase"]!="answer":raise ValueError("Geen kaartduel.")
    q=g["question"];stage=q["stage"];deck=q["deck"];active=q["active"];guesses=q["stage_guesses"]
    if any(p not in guesses for p in active):raise ValueError("Wacht op de voorspellingen.")
    if stage==0:correct="red" if deck[0]["suit"] in ("♥","♦") else "black"
    elif stage==1:correct="higher" if deck[1]["rank"]>deck[0]["rank"] else "lower"
    elif stage==2:
        low,high=sorted([deck[0]["rank"],deck[1]["rank"]])
        correct="inside" if low<deck[2]["rank"]<high else "outside"
    else:correct=deck[3]["suit"]
    winners=[p for p in active if guesses.get(p)==correct]
    q["stage"]+=1
    q["stage_reveal"]={"correct":correct,"survivors":winners,"card":deck[stage]}
    q["stage_guesses"]={}
    if len(winners)<=1 or stage==3:
        q["winners"]=winners if winners else active
        q["active"]=q["winners"]
        g["result"]=grading(S,v)
        g["phase"]="review"
    else:q["active"]=winners
    return {"correct":correct,"survivors":q["active"]}
