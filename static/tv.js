/* Sintspel TV screens, built from the Figma file "Sintspel 2.0 — UI Design".
   Loaded before v2.js; uses its globals (state, html, name, cat, round, game …)
   at render time. All coordinates are Figma frame pixels (2560×1440). */
'use strict';
const TV_W=2560,TV_H=1440;
const FIG='/figma/';
function fitTv(){const s=Math.min(innerWidth/TV_W,innerHeight/TV_H);document.documentElement.style.setProperty('--tv-scale',String(s));}
addEventListener('resize',fitTv);fitTv();

const TV_CONFETTI=[[7,19,2005,610,0,'rgba(255,199,108,.55)'],[19,25,1984.8,117.7,-145,'rgba(255,230,169,.79)'],[19,19,2423.6,1034.3,128,'rgba(255,199,108,.79)'],
 [7,25,454.4,926.3,99,'rgba(255,230,169,.55)'],[13,25,2101.6,425,-17,'rgba(255,230,169,.67)'],[19,25,411.9,616.1,-133,'rgba(255,230,169,.79)'],
 [7,25,2081.9,709.7,111,'rgba(255,230,169,.55)'],[13,31,445.4,1157.1,82,'rgba(246,93,168,.67)'],[13,25,471,354.3,-5,'rgba(255,230,169,.67)'],
 [19,31,2149.6,198.3,-34,'rgba(246,93,168,.79)'],[19,25,1994.4,970.1,-121,'rgba(255,230,169,.79)'],[7,31,337.4,822.1,-150,'rgba(246,93,168,.55)'],
 [7,25,599.5,88.3,123,'rgba(255,230,169,.55)'],[13,31,2193.5,523.2,94,'rgba(246,93,168,.67)'],[19,31,326.4,515.4,-22,'rgba(246,93,168,.79)'],
 [7,31,2177,832.3,-138,'rgba(246,93,168,.55)'],[13,37,300.2,1059.1,-167,'rgba(6,185,244,.67)']];
// [file, x, y, w, h] in z-order (bottom → top); rotations are baked into the SVGs.
const TV_DECOR=[['decor-staf',2422.53,644.96,139,833.78],['decor-zak-links',-42.21,1093.99,343.74,352.03],['decor-mijter',1896.15,1099.99,362.89,392.12],
 ['decor-cadeau-links',287.51,1137.27,235.62,309.66],['decor-zak-rechts',2244.58,1098.58,290.87,333.97],['decor-schoen',492.11,1247.87,209.4,200.86]];
const TV_RING_COLORS=['#06b9f4','#f65da8','#ffc76c','#af50df'];
const box=(x,y,w,h)=>`left:${x}px;top:${y}px;width:${w}px;height:${h}px`;
const up=s=>String(s??'').toLocaleUpperCase('nl-NL');

function tvJoinUrl(){return state.join_url+'?room='+encodeURIComponent(state.room);}
function tvQr(x,y,size,ringInset,qrBox){ // rings + real join QR
 const rings=TV_RING_COLORS.map((c,i)=>`<div class="tv-abs tv-qr-ring" style="${box(x+i*ringInset,y+i*ringInset,size-2*i*ringInset,size-2*i*ringInset)};border-color:${c}"></div>`).join('');
 return `${rings}<div class="tv-abs tv-qr-box" style="${box(...qrBox)}"><img src="/qr.png?url=${encodeURIComponent(tvJoinUrl())}" alt="QR-code om mee te doen"></div>`;}
setInterval(()=>{if(page==='screen'&&game()?.category==='three'&&game()?.phase==='review'){ownerCycle++;renderApp();}},7000);
function tvScaffold({title='',titleLine=null,qr=true,decor=true,halos=true,accent=null,rule=true}={}){
 const confetti=TV_CONFETTI.map(([w,h,x,y,r,c])=>`<div class="tv-abs tv-confetti" style="${box(x,y,w,h)};background:${c};transform:rotate(${r}deg)"></div>`).join('');
 const props=decor?TV_DECOR.map(([f,x,y,w,h])=>`<img class="tv-abs tv-decor" src="${FIG}${f}.svg" alt="" style="${box(x,y,w,h)}">`).join(''):'';
 const line=titleLine??Math.round(Math.max(6,String(title).length)*36);  // 0 = no accent line
 return `<div class="tv-abs tv-wine"></div><div class="tv-abs tv-velvet"></div><div class="tv-abs tv-glow"></div>
 ${halos?'<div class="tv-abs tv-halo h1"></div><div class="tv-abs tv-halo h2"></div><div class="tv-abs tv-halo h3"></div>':''}
 ${confetti}${props}${rule?'<div class="tv-abs tv-rule"></div>':''}
 ${title?`<div class="tv-abs tv-title">${html(up(title))}</div><div class="tv-abs tv-title-line" style="width:${line}px;${line?'':'display:none'}${accent?`;background:${accent}`:''}"></div>`:''}
 ${qr?tvQr(2177,41,266,11,[2215,79,190,190]):''}`;}
function tvFrame(inner,opts={}){return `<div class="tv-viewport"><div class="tv-frame ${opts.theme?'theme-'+opts.theme:''}">${tvScaffold(opts)}${inner}</div>
 <button class="tv-sound" data-enable-sound aria-pressed="${audioEnabled}">${audioEnabled?'🔊 Geluid aan':'🔈 Geluid aanzetten'}</button></div>`;}
const tvStatus=t=>t?`<div class="tv-abs tv-status" style="left:730px;width:1100px">${t}</div>`:'';
const tvWell=(h,p='')=>`<div class="tv-abs tv-well"><h2>${h}</h2>${p?`<p>${p}</p>`:''}</div>`;

/* ---------- 00 · welcome ---------- */
function tvWelcome(){
 return tvFrame(`<div class="tv-abs tv-brand1">DE GROTE</div><div class="tv-abs tv-brand2">SINTERKLAAS</div><div class="tv-abs tv-brand3">SPELLENAVOND</div>
 <img class="tv-abs" src="${FIG}welcome-gift.svg" alt="" style="${box(1091,860,351,461)}">
 <div class="tv-abs tv-welcome-panel"></div>
 ${tvQr(1825,418,542.64,22.44,[1902.5,495.5,387.6,387.6])}
 <div class="tv-abs tv-passcode">SPELCODE ${html(state.room)}</div>
`,{qr:false});}

/* ---------- song cards ---------- */
const PASTELS=['#78c7ed','#eba1b9','#a9e6e0'];
function pastel(k){return typeof k==='number'?PASTELS[k%PASTELS.length]:PASTELS[[...String(k||'')].reduce((h,c)=>(h*31+c.charCodeAt(0))>>>0,0)%PASTELS.length];}
function songFront(c,id){return `<div class="tv-song-front" style="--bg:${pastel(id)}"><div class="artist">${html(c.artist)}</div><div class="year">${html(c.year)}</div><div class="title">${html(c.title)}</div></div>`;}
function songBack(qrUrl){const rings=[0,1,2,3,4,5,6,7].map(i=>`<img class="ring" src="${FIG}classic-cardback-ring-${i}.svg" alt="">`).join('');
 return `<div class="tv-song-back">${rings}<div class="qr">${qrUrl?`<img src="${html(qrUrl)}" alt="QR-code van het geheime nummer">`:''}</div></div>`;}

/* ---------- choosing (10 · classic difficulty, 20 · quiz era) ---------- */
const LEVELS=[['easy','MAKKELIJK','1','#65dec0'],['medium','GEMIDDELD','2','#06b9f4'],['hard','MOEILIJK','4','#f65da8']];
const ERAS_TV=[['60s & 70s','1960–1979','#ffc76c'],['80s & 90s','1980–1999','#f65da8'],['00s & 10s','2000–2019','#06b9f4'],['20s','2020–heden','#65dec0']];
function tvChoose(g){const r=round(),classic=g.category==='classic';
 const cards=classic?LEVELS.map(([,l,p,c])=>`<div class="tv-choice level" style="--c:${c}"><b>${l}</b><span>${p}</span></div>`).join('')
  :ERAS_TV.map(([e,p,c])=>`<div class="tv-choice era" style="--c:${c}"><b>${html(e)}</b><span>${p}</span></div>`).join('');
 return tvFrame(`<div class="tv-abs tv-chooser" style="top:${classic?390:386}px;font-size:${classic?136:138}px">${html(up(pl(r.chooser)?.name))} KIEST</div>
 <div class="tv-abs tv-choice-row" style="top:${classic?658:687}px;gap:${classic?91:52}px">${cards}</div>`,{title:cat(g.category).name});}

/* ---------- 11/12 · Muziek Classic timeline ---------- */
const SLOT_X=[231.5,983.5,1733.5],DOT_X=[511,1263,2013];
function classicSlots(r,ended){ // returns [refA slot, refB slot, hidden slot]
 if(!ended)return [0,2,1];
 return {left:[1,2,0],middle:[0,2,1],right:[0,1,2]}[r.correct]||[0,2,1];}
function tvClassic(g){const r=round(),ended=g.phase==='reveal';const [a,b,h]=classicSlots(r,ended);
 const lvl=LEVELS.find(l=>l[0]===r.level);
 const card=(slot,inner,extra='')=>`<div class="tv-abs tv-song ${extra}" style="left:${SLOT_X[slot]}px;top:422px" data-slot="${slot}">${inner}</div>`;
 return tvFrame(`${lvl?`<div class="tv-abs" style="left:560px;width:1440px;top:328px;text-align:center;font-size:56px;color:${lvl[3]}">${lvl[1]} · ${lvl[2]} ${lvl[2]==='1'?'PUNT':'PUNTEN'}</div>`:''}
 ${card(a,songFront(r.ref[0],0))}${card(b,songFront(r.ref[1],2))}
 ${card(h,`<div class="tv-flip-inner">${songBack(r.qr_url)}${r.song?songFront(r.song,1):''}</div>`,`tv-flip hidden-card ${ended?'revealed':''}`)}
 <div class="tv-abs tv-axis"></div>${DOT_X.map(x=>`<img class="tv-abs tv-axis-dot" src="${FIG}classic-timeline-dot.svg" alt="" style="left:${x}px">`).join('')}
 ${ended?'':`<div class="tv-abs tv-mark">?</div>`}
 ${ended?'':tvStatus(answersCount(g))}`,{title:cat(g.category).name});}

/* ---------- 21/22/23 · Muziek Quiz ---------- */
const QTYPES=[['title','TITEL','#ffc76c',448,73],['artist','ARTIEST','#f65da8',747.6,290.7],['year5','JAARTAL<br>± 5','#06b9f4',633.2,642.8],
 ['year3','JAARTAL<br>± 3','#65dec0',262.9,642.8],['boundary','VOOR OF<br>NA','#af50df',148.4,290.7]];
const QFILES=['quiz-wheel-sector-1-titel','quiz-wheel-sector-2-artiest','quiz-wheel-sector-3-jaartal5','quiz-wheel-sector-4-jaartal3','quiz-wheel-sector-5-voorofna'];
let quizWheelShown='',quizWheelUntil=0;
function eraRange(era){return (ERAS_TV.find(e=>e[0]===era)||[])[1]||era;}
function quizResultLabel(t){return {title:'TITEL',artist:'ARTIEST',year5:'JAARTAL ±5',year3:'JAARTAL ±3',boundary:'VOOR OF NA'}[t]||'';}
function tvQuizWheel(g,spinning){const r=round(),i=Math.max(0,QTYPES.findIndex(q=>q[0]===r.question_type));
 const lamps=Array.from({length:50},(_,k)=>{const a=k*7.2*Math.PI/180;return `<img class="tv-abs tv-lamp" src="${FIG}quiz-wheel-lamp.svg" alt="" style="left:${(1280+464*Math.sin(a)-8).toFixed(1)}px;top:${(766-464*Math.cos(a)-8).toFixed(1)}px">`;}).join('');
 const to=1800-i*72;
 return tvFrame(`<div class="tv-abs tv-badge">${html(eraRange(r.era))}</div>
 <img class="tv-abs" src="${FIG}quiz-wheel-outer-gold-ring.svg" alt="" style="left:794px;top:280px">
 <img class="tv-abs" src="${FIG}quiz-wheel-outer-navy-rim.svg" alt="" style="left:808px;top:294px">
 <div class="tv-abs tv-qwheel"><div class="tv-qwheel-rot ${spinning?'spin':''}" style="--to:${to}deg;${spinning?'':`transform:rotate(${to}deg)`}">
  ${QFILES.map(f=>`<img src="${FIG}${f}.svg" alt="">`).join('')}
  ${QTYPES.map(([,l,,x,y])=>`<div class="tv-qwheel-label" style="left:${x}px;top:${y}px">${l}</div>`).join('')}</div>
  <div class="tv-qwheel-hub"><img class="tv-abs" src="${FIG}quiz-wheel-hub-gold.svg" alt="" style="left:344px;top:344px"><img class="tv-abs" src="${FIG}quiz-wheel-hub-bordeaux.svg" alt="" style="left:355px;top:355px"><img class="tv-abs" src="${FIG}quiz-wheel-hub-innerring.svg" alt="" style="left:371px;top:371px"><div class="note">♫</div></div></div>
 ${lamps}<img class="tv-abs" src="${FIG}quiz-wheel-pointer.svg" alt="" style="left:1219px;top:254px">
 <div class="tv-abs tv-result-slot ${spinning?'pending':'show'}">${spinning?'?':quizResultLabel(r.question_type)}</div>`,{title:cat(g.category).name});}
function tvQuizQuestion(g){const r=round();
 return tvFrame(`<div class="tv-abs tv-question cream">${html(up(quizPrompt(r)))}</div>
 <div class="tv-abs tv-song" style="left:982.5px;top:544px">${songBack(r.qr_url)}</div>
 ${tvStatus(answersCount(g))}`,{title:cat(g.category).name});}
function quizAnswerText(r){const s=r.song;if(!s)return '';const t=r.question_type;
 if(t==='artist')return s.artist;if(t==='title')return s.title;if(t==='boundary')return (s.year<r.boundary?'VÓÓR ':'VANAF ')+r.boundary;return String(s.year);}
function tvQuizReveal(g){const r=round();
 return tvFrame(`<div class="tv-abs tv-headline">${html(up(quizAnswerText(r)))}</div>
 <div class="tv-abs tv-song" style="left:970px;top:580px;width:615px;height:594px">${r.song?songFront(r.song,2):''}</div>`,{title:cat(g.category).name});}
function tvQuiz(g){const r=round(),marker=`${g.index}-${r.hidden_id}`;
 if(g.phase==='reveal')return tvQuizReveal(g);
 if(quizWheelShown!==marker){quizWheelShown=marker;quizWheelUntil=Date.now()+6500;setTimeout(()=>{lastRender='';renderApp();},6600);}
 if(Date.now()<quizWheelUntil)return tvQuizWheel(g,Date.now()<quizWheelUntil-1500);
 return tvQuizQuestion(g);}

/* ---------- 80–83 · boodschappenspel ---------- */
const GRID_COLORS=['#ffc76c','#06b9f4','#f65da8','#65dec0'];
const ring=(file,x,y)=>`<img class="tv-abs" src="${FIG}${file}.svg" alt="" style="left:${x}px;top:${y}px">`;
function groceryGrid(items){return `<div class="tv-abs tv-grid">${items.map((it,i)=>`<div class="tv-grid-item" style="--c:${GRID_COLORS[i%4]}"><i></i><span style="font-size:${fitSize(it,62,11)}px">${html(up(it))}</span></div>`).join('')}</div>`;}
function tvGrocery(){const sh=state.show,gr=sh.grocery||{},mode=sh.mode,title='Boodschappenlijst';
 if(mode==='grocery_alarm'){
  const rings=[[940,414],[974,448],[1008,482],[1042,516],[1076,550]].map(([x,y],i)=>ring('grocery-alarm-ring-'+i,x,y)).join('');
  const beacon=(side,fx,rx,sx)=>`<img class="tv-abs tv-flare ${side}" src="${FIG}grocery-beacon-flare.svg" alt="" style="left:${fx}px;top:325px">
   <img class="tv-abs tv-rim ${side}" src="${FIG}grocery-beacon-rim.svg" alt="" style="left:${rx}px;top:560px">
   <img class="tv-abs tv-siren ${side}" src="${FIG}grocery-siren.svg" alt="" style="left:${sx}px;top:591px">`;
  return tvFrame(`<div class="tv-abs tv-alarm-wash"></div>${rings}${beacon('l',-13,217,248)}${beacon('r',1763,1993,2024)}
  <div class="tv-abs tv-alarm-big">ALARM!</div>
  <div class="tv-abs tv-alarm-sub">${gr.phase==='alarm_recall'?'WAT STOND ER OP DE LIJST?':'ONTHOUD DE BOODSCHAPPEN'}</div>`,{title,titleLine:612,theme:'alarm',halos:false});}
 if(mode==='grocery_study')return tvFrame(`<div class="tv-abs tv-timer-small" data-countdown="${gr.deadline}">01:00</div>${groceryGrid(gr.items||[])}`,{title,titleLine:578,accent:'#f65da8'});
 if(mode==='grocery_recall')return tvFrame(`<div class="tv-abs tv-timer-big" data-countdown="${gr.deadline}">03:00</div>
  ${tvStatus(`${gr.responses_count||0} van 4 lijstjes ingeleverd`)}`,{title,titleLine:578,accent:'#f65da8',halos:false});
 // review
 const scores=Object.entries(gr.review||{}).map(([pid,v])=>`${html(pl(pid)?.name||'')} ${v.score}`).join(' · ');
 return tvFrame(`<div class="tv-abs tv-subline">CONTROLE VAN DE LIJST</div>${groceryGrid(gr.items||[])}${tvStatus(scores)}`,{title,titleLine:578,accent:'#f65da8'});}

/* ---------- 90 · winnaars, 91 · cadeautijd, 99 · afsluiting ---------- */
function namesLine(ids){return ids.map(id=>up(pl(id)?.name||'')).join(' & ');}
function fitSize(text,base,maxChars){const n=String(text).length;return n<=maxChars?base:Math.max(Math.round(base*.45),Math.floor(base*maxChars/n));}
function tvWinners(g){const scores=g.scores||{},top=Math.max(0,...Object.values(scores));
 const winners=top>0?Object.keys(scores).filter(p=>scores[p]===top):[];
 const names=winners.length?namesLine(winners):'GEEN WINNAAR';
 const line=state.players.map(p=>`${html(p.name)} ${scores[p.id]??0}`).join(' · ');
 return tvFrame(`<div class="tv-abs tv-win-panel"><div class="names" style="font-size:${fitSize(names,winners.length?172:130,17)}px">${html(names)}</div>
  <div class="trophy">${winners.length?'🏆':'🎄'}</div>${winners.length?'':'<div class="none">Niemand scoorde punten · deze keer geen cadeau</div>'}</div>
  <div class="tv-abs tv-win-game">${html(up(cat(g.category).name))}</div>${tvStatus(line)}`,{title:'De winnaars',titleLine:396});}
function tvGift(){const g=state.show.gift||{winners:[]},names=namesLine(g.winners),many=g.winners.length>1;
 const rings=[[1020.75,724],[1032.72,742],[1048.7,760],[1063.31,778]].map(([x,y],i)=>ring('gift-spot-ring-'+i,x,y)).join('');
 const t=names;
 return tvFrame(`<div class="tv-abs tv-gift-name" style="font-size:${fitSize(t,145,24)}px">${html(t)}</div>
  <div class="tv-abs tv-gift-sub">${many?'MOGEN EEN CADEAU KIEZEN':'MAG EEN CADEAU KIEZEN'}</div>
  ${rings}<img class="tv-abs" src="${FIG}gift-present.svg" alt="" style="left:1052.31px;top:746px">`,{title:'Cadeautijd!',titleLine:374});}
function tvFinale(){const rings=[[990,804],[1019,833],[1048,862],[1077,891],[1106,920]].map(([x,y],i)=>ring('finale-light-ring-'+i,x,y)).join('');
 return tvFrame(`<div class="tv-abs tv-finale1">DE KERSTBOOM</div><div class="tv-abs tv-finale2">MAG VAN ZOLDER!</div>
  ${rings}<img class="tv-abs" src="${FIG}finale-present.svg" alt="" style="left:1085.34px;top:846px">`,{});}

/* ---------- 30–32 · Quiplash ---------- */
const PCOL=['#ffc76c','#f65da8','#06b9f4','#65dec0'];  // player colours in seat order
const SLOTCOL=['#f65da8','#06b9f4','#65dec0','#ffc76c'];  // answer slots A–D
function splitPrompt(t){const w=String(t).split(' ');if(w.length<4)return [t,''];const mid=Math.ceil(w.length/2);return [w.slice(0,mid).join(' '),w.slice(mid).join(' ')];}
function tvQuiplash(g){const r=round();
 if(g.phase==='vote'){const opts=r.options||[];
  return tvFrame(`<div class="tv-abs tv-quip-grid">${opts.map((o,i)=>`<div class="tv-quip-card" style="--c:${SLOTCOL[i%4]}"><b>${'ABCD'[i]}</b><span>${html(o.text)}</span></div>`).join('')}</div>
  ${tvStatus(`${r.voted?.length||0} van 4 stemmen binnen`)}`,{title:'Quiplash'});}
 if(g.phase==='reveal'){const pts=r.points||{},win=Object.keys(pts).filter(p=>pts[p]>0);
  const names=win.length?namesLine(win):'GEEN STEMMEN';
  return tvFrame(`<div class="tv-abs tv-quip-head">DE STEMMEN ZIJN BINNEN</div>
  <div class="tv-abs tv-quip-panel"><div class="names" style="font-size:${fitSize(names,155,14)}px">${html(names)}</div>${win.length?'<div class="pts">+1</div>':''}</div>`,{title:'Quiplash',titleLine:0});}
 const [l1,l2]=splitPrompt(up(r.prompt));
 return tvFrame(`<div class="tv-abs tv-quip-line" style="top:412px;font-size:${fitSize(l1,104,30)}px">${html(l1)}</div>
 ${l2?`<div class="tv-abs tv-quip-line gold" style="top:581px;font-size:${fitSize(l2,102,30)}px">${html(l2)}</div>`:''}
 <div class="tv-abs tv-status-cards">${state.players.map((p,i)=>`<div class="tv-pcard ${(r.submitted||[]).includes(p.id)?'on':''}" style="--c:${PCOL[i]}"><b>${html(up(p.name))}</b><i></i></div>`).join('')}</div>`,{title:'Quiplash'});}

/* ---------- 40–42 · Wie van de 3? ---------- */
function dossier(pid,slot,x,y,small=false){const p=pl(pid);
 return `<div class="tv-abs tv-dossier ${small?'small':''}" style="left:${x}px;top:${y}px">
  <div class="strip"></div><div class="clip"></div><div class="medal"><img src="${FIG}three-portrait-${'abc'[slot]}.svg" alt=""></div>
  <div class="seal">${'ABC'[slot]}</div>${small?'':`<div class="divider"></div><div class="who">${html(up(p?.name||''))}</div>`}</div>`;}
let ownerCycle=0;
function tvThree(g){const r=round(),ids=state.players.map(p=>p.id);
 const suspects=ids.filter(id=>id!==r.investigator);
 const titleOpts={title:'Wie van de 3?',titleLine:442,accent:'#06b9f4'};
 if(g.phase==='review'){const rounds=g.rounds||[],k=ownerCycle%Math.max(1,rounds.length),rr=rounds[k]||{};
  const slot=Math.max(0,ids.filter(id=>id!==rr.investigator).indexOf(rr.owner));
  return tvFrame(`<div class="tv-abs tv-three-panel"></div><div class="tv-abs tv-three-strip"></div>
  <div class="tv-abs tv-three-kicker" style="top:407px;font-size:45px;left:826px;width:905px">HET VERHAAL WAS VAN</div>
  <div class="tv-abs tv-three-name" style="top:451px">${html(up(pl(rr.owner)?.name||''))}</div>
  ${dossier(rr.owner,slot,947,663,true)}<img class="tv-abs" src="${FIG}three-magnifier-large.svg" alt="" style="left:1776px;top:423px">
  <div class="tv-abs tv-three-story">“${html(rr.story||'')}” · ${k+1}/${rounds.length}</div>`,titleOpts);}
 if(g.phase==='reveal'){const s=r.guess,slot=Math.max(0,suspects.indexOf(s));
  const who=up(pl(r.investigator)?.name||'');
  return tvFrame(`<div class="tv-abs tv-three-panel"></div><div class="tv-abs tv-three-strip"></div>
  <div class="tv-abs tv-three-kicker">${html(who)} ${s?'VERDENKT':'KOOS NIEMAND'}</div>
  <div class="tv-abs tv-three-name">${s?html(up(pl(s)?.name||'')):'—'}</div>
  ${s?dossier(s,slot,947,663,true):''}<img class="tv-abs" src="${FIG}three-magnifier-large.svg" alt="" style="left:1776px;top:423px">
  ${tvStatus('Van wie het verhaal is, blijft geheim tot alle vier de verhalen geweest zijn.')}`,titleOpts);}
 return tvFrame(`<img class="tv-abs" src="${FIG}three-connections.svg" alt="" style="left:210px;top:347px">
 <div class="tv-abs tv-three-q"><span style="font-size:${fitSize(r.story||'',82,40)}px">“${html(up(r.story||''))}”</span></div>
 <img class="tv-abs" src="${FIG}three-magnifier.svg" alt="" style="left:209px;top:290px">
 <div class="tv-abs tv-three-bar">${html(up(pl(r.investigator)?.name||''))} ONDERZOEKT &nbsp;&nbsp; ${r.questions_used} / 10 VRAGEN</div>
 ${suspects.map((id,i)=>dossier(id,i,[250,985,1720][i],570)).join('')}`,titleOpts);}

/* ---------- 50 · Yahtzee-sprint ---------- */
const DICE=[['dice-3',250,630,9],['dice-6',663,594,-7],['dice-1',1088,618,3],['dice-5',1513,589,-10],['dice-4',1926,626,8]];
function diceTask(r){return {sum:'HOOGSTE SOM',pairs:'MEESTE DEZELFDE',target:`MEESTE ${r.target}-EN`,straight:'LANGSTE STRAAT'}[r.rule]||'';}
function tvDice(g){const r=round(),dice=DICE.map(([f,x,y,a])=>`<img class="tv-abs tv-die" src="${FIG}${f}.svg" alt="" style="left:${x}px;top:${y}px;transform:rotate(${a}deg)">`).join('');
 let action='GOOI!',status=r.rule==='sum'?'Eén worp':'Maximaal drie keer gooien';
 if(g.phase==='reveal'){const pts=r.points||{},win=Object.keys(pts).filter(p=>pts[p]>0);action=win.length?`${namesLine(win)} +1`:'GEEN PUNTEN';
  const yz=Object.entries(r.grades||{}).filter(([,v])=>v?.yahtzee).map(([p])=>pl(p)?.name);status=yz.length?`Yahtzee! ${yz.join(' & ')} +3`:'';}
 else status=`${answersCount(g)} · ${status}`;
 return tvFrame(`<div class="tv-abs tv-dice-task">${html(diceTask(r))}</div>${dice}
 <div class="tv-abs tv-dice-action" style="font-size:${fitSize(action,108,12)}px">${html(action)}</div>${tvStatus(html(status))}`,{title:'Yahtzee-sprint'});}

/* ---------- 60/61 · Kaartenduel ---------- */
const CARD_Q=['ROOD OF ZWART?','HOGER OF LAGER?','BINNEN OF BUITEN?','WELKE SOORT?'];
const CARD_X=[258.5,804.5,1350.5,1896.5];
function tvCards(g){const r=round(),cards=r.cards||[];
 const row=CARD_X.map((x,i)=>`<div class="tv-abs tv-pcard-frame playing-card ${cards[i]?'is-up':''}" style="left:${x}px;top:530px"><div class="playing-inner"><div class="playing-back"></div>${cardFace(cards[i])}</div></div>`).join('');
 const alive=(r.alive||[]).map(id=>pl(id)?.name).join(', ');
 if(r.deal_finished){const w=r.deal_winners||[],t=w.length?`${namesLine(w)} +1`:'GEEN WINNAAR';
  return tvFrame(`<div class="tv-abs tv-card-q" style="top:357px;font-size:${fitSize(t,112,20)}px">${html(t)}</div>${row}`,{title:'Kaartenduel',titleLine:374});}
 const res=g.phase==='reveal'&&r.stage_result?`Juist: ${CARD_ANSWERS[r.stage_result.correct]||r.stage_result.correct} · nog in het spel: ${alive||'niemand'}`:`Nog in het spel: ${alive} · ${answersCount(g)}`;
 return tvFrame(`<div class="tv-abs tv-card-q">${CARD_Q[r.stage]||''}</div>${row}${tvStatus(html(res))}`,{title:'Kaartenduel'});}

/* ---------- 70/71 · Verboden woord ---------- */
function tvTaboo(g){const r=round(),who=up(pl(r.performer)?.name||'');
 const cloud=`<img class="tv-abs" src="${FIG}taboo-speech-cloud.svg" alt="" style="left:449px;top:350px">`;
 if(g.phase==='reveal')return tvFrame(`${cloud}<div class="tv-abs tv-taboo-word" style="font-size:${fitSize(r.word||'',134,14)}px">${html(up(r.word||''))}</div>
  <div class="tv-abs tv-taboo-who" style="top:850px">${html(who)}</div>`,{title:'Verboden woord'});
 return tvFrame(`${cloud}<div class="tv-abs tv-taboo-timer" data-countdown="${r.deadline||''}">${r.deadline?'01:00':'01:00'}</div>
  <div class="tv-abs tv-taboo-who">${html(who)}</div>${tvStatus(r.deadline?answersCount(g):`${html(pl(r.performer)?.name||'')} start de timer op de telefoon`)}`,{title:'Verboden woord'});}

/* ---------- Pepernotenpong (intermezzo, no own Figma frame: built from the shared style) ---------- */
function tvPong(g){const r=round();
 return tvFrame(`<div class="tv-abs tv-quip-line" style="top:412px;font-size:100px">IEDEREEN ${r.throws} PEPERNOTEN</div>
 <div class="tv-abs tv-quip-line gold" style="top:581px;font-size:86px">RAAK? HET CADEAUTJE IS VOOR JOU!</div>
 <div class="tv-abs tv-status-cards">${(r.order||[]).map((id,i)=>`<div class="tv-pcard on" style="--c:${PCOL[state.players.findIndex(p=>p.id===id)]}"><b>${i+1}. ${html(up(pl(id)?.name||''))}</b><i></i></div>`).join('')}</div>`,{title:'Pepernotenpong'});}

/* ---------- spelrad (Figma 44:3) ---------- */
const WHEEL_C=[1265,610],WHEEL_R=509;
const WHEEL_STYLE={classic:['#FFD579','#B18B48','MUZIEK<br>CLASSIC'],quiz:['#F36FA1','#BA416E','MUZIEK<br>QUIZ'],quiplash:['#1EADE6','#137AAE','QUIPLASH'],
 three:['#6CD9BD','#379886','WIE VAN<br>DE 3?'],dice:['#A772D3','#8050A5','YAHTZEE'],cards:['#FDA675','#BD7243','KAARTEN<br>DUEL'],
 taboo:['#D76CA3','#A04472','VERBODEN<br>WOORD'],pong:['#D9A066','#9C6A38','PEPER-<br>NOTEN']};
// Game names on the wheel follow the design (Muziek …); the app elsewhere says Hitster.
function wheelDisc(bag){const n=bag.length,R=WHEEL_R,step=360/n;
 const pt=a=>{const r=(a-90)*Math.PI/180;return [(R+R*Math.cos(r)).toFixed(2),(R+R*Math.sin(r)).toFixed(2)];};
 const grads=bag.map((id,i)=>{const [b,e]=WHEEL_STYLE[id]||['#999','#666'];return `<radialGradient id="wg${i}" cx="${R}" cy="${R}" r="${R}" gradientUnits="userSpaceOnUse"><stop offset=".74" stop-color="${b}"/><stop offset="1" stop-color="${e}"/></radialGradient>`;}).join('');
 const wedges=n===1?`<circle cx="${R}" cy="${R}" r="${R}" fill="url(#wg0)" stroke="#B87932" stroke-width="5"/>`:bag.map((id,i)=>{const [x1,y1]=pt(i*step),[x2,y2]=pt((i+1)*step);
  return `<path d="M${R} ${R}L${x1} ${y1}A${R} ${R} 0 ${step>180?1:0} 1 ${x2} ${y2}Z" fill="url(#wg${i})" stroke="#B87932" stroke-width="5" stroke-linejoin="round"/>`;}).join('');
 return `<svg width="${2*R}" height="${2*R}" viewBox="0 0 ${2*R} ${2*R}" aria-hidden="true"><defs>${grads}</defs>${wedges}</svg>`;}
function wheelLabels(bag){const n=bag.length,step=360/n;
 return bag.map((id,i)=>{const a=((i+.5)*step-90)*Math.PI/180,r=n<=2?250:345,x=WHEEL_R+r*Math.cos(a),y=WHEEL_R+r*Math.sin(a);
  const label=(WHEEL_STYLE[id]||[,,html(up(cat(id).name))])[2],top=Math.abs(((i+.5)*step)%360-0)<40||Math.abs(((i+.5)*step)-360)<40;
  const icon=id==='pong'?'<span class="glyph">●</span>':`<img src="${FIG}icon-${id}.svg" alt="">`;
  return `<div class="tv-wlabel" style="left:${x.toFixed(1)}px;top:${y.toFixed(1)}px;font-size:${top?33:38}px">${icon}<b>${label}</b></div>`;}).join('');}
function tvWheel(){const sh=state.show,spinning=sh.mode==='spinning'&&sh.spin;
 const bag=spinning&&sh.spin.options?.length?sh.spin.options:(sh.bag.length?sh.bag:sh.enabled_games);
 const ids=state.players.map(p=>p.id);
 const turnPid=spinning&&sh.spin.turn_before!=null?ids[sh.spin.turn_before%ids.length]:sh.spin_player;
 const n=Math.max(1,bag.length),win=spinning?bag.indexOf(sh.spin.category):-1;
 const to=win>=0?1800-(win+.5)*360/n:0;
 const resultName=spinning?up(cat(sh.spin.category).name):'';
 const hint=spinning?'HET RAD DRAAIT…':(isFinite(n)&&bag.length?'DRAAI OP JE TELEFOON':'');
 const stories=sh.stories_needed&&!spinning?`<div class="tv-abs tv-wheel-note">Wie van de 3? wacht op nieuwe weetjes</div>`:'';
 return tvFrame(`<div class="tv-abs tv-wheel" style="left:${WHEEL_C[0]-WHEEL_R}px;top:${WHEEL_C[1]-WHEEL_R}px">
  <div class="tv-wheel-rot ${spinning?'spin':''}" style="--to:${to}deg">${wheelDisc(bag)}${wheelLabels(bag)}</div></div>
 <img class="tv-abs" src="${FIG}wheel-frame.svg" alt="" style="left:535px;top:-120px">
 <img class="tv-abs" src="${FIG}wheel-hub.svg" alt="" style="left:1088px;top:433px">
 <img class="tv-abs" src="${FIG}wheel-pointer.svg" alt="" style="left:1191px;top:-4px">
 <img class="tv-abs" src="${FIG}player-banner.svg" alt="" style="left:-1px;top:367px">
 <img class="tv-abs" src="${FIG}sinterklaas-face.svg" alt="" style="left:18.97px;top:371.42px">
 <div class="tv-abs tv-banner-name" style="font-size:${fitSize(up(pl(turnPid)?.name||''),98,8)}px">${html(up(pl(turnPid)?.name||''))}</div>
 <div class="tv-abs tv-wheel-hint">${hint}</div>${stories}
 ${spinning?`<div class="tv-abs tv-wheel-result"><span>${cat(sh.spin.category).icon}</span>${html(resultName)}</div>`:''}`,{halos:false,title:'',rule:false});}

/* ---------- router ---------- */
function tvGame(g){
 if(g.category==='pong')return tvPong(g);
 if(g.phase==='review'&&g.category!=='three')return tvWinners(g);
 if(g.category==='quiplash')return tvQuiplash(g);
 if(g.category==='three')return tvThree(g);
 if(g.category==='dice')return tvDice(g);
 if(g.category==='cards')return tvCards(g);
 if(g.category==='taboo')return tvTaboo(g);
 if(g.phase==='choose'&&(g.category==='classic'||g.category==='quiz'))return tvChoose(g);
 if(g.category==='classic'&&g.phase!=='review')return tvClassic(g);
 if(g.category==='quiz'&&g.phase!=='review')return tvQuiz(g);
 return tvFallback();}
function tvFallback(){ // existing (pre-Figma) screen, scaled into the TV frame until its design is implemented
 return `<div class="tv-viewport tv-legacy">${shell(legacyContent(),false)}</div>`;}
function tvScreen(){const sh=state.show,mode=sh.mode;
 if(mode==='setup')return tvWelcome();
 if(mode==='wheel'||mode==='spinning')return tvWheel();
 if(mode.startsWith('grocery_'))return tvGrocery();
 if(mode==='gift')return tvGift();
 if(mode==='finished')return tvFinale();
 if(mode==='game'&&game())return tvGame(game());
 return tvFallback();}
function tvAfterRender(){
 // Muziek Classic reveal: slide cards into chronological order, then flip.
 const hidden=document.querySelector('.tv-flip.hidden-card.revealed');
 if(hidden){const marker=`classic-${game()?.index}`;if(lastReveal!==marker){lastReveal=marker;
  const cards=[...document.querySelectorAll('.tv-song[data-slot]')];const finals=cards.map(c=>c.style.left);
  hidden.classList.remove('revealed');[cards[0].style.left,cards[1].style.left,cards[2].style.left]=[SLOT_X[0]+'px',SLOT_X[2]+'px',SLOT_X[1]+'px'];
  requestAnimationFrame(()=>requestAnimationFrame(()=>{cards.forEach((c,i)=>c.style.left=finals[i]);setTimeout(()=>hidden.classList.add('revealed'),950);}));}}
}
