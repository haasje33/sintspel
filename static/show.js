'use strict';
const $=s=>document.querySelector(s);
const view=location.pathname==='/host'?'host':location.pathname==='/screen'?'screen':location.pathname==='/play'?'phone':'home';
const adminKey=new URLSearchParams(location.search).get('key')||'';
const localKey='sint-party-token';
let token=localStorage.getItem(localKey)||'',state=null,prevSignature='',busy=false,selectedIndex=0,notice='',soundEnabled=false,audioCtx=null,lastAlarm='',pendingSpin=false;
const label={classic:'Muziektijdlijn',quiz:'Muziekquiz',quiplash:'Quiplash',who3:'Wie van de 3?',yahtzee:'Yahtzee-sprint',cards:'Kaartenduel',taboo:'Verboden woord',groceries:'Boodschappenspel'};
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const name=id=>state?.players.find(p=>p.id===id)?.name||'Speler';
const me=()=>state?.me;
const isHost=()=>view==='host'&&state?.host_authorized;
const padded=n=>String(n).padStart(2,'0');
const timeLeft=deadline=>deadline?Math.max(0,Math.ceil(deadline-Date.now()/1000)):0;
const fmt=s=>`${padded(Math.floor(s/60))}:${padded(s%60)}`;
function toast(msg){notice=msg;renderNotice();}
function renderNotice(){let e=$('#notice');if(e)e.textContent=notice;}
async function request(url,body,host=false){
 const headers={'Content-Type':'application/json'};
 if(host)headers['X-Admin-Key']=adminKey;
 const response=await fetch(url,{method:'POST',headers,body:JSON.stringify(body)});
 const data=await response.json();
 if(!response.ok)throw Error(data.error||'Onbekende fout');
 return data.data??data;
}
async function act(action,extras={},host=false){
 if(busy)return;
 busy=true;
 try{
  let result=await request('/api/v2',{action,...extras,token},host);
  if(action==='claim'){token=result.token;localStorage.setItem(localKey,token);}
  prevSignature='';await refresh();
  return result;
 }catch(e){toast('⚠ '+e.message);}
 finally{busy=false;}
}
async function legacy(action,extras){
 if(busy)return;busy=true;
 try{
  const r=await request('/api/admin',{action,...extras},true);
  prevSignature='';await refresh();toast('✅ Import voltooid');
  return r;
 }catch(e){toast('⚠ '+e.message);}
 finally{busy=false;}
}
async function join(id){
 if(busy)return;busy=true;
 try{
  const r=await request('/api/claim',{room:$('#join-room').value.trim(),player:id,token});
  token=r.token;localStorage.setItem(localKey,token);
  prevSignature='';await refresh();
 }catch(e){toast('⚠ '+e.message);}
 finally{busy=false;}
}
function sound(){
 try{
  if(!audioCtx)audioCtx=new (window.AudioContext||window.webkitAudioContext)();
  audioCtx.resume();
  soundEnabled=true;
  toast('🔔 Geluid ingeschakeld op dit apparaat');
 }catch(e){toast('Geluid kan niet worden geactiveerd');}
}
function tone(freq,duration,delay=0){
 if(!soundEnabled||!audioCtx)return;
 const o=audioCtx.createOscillator(),gain=audioCtx.createGain();
 o.type='triangle';o.frequency.value=freq;gain.gain.setValueAtTime(0.0001,audioCtx.currentTime+delay);
 gain.gain.exponentialRampToValueAtTime(.10,audioCtx.currentTime+delay+.02);
 gain.gain.exponentialRampToValueAtTime(.0001,audioCtx.currentTime+delay+duration);
 o.connect(gain);gain.connect(audioCtx.destination);
 o.start(audioCtx.currentTime+delay);o.stop(audioCtx.currentTime+delay+duration+.02);
}
function alarmSound(){[0,.24,.48,.72].forEach((d,i)=>tone(i%2?620:820,.19,d));}
function successSound(){[523,659,784].forEach((n,i)=>tone(n,.19,i*.17));}
function base(){
 return `<div class="sparkles" aria-hidden="true">✦　 ✧　 ★　 ✦</div><header class="masthead">
 <div class="brand"><span class="mijter">♛</span><div><small>DE GROTE</small><strong>SINTERKLAAS SPELLENAVOND</strong></div></div>
 <div class="mast-right"><span class="chip">${view==='host'?'🎛 Spelleider':view==='screen'?'📺 TV':'📱 Speler'}</span><span class="chip gold">KAMER ${state.room}</span></div>
 </header>`;
}
function layout(body,side=true){
 const players=state.players;
 const scoreboard=`<aside class="sidebar"><h3>🎁 Cadeaustand</h3>
 ${players.map(p=>`<div class="player-score"><div><strong>${esc(p.name)}</strong><small>${p.wins}× winnaar</small></div><b>${p.received}/${p.target}</b></div>`).join('')}
 <div class="divider"></div><small>Uitgedeeld: ${state.gifts_given} van ${players.reduce((n,p)=>n+p.target,0)} cadeaus</small>
 <small>Radcyclus ${state.cycle}</small>
 ${isHost()?`<button class="button quiet" data-do="sound">🔔 TV-geluid testen</button>`:''}
 </aside>`;
 return `<div class="stage ${side?'with-sidebar':''}"><section class="mainstage">${body}</section>${side?scoreboard:''}</div>`;
}
function home(){
 return `<div class="welcome"><div class="giant">🎁</div><h1>De Grote Sinterklaas Spellenavond</h1><p>Vier spelers, één TV en een zak vol cadeautjes.</p>
 <p><a class="button" href="/play">📱 Speel mee</a> <a class="button secondary" href="/screen">📺 TV-scherm</a></p>
 <p class="muted">Spelleider? Open de hostlink op de laptop via het startvenster.</p></div>`;
}
function setup(){
 if(!isHost())return `<div class="card"><h1>🔒 Hosttoegang ontbreekt</h1><p>Open de hostlink via start.bat op de laptop.</p><a class="button" href="http://127.0.0.1:${location.port||8765}/host">Open lokale hostlink</a></div>`;
 const players=state.players.map((p,i)=>`<div class="fields"><label>Speler ${i+1}<input class="input" id="p${i}" value="${esc(p.name)}" maxlength="28"></label><label>Cadeaus<input type="number" class="input" id="t${i}" min="1" max="99" value="${p.target}"></label></div>`).join('');
 return `<div class="card"><div class="eyebrow">🎄 Welkom bij de pakjesavond</div><h1>Klaar voor de spelshow?</h1>
 <p>Stel de spelers en het aantal cadeaus in. De muzikale bibliotheek wordt bij het opstarten geladen.</p>
 <div class="names">${players}</div>
 <div class="actions"><button class="button secondary" data-do="configure">Namen opslaan</button><button class="button" data-do="start">🎁 Start de spelshow</button></div>
 </div><div class="card"><h2>🎵 Muziekbibliotheek</h2><p>${state.count_cards} kaarten beschikbaar. De gecontroleerde collectie wordt later automatisch meegeleverd.</p>
 <form id="import"><label>CSV importeren (URL, artiest, titel, jaar)</label><input type="file" name="file" accept=".csv,.txt" required><button class="button secondary" type="submit">Importeer kaarten</button></form>
 <p class="muted">Kaarten blijven bij een reset bewaard. De huidige lokale kaarten blijven bruikbaar totdat de centrale bibliotheek is aangeleverd.</p></div>`;
}
function wheel(){
 const cats=state.categories.filter(c=>state.wheel_left.includes(c.id));
 const n=cats.length||1,arc=360/n;
 const conic=cats.map((c,i)=>`${c.color} ${i*arc}deg ${(i+1)*arc}deg`).join(',');
 const ring=`<div class="wheel-wrapper"><div class="wheel-pointer">▼</div><div class="wheel" style="background:conic-gradient(${conic})">
 ${cats.map((c,i)=>`<span class="wheel-label" style="transform:rotate(${(i+.5)*arc}deg) translateY(-111px) rotate(${-(i+.5)*arc}deg)">${c.icon}</span>`).join('')}
 <div class="wheel-center">🎁</div></div></div>`;
 return layout(`<div class="card center"><div class="eyebrow">Spelrad · Cyclus ${state.cycle}</div>
 <h1>Welk spel wordt het?</h1><p>Elk spel komt minstens één keer aan bod, daarna begint het rad opnieuw.</p>${ring}
 ${isHost()?`<div class="actions"><button class="button" data-do="wheel-spin">🎡 Draai aan het rad</button>
 <select id="direct-game" class="input">${cats.map(c=>`<option value="${c.id}">${c.icon} ${esc(c.name)}</option>`).join('')}</select>
 <button class="button secondary" data-do="direct">▶ Direct kiezen</button></div>`:`<p class="muted">De spelleider draait het rad.</p>`}
 </div>`);
}
const questions={artist:'Welke artiest?',title:'Wat is de titel?',year5:'Welk releasejaar? (± 5 jaar)',year3:'Welk releasejaar? (± 3 jaar)',before:'Vóór of vanaf het getoonde jaar?'};
const difficulty={easy:'Makkelijk · 1 punt',medium:'Gemiddeld · 2 punten',hard:'Moeilijk · 4 punten'};
function top(g){
 const cat=state.categories.find(x=>x.id===g.category);
 return `<div class="game-top"><div class="eyebrow">${cat?.icon||'🎄'} ${label[g.category]} · Ronde ${g.round+1}/${g.rounds}</div>
 <div class="scorechips">${state.players.map(p=>`<span class="chip">${esc(p.name)} <strong>${g.points[p.id]||0} p</strong></span>`).join('')}</div></div>`;
}
function qr(id){return `<img class="qr-art" src="/v2/qr.png?id=${encodeURIComponent(id)}" alt="QR-code voor het muzieknummer">`;}
function cardFront(c,extra=''){return `<div class="music-card ${extra}"><div class="music-card-head">♪ MUZIEKKAART</div><strong>${esc(c.year)}</strong><span>${esc(c.artist)}</span><small>${esc(c.title)}</small></div>`;}
function classic(g){
 if(g.phase==='choice'){
  return `<h1>Kies de moeilijkheid</h1><p>${esc(name(g.chooser))} is aan de beurt. Iedereen mag straks raden.</p>
  ${me()===g.chooser?`<div class="choice-grid">${Object.entries(difficulty).map(([x,l])=>`<button class="choice-button" data-do="select" data-value="${x}">${l}</button>`).join('')}</div>`:`<div class="waiting">⏳ ${esc(name(g.chooser))} kiest…</div>`}`;
 }
 const q=g.question,rev=g.result?.reveal,correct=rev?.answer;
 return `<h1>Waar hoort het nummer?</h1><p>${difficulty[q.level]} · Scan de verborgen QR-code met de muziekapp.</p>
 <div class="music-row ${rev?'revealed':''} result-${correct||'none'}" id="music-row">
 ${cardFront(q.refs[0],"reference leftref")}
 <div class="music-card backcard"><div class="music-card-head">VERBORGEN NUMMER</div>${rev?cardFront(rev.card,"inner-front"):qr(q.card_id)}</div>
 ${cardFront(q.refs[1],"reference rightref")}
 </div>
 ${g.phase==='answer'?`${me()&&!g.my_answer?`<div class="choice-grid three">
 <button class="choice-button" data-do="answer" data-value="left">← Links</button>
 <button class="choice-button" data-do="answer" data-value="middle">↔ Midden</button>
 <button class="choice-button" data-do="answer" data-value="right">Rechts →</button></div>`:`<p class="waiting">Antwoorden: ${g.submitted.length} van 4 · ${g.my_answer?'Je antwoord is opgeslagen.':''}</p>`}`:
 `<p class="result-head">✅ Correcte positie: ${correct==='left'?'Links':correct==='middle'?'Midden':'Rechts'}</p>${reviewPanel(g)}`}`;
}
function quiz(g){
 const choices=state.eras.filter(e=>state.count_cards>0);
 if(g.phase==='choice')return `<h1>Kies je muziekperiode</h1><p>De beurt is aan ${esc(name(g.chooser))}. Iedereen beantwoordt daarna dezelfde vraag.</p>
 ${me()===g.chooser?`<div class="choice-grid">${choices.map(e=>`<button class="choice-button" data-do="select" data-value="${e.id}">${esc(e.name)}</button>`).join('')}</div>`:`<p class="waiting">⏳ ${esc(name(g.chooser))} kiest de era…</p>`}`;
 const q=g.question,rev=g.result?.reveal,values=g.suggestions||[];
 const type=q.type,bound=q.boundary;
 let input='';
 if(type==='before')input=`<div class="choice-grid"><button class="choice-button" data-do="answer" data-value="before">Vóór ${bound}</button><button class="choice-button" data-do="answer" data-value="after">Vanaf ${bound}</button></div>`;
 else if(type.startsWith('year'))input=`<form id="answer-form"><input class="input" type="number" name="value" min="1900" max="2100" placeholder="Jaartal" required><button class="button">Verstuur</button></form>`;
 else input=`<form id="answer-form"><input class="input" name="value" id="auto-input" autocomplete="off" placeholder="Typ ${type==='artist'?'artiest':'titel'}..." required><div id="suggestions" class="suggestions"></div><button class="button">Verstuur</button></form>`;
 return `<h1>${questions[type]}</h1><p>Era: ${state.eras.find(e=>e.id===q.era)?.name||q.era} · Ieder goed antwoord = 1 punt.</p>
 <div class="quiz-card">${qr(q.card_id)}</div>
 ${g.phase==='answer'?`${me()&&!g.my_answer?input:`<p class="waiting">${g.submitted.length} van 4 antwoorden · ${g.my_answer?'Antwoord ontvangen':''}</p>`}`:
 `<div class="result-head">🎵 ${esc(rev?.card?.artist)} — ${esc(rev?.card?.title)} (${esc(rev?.card?.year)})</div>${reviewPanel(g)}`}
 <script type="application/json" id="suggestion-bank">${JSON.stringify(values).replace(/</g,'\\u003c')}</script>`;
}
function quiplash(g){
 const q=g.question,review=g.phase==='review';
 return `<h1>${esc(q.prompt)}</h1><p>Schrijf een grappig of origineel antwoord. Stem daarna op iemand anders.</p>
 ${g.phase==='answer'?(me()&&!g.my_answer?`<form id="answer-form"><textarea class="input" name="value" maxlength="200" placeholder="Jouw antwoord…" required></textarea><button class="button">Verstuur</button></form>`:`<div class="waiting">Antwoorden binnen: ${g.submitted.length}/4</div>`):''}
 ${g.phase==='vote'?`<div class="answer-grid">${(g.options||[]).map((o,i)=>`<div class="answer-card"><b>Antwoord ${i+1}</b><p>${esc(o.text)}</p>
 ${me()!==o.id&&!g.my_vote?`<button class="button secondary" data-do="vote" data-value="${o.id}">♥ Stem</button>`:''}</div>`).join('')}</div><p class="waiting">Stemmen: ${g.voted.length}/4</p>`:''}
 ${review?`${(g.options||[]).map(o=>`<p class="answer-card">${esc(o.text)}</p>`).join('')}${reviewPanel(g)}`:''}
 ${isHost()&&g.phase==='answer'?`<button class="button" data-do="open_vote">🗳 Start stemmen</button>`:''}`;
}
function who3(g){
 if(g.phase==='facts')return `<h1>Vertel een geheim over jezelf</h1><p>Een bijzonder, grappig of raar waargebeurd feit dat de anderen waarschijnlijk niet weten.</p>
 ${me()&&!g.facts_ready.includes(me())?`<form id="fact-form"><textarea class="input" name="text" maxlength="300" required placeholder="Ik heb ooit…"></textarea><button class="button">Bewaar geheim</button></form>`:`<p class="waiting">${g.facts_ready.length}/4 feitjes ingediend.</p>`}
 ${isHost()?`<button class="button" data-do="who_start">Start de onderzoeken</button>`:''}`;
 const q=g.question,done=g.phase==='review';
 return `<h1>🕵️ Wie van de 3?</h1><blockquote class="story">${esc(q.fact)}</blockquote>
 <h2>Onderzoeker: ${esc(name(q.investigator))}</h2>
 <p>Stel maximaal tien vragen in totaal aan de andere drie spelers. Je hebt ${q.asked}/10 vragen gesteld.</p>
 <div class="detective-steps">${Array.from({length:10},(_,i)=>`<span class="${i<q.asked?'on':''}">?</span>`).join('')}</div>
 ${me()===q.investigator&&!g.my_answer&&g.phase==='investigate'?`<div class="choice-grid">${q.suspects.map(p=>`<button class="choice-button" data-do="guess_who" data-value="${p}">${esc(name(p))}</button>`).join('')}</div>`:''}
 ${isHost()&&!done?`<div class="actions"><button class="button secondary" data-do="who_question">+ Vraag gesteld</button><button class="button" data-do="who_next">Volgende onderzoeker →</button></div>`:''}
 ${done?`<div class="answer-grid">${g.who_reveal.map(t=>`<p class="answer-card"><strong>${esc(name(t.investigator))} raadde ${esc(name(t.guess))}</strong><br>Werkelijk: ${esc(name(t.owner))}</p>`).join('')}</div>${reviewPanel(g)}`:''}`;
}
function yahtzee(g){
 const q=g.question,title=q.task==='sum'?'Hoogste som (één worp)':q.task==='same'?'Meeste gelijke dobbelstenen':q.task==='specific'?`Meeste ${q.target}-en`:'Langste straat';
 return `<h1>🎲 ${esc(title)}</h1><p>${q.task==='sum'?'Gooi precies één keer.':'Je mag maximaal drie keer gooien.'} Vijf gelijke = altijd 3 bonuspunten en je doet niet mee aan het opdrachtpunt.</p>
 ${g.phase==='answer'?(me()&&!g.my_answer?`<form id="dice-form" class="dice-entry">
 <div class="dice-grid">${Array.from({length:5},(_,i)=>`<select name="d${i}" class="dice"><option value="">–</option>${[1,2,3,4,5,6].map(n=>`<option value="${n}">${n}</option>`).join('')}</select>`).join('')}</div>
 <button class="button">Bewaar worp</button></form>`:`<p class="waiting">Resultaten: ${g.submitted.length}/4</p>`):reviewPanel(g)}
 ${isHost()&&g.phase==='answer'?`<button class="button" data-do="review">Onthul de worpen</button>`:''}`;
}
function playingCard(c,face){
 return `<div class="playing-card ${face?'turned':''}">
 <div class="card-3d"><div class="card-back">♛</div><div class="card-face ${c?.suit==='♥'||c?.suit==='♦'?'red-suit':''}">${c?`${c.name}<span>${c.suit}</span>`:''}</div></div></div>`;
}
function cardDuel(g){
 const q=g.question,stage=q.stage,hand=q.deck;
 const prompts=['Rood of zwart?','Hoger of lager?','Binnen of buiten?','Welke kaartsoort?'];
 const options=[['red','black'],['higher','lower'],['inside','outside'],['♥','♦','♠','♣']][stage]||[];
 const names={red:'♥ Rood',black:'♠ Zwart',higher:'↑ Hoger',lower:'↓ Lager',inside:'↔ Binnen',outside:'← → Buiten','♥':'♥ Harten','♦':'♦ Ruiten','♠':'♠ Schoppen','♣':'♣ Klaveren'};
 return `<h1>🃏 Kaartenduel</h1><p>${g.phase==='review'?'Duel afgerond.':prompts[stage]} Alleen spelers die goed voorspellen gaan door.</p>
 <div class="playing-row">${Array.from({length:4},(_,i)=>playingCard(hand[i],i<stage)).join('')}</div>
 <div class="player-pills">${state.players.map(p=>`<span class="chip ${q.active.includes(p.id)?'active':'out'}">${esc(p.name)}</span>`).join('')}</div>
 ${g.phase==='answer'&&me()&&q.active.includes(me())&&!g.my_answer?`<div class="choice-grid">${options.map(opt=>`<button class="choice-button" data-do="answer" data-value="${esc(opt)}">${names[opt]}</button>`).join('')}</div>`:''}
 ${g.phase==='answer'&&!q.active.includes(me())?'<p class="waiting">Je bent uitgeschakeld voor dit duel.</p>':''}
 ${isHost()&&g.phase==='answer'?`<button class="button" data-do="card_advance">Draai kaart ${stage+1} om →</button>`:''}
 ${g.phase==='review'?`<p class="result-head">Winnaar(s): ${q.winners.map(p=>esc(name(p))).join(', ')}</p>${reviewPanel(g)}`:''}`;
}
function taboo(g){
 const q=g.question,ready=g.phase==='ready';
 return `<h1>🤫 Verboden woord</h1><p>Omschrijver: <strong>${esc(name(q.performer))}</strong>. De andere drie spelers typen hun antwoorden.</p>
 ${g.phase==='ready'?(me()===q.performer?`<div class="secret-word"><strong>${esc(g.private_word)}</strong><p>Verboden: ${(g.forbidden||[]).map(esc).join(' · ')}</p>
 <button class="button" data-do="start_timer">▶ Start 60 seconden</button></div>`:`<p class="waiting">De omschrijver bereidt zich voor…</p>`):''}
 ${g.phase==='answer'?`<div class="countdown" data-deadline="${g.deadline}">${fmt(timeLeft(g.deadline))}</div>
 ${me()!==q.performer?`<form id="answer-form"><input name="value" class="input" placeholder="Raad het woord…" required><button class="button">Probeer</button></form>`:`<p>Omschrijf zonder de verboden woorden te gebruiken!</p>`}
 <p class="muted">${g.submitted.length}/3 spelers hebben een poging gedaan</p>`:''}
 ${isHost()&&g.phase==='answer'?`<button class="button" data-do="review">⏱ Stop & beoordeel</button>`:''}
 ${g.phase==='review'?`<div class="result-head">Het woord was: ${esc(q.word)}</div>${reviewPanel(g)}`:''}`;
}
function reviewPanel(g){
 if(g.phase!=='review')return '';
 const entries=state.players.map(p=>{
  const answer=g.result?.answers?.[p.id];
  const correct=g.result?.correct?.[p.id];
  const n=g.result?.points?.[p.id]||0;
  const txt=typeof answer==='object'?answer?.text||answer?.dice?.join(' – ')||'—':answer??'—';
  return `<div class="review-line"><strong>${esc(p.name)}</strong><span>${esc(txt)}</span>
  <b>${n} pt</b>${isHost()&&correct!==undefined&&answer!==undefined?`<button class="mini ${correct?'positive':'negative'}" data-do="override" data-player="${p.id}" data-correct="${!correct}">${correct?'✓ Goed':'✗ Fout · Keur goed'}</button>`:''}</div>`;
 }).join('');
 return `<div class="review"><h2>Uitslag controleren</h2>${entries}
 ${isHost()?`<button class="button" data-do="confirm">✅ Uitslag bevestigen</button>`:`<p class="waiting">De spelleider controleert de antwoorden.</p>`}</div>`;
}
function game(){
 const g=state.game;
 const content={classic,quiz,quiplash,who3,yahtzee,cards:cardDuel,taboo}[g.category](g);
 return layout(`<div class="card">${top(g)}${content}
 ${isHost()?`<div class="actions"><button class="button quiet" data-do="cancel">↩ Minigame annuleren</button></div>`:''}</div>`);
}
function alertPage(){
 const a=state.surprise,mem=a.status==='memorize',review=a.status==='review';
 const list=mem||review?a.list:[];
 let body=`<div class="alert-scene"><div class="siren">🚨</div><h1>ALARM!</h1><h2>${mem?'ONTHOUD DE BOODSCHAPPEN!':'WAT STOND ER OP DE LIJST?'}</h2>`;
 if(mem)body+=`<div class="countdown" data-deadline="${a.deadline}">${fmt(timeLeft(a.deadline))}</div>
 <div class="grocery-grid">${list.map(x=>`<span>🛒 ${esc(x)}</span>`).join('')}</div>
 ${isHost()?`<button class="button" data-do="alarm_continue">Lijst verbergen & verder spelen</button>`:''}`;
 else if(a.status==='recall')body+=`<div class="countdown" data-deadline="${a.deadline}">${fmt(timeLeft(a.deadline))}</div>
 <p>Typ zoveel mogelijk boodschappen. Eén punt per uniek juist product.</p>
 ${me()?`<form id="grocery-form"><textarea class="input" name="value" placeholder="Eén product per regel…">${esc((a.my_answers||[]).join('\n'))}</textarea><button class="button">Bewaar lijst</button></form>`:''}
 <p>${a.submitted.length}/4 lijsten opgeslagen</p>
 ${isHost()?`<button class="button" data-do="alarm_score">Bekijk antwoorden</button>`:''}`;
 else body+=`<div class="grocery-grid">${list.map(x=>`<span>🛒 ${esc(x)}</span>`).join('')}</div>
 <div class="scorechips">${state.players.map(p=>`<span class="chip">${esc(p.name)}: ${a.result?.points?.[p.id]||0} pt</span>`).join('')}</div>
 ${isHost()?`<button class="button" data-do="alarm_confirm">✅ Uitslag bevestigen</button>`:''}`;
 return layout(body+'</div>',false);
}
function gift(){
 const gift=state.gift,done=gift?.index||0,queue=gift?.queue||[];
 const item=queue[done];
 if(!item)return layout(`<div class="card center"><h1>🎁 Cadeaus uitdelen</h1><p>Iedereen heeft zijn keuzes gehad.</p></div>`);
 const winner=state.players.find(x=>x.id===item.winner);
 const ownDue=winner.received<winner.target;
 const selfTurn=item.slot===0&&ownDue;
 const available=state.players.filter(p=>p.received<p.target&&(selfTurn?p.id===winner.id:p.id!==winner.id));
 const fewest=Math.min(...available.map(p=>p.received));
 const eligible=selfTurn?available:available.filter(p=>p.received===fewest);
 return layout(`<div class="card center gift-scene"><div class="gift-pop">🎁</div>
 <div class="eyebrow">Cadeaus uitdelen · ${done+1}/${queue.length}</div>
 <h1>${esc(name(item.winner))} heeft gewonnen!</h1><p>${selfTurn?'Het eerste cadeau is voor de winnaar zelf.':'Kies een cadeau voor een andere speler met de laagste cadeaustand.'}</p>
 <div class="choice-grid">${eligible.map(p=>`<button class="choice-button" ${isHost()?'':'disabled'} data-do="gift" data-recipient="${p.id}">🎁 ${esc(p.name)}<br><small>${p.received}/${p.target}</small></button>`).join('')}</div>
 </div>`);
}
function finished(){
 return layout(`<div class="card center"><div class="giant">🎊</div><h1>Alle cadeautjes zijn verdeeld!</h1>
 <h2>Fijne pakjesavond!</h2><div class="scorechips">${state.players.map(p=>`<span class="chip">${esc(p.name)} · ${p.received} cadeaus</span>`).join('')}</div>
 ${isHost()?`<button class="button" data-do="reset">Nieuwe spelavond</button>`:''}</div>`);
}
function phoneJoin(){
 return `<div class="card center"><h1>📱 Doe mee!</h1><p>Kies wie jij bent en vul de viercijferige spelcode in.</p>
 <input id="join-room" class="input" value="${esc(localStorage.getItem('sint-party-room')||state.room)}" maxlength="4" inputmode="numeric">
 <div class="choice-grid">${state.players.map(p=>`<button class="choice-button" data-do="join" data-value="${p.id}">${esc(p.name)}${p.joined?' · online':''}</button>`).join('')}</div></div>`;
}
function screen(){
 if(view==='home')return home();
 if(view==='host'&&!state.host_authorized)return setup();
 if(view==='phone'&&!state.me)return phoneJoin();
 if(state.mode==='setup')return view==='host'?layout(setup()):layout(`<div class="card center"><h1>🎁 Bijna klaar!</h1><p>De spelleider stelt de spelavond in.</p></div>`);
 if(state.mode==='wheel')return wheel();
 if(state.mode==='game')return game();
 if(state.mode==='alarm')return alertPage();
 if(state.mode==='gift')return gift();
 if(state.mode==='finished')return finished();
 return layout(`<div class="card"><h2>Momentje…</h2></div>`);
}
function paint(){
 document.body.className=(state?.mode==='alarm'?'alarm-active ':'')+'view-'+view;
 $('#app').innerHTML=base()+screen()+`<footer>🎄 Pepernoten, plezier en verrassingen · Sintspel 2.0</footer>`;
 renderNotice();
 if(state.mode==='alarm'&&soundEnabled&&lastAlarm!==state.surprise.status){
  lastAlarm=state.surprise.status;alarmSound();
 }
}
function signature(){
 if(!state)return '';
 return JSON.stringify(state);
}
async function refresh(){
 try{
  const qs=new URLSearchParams();
  if(view==='host')qs.set('key',adminKey);
  if(view==='phone'&&token)qs.set('token',token);
  const r=await fetch('/api/v2/state?'+qs.toString(),{cache:'no-store'});
  if(!r.ok)throw Error('De server is niet bereikbaar.');
  state=await r.json();
  if(state.me)localStorage.setItem('sint-party-room',state.room);
  const sig=signature();
  if(sig!==prevSignature){prevSignature=sig;paint();}
  tick();
 }catch(e){if(!state)$('#app').innerHTML='<main class="welcome">⚠ Geen verbinding met Sintspel. Controleer of start.bat draait.</main>';}
}
function tick(){
 document.querySelectorAll('[data-deadline]').forEach(x=>x.textContent=fmt(timeLeft(Number(x.dataset.deadline))));
 const a=state?.surprise;
 if(a&&a.status==='memorize'&&timeLeft(a.deadline)===0)document.body.classList.add('alarm-expired');
}
function noDefault(event){event.preventDefault();event.stopPropagation();}
document.addEventListener('click',async event=>{
 const b=event.target.closest('[data-do]');
 if(!b)return;
 const type=b.dataset.do;
 if(type==='sound'){sound();return;}
 if(type==='join'){await join(b.dataset.value);return;}
 if(type==='wheel-spin'){
  const remaining=state.categories.filter(c=>state.wheel_left.includes(c.id));
  if(!remaining.length)return;
  const winner=remaining[Math.floor(Math.random()*remaining.length)];
  const wheel=$('.wheel');
  if(wheel){wheel.classList.add('spinning');b.disabled=true;}
  await new Promise(resolve=>setTimeout(resolve,2800));
  await act('start_game',{category:winner.id},true);return;
 }
 if(type==='configure'||type==='start'){
  const names=[0,1,2,3].map(i=>$(`#p${i}`).value);
  const targets=[0,1,2,3].map(i=>Number($(`#t${i}`).value));
  await act('configure',{names,targets},true);
  if(type==='start')await act('start',{},true);
  return;
 }
 if(type==='direct'){await act('start_game',{category:$('#direct-game').value},true);return;}
 if(type==='gift'){await act('gift',{recipient:b.dataset.recipient},true);successSound();return;}
 if(type==='select'){await act('select',{value:b.dataset.value});return;}
 if(type==='answer'){await act('submit',{value:b.dataset.value});return;}
 if(type==='vote'){await act('vote',{value:b.dataset.value});return;}
 if(type==='guess_who'){await act('guess_who',{value:b.dataset.value});return;}
 if(type==='cancel'){
  if(confirm('Minigame annuleren zonder punten of cadeaus?'))await act('cancel_game',{},true);
  return;
 }
 if(type==='reset'){if(prompt('Typ RESET om te bevestigen')==='RESET')await act('reset',{confirmation:'RESET'},true);return;}
 if(type==='override'){await act('override',{player:b.dataset.player,correct:b.dataset.correct==='true'},true);return;}
 if(type==='confirm'){await act('confirm',{},true);successSound();return;}
 if(type==='who_start'||type==='who_question'||type==='who_next'||type==='open_vote'||type==='review'||type==='card_advance'||type==='alarm_continue'||type==='alarm_score'||type==='alarm_confirm'){
  await act(type,{},true);return;
 }
 if(type==='start_timer'){await act('start_timer');return;}
});
document.addEventListener('submit',async event=>{
 const f=event.target;
 if(!['import','fact-form','answer-form','dice-form','grocery-form'].includes(f.id))return;
 noDefault(event);
 if(f.id==='import'){
  const file=f.querySelector('[type=file]')?.files[0];if(!file)return;
  if(file.size>300000){toast('CSV mag maximaal 300 KB zijn');return;}
  await legacy('import_hitster',{csv:await file.text()});return;
 }
 if(f.id==='fact-form'){await act('save_fact',{text:new FormData(f).get('text')});return;}
 if(f.id==='answer-form'){await act('submit',{value:new FormData(f).get('value')});return;}
 if(f.id==='dice-form'){
  const data=new FormData(f);
  await act('submit',{value:[0,1,2,3,4].map(i=>data.get(`d${i}`))});return;
 }
 if(f.id==='grocery-form'){
  const items=new FormData(f).get('value').split(/[\n,;]+/).map(x=>x.trim()).filter(Boolean);
  await act('submit_groceries',{items});return;
 }
});
document.addEventListener('input',event=>{
 if(event.target.id!=='auto-input')return;
 const raw=event.target.value.trim().toLocaleLowerCase();
 const el=$('#suggestions');if(!el)return;
 if(raw.length<3){el.innerHTML='';return;}
 const normalize=s=>s.toLocaleLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/^the\s+/,'').replace(/&|\band\b|\ben\b/g,'en');
 let bank=[];try{bank=JSON.parse($('#suggestion-bank')?.textContent||'[]');}catch{}
 const items=bank.filter(x=>normalize(x).includes(normalize(raw))).slice(0,5);
 el.innerHTML=items.map(x=>`<button type="button" class="suggestion" data-fill="${esc(x)}">${esc(x)}</button>`).join('');
});
document.addEventListener('click',event=>{
 const b=event.target.closest('[data-fill]');if(!b)return;
 const e=$('#auto-input');if(e){e.value=b.dataset.fill;$('#suggestions').innerHTML='';e.focus();}
});
refresh();
setInterval(refresh,1200);
setInterval(tick,250);
