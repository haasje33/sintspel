/* Sintspel 2.0 — LAN party-show client. No external dependencies. */
'use strict';
const $=s=>document.querySelector(s);
const page=location.pathname==='/host'?'host':location.pathname==='/screen'?'screen':location.pathname==='/play'?'phone':'home';
const key=new URLSearchParams(location.search).get('key')||'';
const tokenKey='sintspel-phone-token';
let token=localStorage.getItem(tokenKey)||'',state=null,lastRender='',busy=false,lastMode='',lastReveal='',audioEnabled=false,audioContext=null,spinHandle=null;
let cardFlash='',lastError='',importNotice='';
let alarmVoices=null;
const html=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pl=id=>state?.players?.find(p=>p.id===id);
const name=id=>html(pl(id)?.name||'Speler');
const cat=id=>state?.show?.games?.find(g=>g.id===id)||{id,name:id,icon:'🎲',color:'#8e9d9f'};
const game=()=>state?.show?.game;
const round=()=>game()?.current;
const isHost=page==='host';
const isPhone=page==='phone';
const score=(p,pts)=>`<div class="score-chip"><b>${html(p.name)}</b><span>${pts??0} pt</span></div>`;
function toast(message){lastError=String(message);const el=$('#toast');if(!el)return;el.textContent=lastError;el.classList.add('visible');setTimeout(()=>el.classList.remove('visible'),3800);}
async function request(path,body={},admin=false){
 const headers={'Content-Type':'application/json'};
 if(admin)headers['X-Admin-Key']=key;
 const res=await fetch(path,{method:'POST',headers,body:JSON.stringify(body)});
 const data=await res.json();
 if(!res.ok)throw Error(data.error||`HTTP ${res.status}`);
 return data.data;
}
async function host(action,data={}){return request('/api/admin',{action,...data},true)}
async function send(action,data={}){return request('/api/submit',{action,token,...data})}
// A continuous, two-tone wavering warning siren. Only the TV plays it,
// and only after someone has activated sound in that browser.
function stopAlarmSound(){
 if(!alarmVoices)return;
 const {oscillators,gain,nodes}=alarmVoices;alarmVoices=null;
 try{const t=audioContext.currentTime;gain.gain.cancelScheduledValues(t);
   gain.gain.setTargetAtTime(.0001,t,.035);
   oscillators.forEach(o=>o.stop(t+.18));
   setTimeout(()=>nodes.forEach(n=>{try{n.disconnect()}catch(_){}}),250);
 }catch(e){console.warn('Sirene stoppen mislukt',e);}
}
function sound(){
 if(!audioEnabled||page!=='screen'||alarmVoices)return;
 try{
  const A=window.AudioContext||window.webkitAudioContext;
  if(!A)return;
  audioContext ||=new A();
  if(audioContext.state==='suspended')audioContext.resume().catch(e=>console.warn('Audio activering nodig',e));
  const t=audioContext.currentTime+.04;
  const carrier=audioContext.createOscillator(),sweep=audioContext.createOscillator();
  const sweepDepth=audioContext.createGain(),gain=audioContext.createGain();
  carrier.type='sawtooth';carrier.frequency.setValueAtTime(660,t);
  sweep.type='sine';sweep.frequency.setValueAtTime(.88,t);
  sweepDepth.gain.setValueAtTime(285,t);
  sweep.connect(sweepDepth);sweepDepth.connect(carrier.frequency);
  carrier.connect(gain);gain.connect(audioContext.destination);
  gain.gain.setValueAtTime(.0001,t);
  gain.gain.exponentialRampToValueAtTime(.052,t+.16);
  sweep.start(t);carrier.start(t);
  alarmVoices={oscillators:[carrier,sweep],gain,nodes:[carrier,sweep,sweepDepth,gain]};
 }catch(e){console.warn('Sirene niet beschikbaar',e);}
}
function decorate(){return `<div class="decor star-one">✦</div><div class="decor star-two">✦</div><div class="decor star-three">✦</div>`;}
function header(){return `<header class="topbar ${isHost?'host-topbar':''}"><div class="brand"><span class="brand-signet">🎁</span><div><b>DE GROTE</b><strong>SINTERKLAAS SPELLENAVOND</strong></div></div>
<div class="head-right"><span class="head-label">${page==='host'?'🎛 Spelleider':page==='screen'?'📺 Spelshow':'📱 Speler'}</span><span class="roomcode">CODE ${html(state.room)}</span>${page==='screen'?`<button class="sound-toggle" data-enable-sound aria-pressed="${audioEnabled}">${audioEnabled?'🔊 Geluid aan':'🔈 Geluid aanzetten'}</button>`:''}</div></header>`;}
function scoreboard(){const show=state.show;return `<aside class="sidebar">
<h3>🎁 De cadeauzak</h3><div class="gift-progress"><div class="gift-fill" style="width:${Math.max(0,100-100*show.remaining_gifts/Math.max(1,state.players.reduce((t,p)=>t+p.target,0)))}%"></div></div>
<p class="small subtle">${show.remaining_gifts} cadeaus te gaan · ${show.gifts_given} uitgedeeld</p>
${state.players.map((p,i)=>`<div class="player-row"><div class="avatar">${['👑','🎄','⭐','🔔'][i]}</div><div class="player-details"><strong>${html(p.name)}</strong><small>${p.wins}× gewonnen</small></div><div class="player-gifts"><b>${p.received}/${p.target}</b><small>cadeaus</small></div></div>`).join('')}
${isHost?`<div class="side-tools"><button class="soft" data-act="v2_reset">↺ Nieuwe spelavond</button><a class="soft" href="/screen" target="_blank" rel="noopener">📺 TV-scherm</a></div>`:''}
</aside>`;}
function tvJoinMini(){
 // Render on every TV game view except the lobby, which already has a large QR.
 if(page!=='screen'||state?.show?.mode==='setup'||!state?.join_url||!state?.room)return '';
 const url=state.join_url+'?room='+encodeURIComponent(state.room);
 const qr='/qr.png?url='+encodeURIComponent(url);
 return `<aside class="tv-mini-join" aria-label="Opnieuw verbinden via QR-code">
  <img src="${html(qr)}" width="132" height="132" alt="Scan om deel te nemen of opnieuw te verbinden"/>
  <div class="tv-mini-caption">📱 Meedoen / opnieuw verbinden</div>
  <div class="tv-mini-room">CODE ${html(state.room)}</div>
 </aside>`;
}
function shell(content,side=true){return `${decorate()}${header()}<main class="layout ${side?'with-sidebar':'full-stage'}"><section class="stage">${content}</section>${side?scoreboard():''}</main><footer>Een avond vol verrassingen · Alleen op jullie eigen wifi</footer>${tvJoinMini()}`;}
const button=(act,label,cls='',attrs='')=>`<button class="btn ${cls}" data-act="${act}" ${attrs}>${label}</button>`;
const pill=t=>`<span class="pill">${t}</span>`;
function home(){return `<main class="entry-screen"><div class="entry-panel"><div class="big-signet">🎁</div><p class="eyebrow">Sintspel 2.0</p><h1>Welkom op de<br>pakjesavond!</h1><p>De laptop is de spelleider, de TV het speelbord en iedere speler gebruikt een telefoon.</p>
<div class="actions"><a class="btn" href="/play">📱 Speel mee</a><a class="btn alt" href="/screen">📺 TV-scherm</a></div><p class="fine">Open de beveiligde hostlink op de laptop, of ga naar <code>127.0.0.1:8765/host</code> op de serverlaptop.</p></div></main>`;}
function joinScreen(){return `<div class="stage-card welcome"><p class="eyebrow">📱 Meld je aan</p><h1>Wie ben jij?</h1><p>Vul de code van de TV in en kies jouw plek.</p><label>Viercijferige spelcode</label><input id="join-code" class="text-input" maxlength="4" inputmode="numeric" value="${html(new URLSearchParams(location.search).get('room')||localStorage.getItem('sintspel-room')||'')}" placeholder="1234">
<div class="player-options">${state.players.map((p,i)=>`<button class="player-choice" data-act="join" data-player="${p.id}" ${p.joined?'disabled':''}><span>${['🎄','⭐','🎁','🔔'][i]} ${html(p.name)}</span><small>${p.joined?'Bezet':'Meedoen →'}</small></button>`).join('')}</div></div>`;}
function setup(){const sh=state.show;
 if(isPhone){const me=sh.has_story[state.me];return `<div class="stage-card"><p class="eyebrow">✨ Voor de start</p><h1>Welkom, ${name(state.me)}</h1><p>Voer alvast een waargebeurd feitje over jezelf in dat de andere spelers vermoedelijk niet kennen.</p>
<div class="form-area"><textarea id="my-story" class="text-input" rows="3" placeholder="Bijvoorbeeld: Ik heb ooit..." minlength="12" maxlength="250"></textarea>${button('save_story','💾 Bewaar mijn weetje')}</div>
<p class="subtle">${me?'✅ Je weetje is bewaard. Je kunt het nog vervangen.':'Nog geen weetje opgeslagen.'}</p><div class="waiting">⏳ De spelleider begint de spelavond.</div></div>`;}
 if(page==='screen'){
  const joinLink=state.join_url+'?room='+encodeURIComponent(state.room);
  const joinQr='/qr.png?url='+encodeURIComponent(joinLink);
  return `<div class="stage-card welcome tv-lobby"><p class="eyebrow">🎁 Vanavond is het zover</p><h1>De grote Sinterklaas<br>Spellenavond</h1><p>De spelleider maakt de show klaar. Pak de pepernoten!</p>
  <div class="tv-join"><div class="tv-join-qr"><img src="${html(joinQr)}" alt="Scan deze QR-code met je telefoon om mee te doen" width="240" height="240"/></div>
  <div class="tv-join-instructions"><h2>📱 Scan en speel mee!</h2><p>Scan de QR-code met de camera van je telefoon. De spelcode wordt automatisch ingevuld; kies daarna je naam.</p>
  <p class="join-link">Of open <strong>${html(state.join_url)}</strong></p>
  <p class="join-room-code">Spelcode: <strong>${html(state.room)}</strong></p>
  </div></div></div>`;
 }
 const cards=sh.hitster_cards||[];
 return `<div class="stage-card"><p class="eyebrow">🎛 Voorbereiding</p><h1>Klaar voor pakjesavond?</h1><p>Geef de vier spelers een naam en stel het aantal cadeaus per speler in.</p>
<form id="setup-form" class="config-form">${state.players.map((p,i)=>`<div class="config-row"><label>Speler ${i+1}<input class="text-input" name="name${i}" maxlength="28" value="${html(p.name)}" required></label><label>Cadeaus<input class="text-input" name="target${i}" type="number" min="1" max="99" value="${p.target||9}" required></label></div>`).join('')}
<div class="actions"><button type="submit" class="btn alt">💾 Instellingen opslaan</button>${button('v2_start','🎉 Start de spelshow','gold','type="button"')}</div></form>
<div class="preflight"><h2>🕵️ Persoonlijke weetjes</h2><p>Voor Wie van de 3? moet iedere speler één waargebeurd weetje hebben ingevuld.</p>
${state.players.map(p=>`<div class="check-row"><span>${name(p.id)}</span><strong>${sh.has_story[p.id]?'✅ Ontvangen':'⏳ Nog niet ingevuld'}</strong></div>`).join('')}
<p class="fine">Spelers vullen dit op hun eigen telefoon in. Je kunt het ook namens hen doen:</p>
<select id="story-player" class="text-input">${state.players.map(p=>`<option value="${p.id}">${name(p.id)}</option>`).join('')}</select>
<textarea id="host-story" rows="2" class="text-input" placeholder="Waargebeurd weetje..."></textarea>${button('host_story','Bewaar weetje','alt')}</div>
<div class="preflight"><h2>🎵 Muziekbibliotheek</h2><p>${sh.hitster_count} kaarten beschikbaar. De QR-codes blijven bruikbaar in deze nieuwe versie.</p>
<form id="csv-import"><label>CSV met URL, artiest, titel, jaar<input id="csv-file" class="text-input" type="file" accept=".csv,.txt,text/csv" required></label><button class="btn alt" type="submit">📥 Importeer kaarten</button></form>
${importNotice?`<div class="message">${html(importNotice)}</div>`:''}
${cards.length?`<details><summary>${cards.length} kaarten bekijken en QR testen</summary><div class="library-rows">${cards.slice(-100).reverse().map(c=>`<div class="library-row"><span>${html(c.artist)} — ${html(c.title)} (${c.year})</span><a href="/hitster/test?id=${encodeURIComponent(c.id)}&key=${encodeURIComponent(key)}" target="_blank" rel="noopener">Test QR</a></div>`).join('')}</div></details>`:''}</div></div>`;}
function wheel(){const sh=state.show,spinning=sh.mode==='spinning',bag=spinning&&sh.spin?.options?.length?sh.spin.options:(sh.bag.length?sh.bag:sh.enabled_games);
 const palette=bag.map(id=>cat(id).color);const grad=palette.map((color,i)=>`${color} ${(i*360/bag.length).toFixed(2)}deg ${((i+1)*360/bag.length).toFixed(2)}deg`).join(',');
 const winningIndex=spinning?bag.indexOf(sh.spin.category):0;
 const stopAngle=2520-360*(winningIndex+.5)/bag.length;
 const spinner=sh.spin_player;
 const spinnerName=spinner?name(spinner):'de volgende speler';
 const opts=bag.map((id,i)=>`<div class="wheel-label" style="--pos:${i};--total:${bag.length}">${cat(id).icon}<small>${html(cat(id).name)}</small></div>`).join('');
 return `<div class="stage-card wheel-stage"><p class="eyebrow">🎡 ${sh.regular_completed+1}e minigame</p><h1>${spinning?'Welk spel wordt het?':'Draai aan het rad!'}</h1>
 ${bag.length?`<div class="wheel-wrap"><div class="wheel-pointer"></div><div class="wheel-disc ${spinning?'spinning':''}" style="background:conic-gradient(${grad});--segments:${bag.length};--wheel-target:${stopAngle}deg">${opts}<div class="wheel-hub">🎁</div></div></div>`:'<div class="waiting">Alle spellen zijn uitgeschakeld. De spelleider kan er hieronder één opnieuw inschakelen.</div>'}
 ${spinning?`<h2 class="result-banner wheel-result-pending">${cat(sh.spin.category).icon} ${html(cat(sh.spin.category).name)}</h2>`:`<p class="subtle">Iedere minigame verdwijnt na het spelen van het rad, tot alle zeven gespeeld zijn.</p><p class="wheel-turn">🎡 <strong>${spinnerName}</strong> is aan de beurt om te draaien.</p>`}
 ${isPhone?(spinning?'<p class="waiting">Het rad draait! Kijk naar de TV.</p>':bag.length===0?'<p class="waiting">De spelleider schakelt een spel in…</p>':state.me===spinner?button('v2_spin','🎡 Geef het rad een slinger!','gold wheel-phone-spin'):`<p class="waiting">Wacht op ${spinnerName}…</p>`):''}
 ${isHost?(spinning?button('v2_open_game','✨ Start het gekozen spel','gold'):bag.length?button('v2_spin',`🎡 Draai namens ${spinnerName}`,'gold'):''):''}
 ${isHost&&!spinning?`<div class="test-picker"><span>Rechtstreeks testen:</span><select id="quick-game" class="text-input">${bag.map(id=>`<option value="${id}">${cat(id).icon} ${html(cat(id).name)}</option>`).join('')}</select>${bag.length?button('v2_direct','Start gekozen spel','alt'):''}</div>`:''}
 ${isHost&&!spinning?`<details class="game-manager"><summary>⚙ Spellen beheren (bij problemen)</summary>
 ${sh.enabled_games.length?`<div class="game-management-row"><select id="disable-select" class="text-input">${sh.enabled_games.map(id=>`<option value="${id}">${cat(id).name}</option>`).join('')}</select>${button('v2_disable_game','⛔ Uit het rad halen','soft-btn')}</div>`:''}
 ${sh.disabled_games?.length?`<div class="game-management-row"><select id="enable-select" class="text-input">${sh.disabled_games.map(id=>`<option value="${id}">${cat(id).name}</option>`).join('')}</select>${button('v2_enable_game','↶ Opnieuw inschakelen','alt')}</div>`:'<p class="subtle">Alle spellen zijn momenteel ingeschakeld.</p>'}</details>`:''}
 </div>`;}
function topGame(g){return `<div class="game-head"><p class="eyebrow">${cat(g.category).icon} ${html(cat(g.category).name)}</p>${pill('Vraag '+(g.index+1)+' / '+g.total)}${pill(g.phase==='review'?'Einduitslag':g.phase==='reveal'?'Antwoord':'Speelronde')}</div>`;}
function cardsRow(r,phase){if(!r.ref)return '';
 const ended=phase==='reveal'||phase==='review',position=r.correct||'middle';
 const pos=ended?position:'middle';
 const x=position==='left'?[1,2,0]:position==='right'?[0,1,2]:[0,2,1];
 const left=ended?x[0]:0,right=ended?x[1]:2,hidden=ended?x[2]:1;
 const ref=c=>`<div class="song-card-front"><div class="song-disc">♫</div><div><strong>${html(c.artist)}</strong><small>${html(c.title)}</small><span class="song-year">${c.year}</span></div></div>`;
 return `<div class="timeline" data-classic="${ended?'reveal':'answer'}" data-place="${pos}">
 <div class="timeline-card" style="--slot:${left}">${ref(r.ref[0])}</div>
 <div class="timeline-card" style="--slot:${right}">${ref(r.ref[1])}</div>
 <div class="timeline-card mystery" style="--slot:${hidden}"><div class="card-flip ${ended?'revealed':''}"><div class="flip-back"><div class="qr-header">🎵 GEHEIME KAART</div>${r.qr_url?`<img class="music-qr" src="${html(r.qr_url)}" alt="QR-code">`:''}<small>Scan met de officiële app</small></div>
 <div class="flip-front">${r.song?ref(r.song):'<span>?</span>'}</div></div></div></div>`;
}
function songQuiz(r,phase){const ended=phase==='reveal'||phase==='review';return `<div class="music-spot"><div class="single-card ${ended?'revealed':''}"><div class="flip-back"><div class="qr-header">🎵 GEHEIME KAART</div>${r.qr_url?`<img class="music-qr" src="${html(r.qr_url)}" alt="QR-code">`:''}<small>Scan om te luisteren</small></div><div class="flip-front">${r.song?`<div class="song-disc">♪</div><strong>${html(r.song.artist)}</strong><span>${html(r.song.title)}</span><b>${r.song.year}</b>`:''}</div></div></div>`;}
function chooseScreen(g){const r=round(),mine=state.me===r.chooser;
 const classic=g.category==='classic';
 const choices=classic?[{v:'easy',label:'⭐ Makkelijk',sub:'1 punt'},{v:'medium',label:'⭐⭐ Gemiddeld',sub:'2 punten'},{v:'hard',label:'🔥 Moeilijk',sub:'4 punten'}]:[
 {v:'60s & 70s',label:'60s & 70s',sub:'1960–1979'},{v:'80s & 90s',label:'80s & 90s',sub:'1980–1999'},
 {v:'00s & 10s',label:'00s & 10s',sub:'2000–2019'},{v:'20s',label:'20s',sub:'2020–heden'}];
 return `<div class="stage-card">${topGame(g)}<h1>${classic?'Kies de moeilijkheid':'Kies je era'}</h1><p><strong>${name(r.chooser)}</strong> mag kiezen. Daarna beantwoordt iedereen dezelfde vraag.</p>
 ${isHost||mine?`<div class="choice-grid">${choices.map(c=>`<button class="big-choice" data-act="v2_choose" data-value="${c.v}"><strong>${c.label}</strong><small>${c.sub}</small></button>`).join('')}</div>`:`<div class="waiting">⏳ ${name(r.chooser)} is aan het kiezen…</div>`}
 ${isHost?button('v2_cancel','↩ Annuleer minigame','soft-btn'):''}</div>`;}
function quizPrompt(r){const t=r.question_type;return t==='boundary'?`Is dit nummer uitgebracht vóór ${r.boundary}, of vanaf ${r.boundary}?`:({artist:'Wie is de artiest?',title:'Wat is de titel?',year5:'In welk jaar is het uitgebracht? (±5 jaar)',year3:'In welk jaar is het uitgebracht? (±3 jaar)'})[t];}
function cardName(c){if(!c)return '?';const v=c.v===14?'A':c.v===13?'K':c.v===12?'Q':c.v===11?'J':String(c.v);return `<span class="${'HD'.includes(c.s)?'red-suit':'dark-suit'}">${v}${{H:'♥',D:'♦',C:'♣',S:'♠'}[c.s]}</span>`;}
function faceDownCards(r){return `<div class="playing-cards">${[0,1,2,3].map(i=>`<div class="playing-card ${r.cards[i]?'is-up':''}" style="animation-delay:${i*.09}s"><div class="playing-inner"><div class="playing-back">🎁<small>SINTSPEL</small></div><div class="playing-face">${cardName(r.cards[i])}</div></div></div>`).join('')}</div>`;}
function stageHint(stage){return ['Rood of zwart?','Is kaart 2 hoger of lager dan kaart 1?','Valt kaart 3 binnen of buiten de eerdere twee waarden?','Welke kaartsoort heeft kaart 4?'][stage];}
function visibleQuestion(g){const r=round(),catid=g.category;
 if(catid==='classic')return `<h1>Links, midden of rechts?</h1><p>Waar hoort het verborgen nummer in de chronologische volgorde?</p><div class="step-points">${['easy','medium','hard'].includes(r.level)?`<b>${{easy:'Makkelijk · 1 punt',medium:'Gemiddeld · 2 punten',hard:'Moeilijk · 4 punten'}[r.level]}</b>`:''}</div>${cardsRow(r,g.phase)}`;
 if(catid==='quiz')return `<h1>${html(quizPrompt(r))}</h1><p>Gekozen era: <b>${html(r.era)}</b> · ${html({artist:'Artiest',title:'Titel',year5:'Jaartal ±5 jaar',year3:'Jaartal ±3 jaar',boundary:'Vóór of vanaf'}[r.question_type])}</p>${songQuiz(r,g.phase)}`;
 if(catid==='quiplash')return `<h1>Quiplash!</h1><blockquote class="big-prompt">${html(r.prompt)}</blockquote>${g.phase==='vote'?`<div class="quip-options">${r.options?.map((o,i)=>`<div class="quip-item"><b>${['A','B','C','D'][i]}</b><span>${html(o.text)}</span></div>`).join('')}</div>`:''}`;
 if(catid==='three')return `<h1>Wie van de 3?</h1><blockquote class="big-prompt">“${html(r.story)}”</blockquote><p><strong>${name(r.investigator)}</strong> is de onderzoeker. Wie van de andere drie heeft dit meegemaakt?</p><div class="question-pips">${Array.from({length:10},(_,i)=>`<span class="${i<r.questions_used?'used':''}">${i+1}</span>`).join('')}</div>
 <p class="subtle">${r.questions_used} / 10 vragen gesteld</p>${isHost?button('v2_count_question','+ Vraag gesteld','alt',r.questions_used>=10?'disabled':''):''}`;
 if(catid==='dice')return `<h1>${html(({sum:'Hoogste som (1 worp)',pairs:'Meeste dezelfde',target:'Meeste '+r.target+'en',straight:'Langste straat'})[r.rule])}</h1><div class="dice-display">${Array.from({length:5},()=>'<div>⚄</div>').join('')}</div>
 <p>Gebruik vijf echte dobbelstenen. ${r.rule==='sum'?'Iedereen heeft één worp.':'Je mag maximaal drie keer gooien en dobbelstenen apart leggen.'}</p><div class="rule-box">🎯 Yahtzee (vijf gelijke) = altijd 3 bonuspunten, buiten de opdracht. De overgebleven spelers strijden om 1 opdrachtpunt.</div>`;
 if(catid==='cards')return `<h1>${html(stageHint(r.stage))}</h1>${faceDownCards(r)}<div class="alive-pills">${r.alive.map(p=>pill('✓ '+name(p))).join('')}${state.players.filter(p=>!r.alive.includes(p.id)).map(p=>pill('✕ '+name(p.id))).join('')}</div>`;
 if(catid==='taboo')return `<h1>Verboden woord</h1><p><strong>${name(r.performer)}</strong> omschrijft het woord. De anderen typen hun gok op hun telefoon.</p>
 <div class="timer-hero"><span data-countdown="${r.deadline||''}" data-prefix="" >${r.deadline?'01:00':'Klaar voor de start?'}</span></div>
 ${g.phase==='reveal'?`<h2 class="answer-reveal">${html(r.word||'')}</h2>`:''}`;
 return '<h1>De volgende opdracht komt eraan</h1>';
}
function answersCount(g){const r=round();return g.category==='taboo'?`${Object.values(r.all_attempts||{}).reduce((t,v)=>t+v.length,0)} pogingen`:
 g.category==='quiplash'&&g.phase==='vote'?`${r.voted?.length||0} van 4 stemmen`:
 g.category==='cards'?`${r.submitted.filter(p=>r.alive.includes(p)).length} van ${r.alive.length} antwoorden`:`${r.submitted.length} van 4 antwoorden`;}
function revealPanel(g){const r=round(),catid=g.category;
 if(catid==='three')return `<div class="reveal-box"><h2>${r.guess_skipped?'Onderzoek overgeslagen':'Verdachte aangewezen!'}</h2><p>${r.guess_skipped?'Geen antwoord: niemand krijgt punten.':'De identiteit wordt pas na alle vier de onderzoeken onthuld.'}</p></div>`;
 if(catid==='cards')return `<div class="reveal-box"><h2>${r.deal_finished?'Duel afgelopen!':'Kaart omgedraaid!'}</h2><p>${r.stage_result?'Juiste antwoord: '+html(r.stage_result.correct):''}</p>${r.deal_winners?.length?`<strong>${r.deal_winners.map(name).join(' & ')} krijgen 1 punt.</strong>`:r.deal_finished?'<p>Geen geldige winnaar deze ronde.</p>':''}</div>`;
 if(catid==='quiplash')return `<div class="reveal-box"><h2>De stemmen zijn geteld!</h2><p>Meeste stemmen = één punt, bij gelijkstand ieder één punt.</p></div>`;
 if(catid==='dice')return `<div class="reveal-box"><h2>De dobbelstenen zijn geteld!</h2><p>Yahtzee-bonussen staan los van de gewone opdracht.</p></div>`;
 return `<div class="reveal-box"><h2>Het antwoord is bekend!</h2>${r.song?`<p><strong>${html(r.song.artist)} — ${html(r.song.title)} (${r.song.year})</strong></p>`:''}${r.word?`<p>${html(r.word)}</p>`:''}</div>`;
}
function currentScoreboard(g){return `<div class="score-strip">${state.players.map(p=>score(p,g.scores[p.id])).join('')}</div>`;}
function hostRoundControls(g){const r=round();if(!isHost)return '';
 let btns='';
 if(g.phase==='answer'){
  if(g.category==='quiplash')btns=button('v2_open_vote','🗳️ Start de stemming','gold');
  else if(g.category==='taboo')btns=!r.deadline?button('v2_start_timer','⏱ Start 60 seconden','gold'):button('v2_reveal','✅ Einde ronde / antwoorden','gold');
  else if(g.category==='three')btns=button('v2_reveal','🔍 Onderzoek afronden (ook zonder antwoord)','gold');
  else btns=button('v2_reveal',g.category==='cards'?'🃏 Draai de kaart om':'✅ Antwoorden onthullen','gold');
 }else if(g.phase==='vote')btns=button('v2_reveal','🗳️ Stemmen onthullen','gold');
 else if(g.phase==='reveal')btns=button('v2_next',g.index+1===g.total?'🏆 Naar de einduitslag':'Volgende vraag →','gold');
 return `<div class="host-controls">${btns}${button('v2_cancel','↩ Annuleer minigame','soft-btn')}</div>`;
}
function phoneGame(g){const r=round(),cid=g.category;
 if(g.phase==='choose')return chooseScreen(g);
 if(g.phase==='review')return reviewScreen(g);
 const mine=r.my_answer!==null && r.my_answer!==undefined;
 const choosing=r.chooser===state.me;
 let content='';
 if(g.phase==='reveal')content=`<div class="waiting">✅ Antwoord onthuld. Kijk naar de televisie voor de uitslag.</div>`;
 else if(cid==='classic')content=mine?`<div class="waiting">✅ Antwoord opgeslagen: ${html(r.my_answer)}.</div>`:
 `<div class="choice-grid three">${[['left','← Links'],['middle','↔ Midden'],['right','Rechts →']].map(([v,l])=>`<button class="big-choice" data-act="v2_answer" data-value="${v}">${l}</button>`).join('')}</div>`;
 else if(cid==='quiz'){
  const typ=r.question_type;const expected=(typ==='artist'||typ==='title')?`<div class="autocomplete-wrap"><input id="quiz-text" class="text-input large-text" autocomplete="off" placeholder="Typ je antwoord..."/><div id="suggestions" class="suggestions"></div></div>`:
   typ==='boundary'?`<div class="choice-grid">${[['before',`Vóór ${r.boundary}`],['after',`Vanaf ${r.boundary}`]].map(([v,l])=>`<button class="big-choice" data-act="v2_answer" data-value="${v}">${l}</button>`).join('')}</div>`:
  `<input id="quiz-year" class="text-input large-text" type="number" min="1900" max="2100" placeholder="Bijvoorbeeld: 1994"/>`;
  content=mine?`<div class="waiting">✅ Antwoord opgeslagen.</div>`:`<h2>${html(quizPrompt(r))}</h2>${expected}${typ==='artist'||typ==='title'||typ.startsWith('year')?button('send_quiz','✓ Antwoord insturen','gold'):''}`;
 }
 else if(cid==='quiplash'){
  if(g.phase==='vote')content=r.my_vote?`<div class="waiting">✅ Stem opgeslagen!</div>`:
    (r.options||[]).filter(o=>!o.mine).length?`<h2>Op welk antwoord stem jij?</h2><div class="quip-options phone-options">${r.options.filter(o=>!o.mine).map(o=>`<button class="quip-item" data-act="v2_vote" data-value="${o.id}">${html(o.text)}</button>`).join('')}</div>`:
    '<div class="waiting">Geen andere antwoorden om op te stemmen. De spelleider kan verdergaan.</div>';
  else content=mine?'<div class="waiting">✅ Je grappige antwoord is bewaard.</div>':`<h2>${html(r.prompt)}</h2><textarea id="quippy" class="text-input" rows="3" maxlength="240" placeholder="Jouw grappigste antwoord…"></textarea>${button('send_quip','💬 Verstuur antwoord','gold')}`;
 }
 else if(cid==='three'){
   if(r.investigator===state.me)content=r.guess?`<div class="waiting">✅ Je verdenking is vastgelegd.</div>`:`<p>Stel maximaal tien vragen aan de overige drie spelers. Kies daarna van wie het verhaal is.</p><div class="choice-grid">${state.players.filter(p=>p.id!==state.me).map(p=>`<button class="big-choice" data-act="v2_guess_owner" data-value="${p.id}">${name(p.id)}</button>`).join('')}</div>`;
   else content='<div class="waiting">🕵️ Jij bent verdachte. Antwoord op de vragen, maar verraad je geheim niet!</div>';
 }
 else if(cid==='dice')content=mine?'<div class="waiting">✅ Jouw worp is ingevoerd.</div>':`<h2>Vul de vijf eindwaarden in</h2><div class="five-dice">${Array.from({length:5},(_,i)=>`<select class="die-entry text-input" aria-label="Dobbelsteen ${i+1}">${[1,2,3,4,5,6].map(v=>`<option>${v}</option>`).join('')}</select>`).join('')}</div>${button('send_dice','🎲 Sla mijn worp op','gold')}`;
 else if(cid==='cards'){
   if(!r.alive.includes(state.me))content='<div class="waiting">🃏 Je ligt uit deze deal. Kijk mee met de overgebleven spelers.</div>';
   else if(mine)content='<div class="waiting">✅ Voorspelling vastgelegd.</div>';
   else {const choices=[[['red','♥ / ♦ Rood'],['black','♠ / ♣ Zwart']], [['higher','↑ Hoger'],['lower','↓ Lager']], [['inside','↔ Binnen'],['outside','← → Buiten']], [['H','♥ Harten'],['D','♦ Ruiten'],['C','♣ Klaveren'],['S','♠ Schoppen']]][r.stage];
    content=`<h2>${html(stageHint(r.stage))}</h2><div class="choice-grid">${choices.map(([v,label])=>`<button class="big-choice" data-act="v2_answer" data-value="${v}">${label}</button>`).join('')}</div>`;}
 }
 else if(cid==='taboo'){
   if(r.performer===state.me)content=`<h2>Jij omschrijft!</h2><div class="secret-word">${html(r.word||'')}</div><p>Verboden woorden:</p><div class="banned-words">${(r.banned||[]).map(w=>pill(html(w))).join('')}</div>${r.deadline?'<div class="waiting">De timer loopt. Succes!</div>':button('v2_start_timer','⏱ Start de timer','gold')}`;
   else content=`<h2>Raad het woord</h2><p>Typ meerdere pogingen. Goed gespeld hoeft niet perfect te zijn.</p><div class="timer-small" data-countdown="${r.deadline||''}">${r.deadline?'01:00':'Wacht tot de omschrijver start…'}</div>${r.deadline?`<input id="guess" class="text-input large-text" placeholder="Jouw gok…"/>${button('send_guess','✓ Verstuur gok','gold')}<p class="small subtle">${(r.my_attempts||[]).length} pogingen verstuurd.</p>`:''}`;
 }
 return `<div class="stage-card phone-stage">${topGame(g)}<h1>${cat(cid).name}</h1>${content}</div>`;
}
function gameScreen(){const g=game();if(!g)return `<div class="stage-card">Spel wordt gestart…</div>`;
 if(isPhone)return phoneGame(g);
 if(g.phase==='choose')return chooseScreen(g);
 if(g.phase==='review')return reviewScreen(g);
 return `<div class="stage-card game-stage ${g.category}">${topGame(g)}${visibleQuestion(g)}
 ${g.phase==='reveal'?revealPanel(g):`<div class="submit-count">${answersCount(g)}</div>`}
 ${currentScoreboard(g)}${hostRoundControls(g)}</div>`;
}
function reviewScreen(g){const scores=Object.entries(g.scores).sort((a,b)=>b[1]-a[1]),top=scores[0]?.[1]||0,winners=scores.filter(x=>x[1]===top).map(x=>x[0]);
 const revisions=isHost?(g.rounds||[]).map((r,i)=>{
   if(!r.grades||!['classic','quiz','taboo'].includes(g.category))return '';
   return `<details class="review-round"><summary>Vraag ${i+1}: ${g.category==='quiz'?html(r.song?.title||''):g.category==='taboo'?html(r.word||''):html(r.song?.title||'')}</summary>
   ${Object.entries(r.grades).map(([pid,grade])=>`<div class="review-row"><span><strong>${name(pid)}:</strong> ${html(grade.guess||grade.all_attempts?.join(', ')||'—')}</span><b class="${grade.accepted?'ok':'no'}">${grade.accepted?'Goed':'Fout'}</b>${button('v2_override',grade.accepted?'↩ Afkeuren':'✓ Goedkeuren',grade.accepted?'soft-btn':'alt',`data-round="${i}" data-player="${pid}" data-accepted="${grade.accepted?'false':'true'}"`)}</div>`).join('')}</details>`;
 }).join(''):'';
 return `<div class="stage-card review"><p class="eyebrow">🏆 Einduitslag · ${html(cat(g.category).name)}</p><h1>${winners.length>1?'Meerdere winnaars!':'De winnaar is bekend!'}</h1><div class="winners">${winners.map(id=>`<div class="winner"><span>🏆</span><strong>${name(id)}</strong><small>${top} punten</small></div>`).join('')}</div>
 <div class="score-table">${scores.map(([pid,n])=>`<div class="score-line"><span>${name(pid)}</span><b>${n} punten</b></div>`).join('')}</div>
 ${isHost?`<div class="host-review"><h2>Antwoorden controleren</h2><p class="subtle">Fout gerekende antwoorden kun je alsnog goedkeuren. Ook een correctie ongedaan maken kan vóór de cadeau-uitdeling.</p>${revisions||'<p>Geen handmatige tekstbeoordeling nodig.</p>'}${button('v2_confirm','✓ Uitslag bevestigen · cadeaus','gold')}</div>`:'<p class="subtle">De spelleider controleert de antwoorden voordat de cadeaus worden uitgedeeld.</p>'}</div>`;
}
function giftScreen(){const sh=state.show,g=sh.gift,need=g?.requirement;if(!g||!need)return `<div class="stage-card">Cadeaus worden klaargemaakt…</div>`;
 const self=need.kind==='self';return `<div class="stage-card gift-stage"><p class="eyebrow">🎁 Tijd om uit te pakken</p><h1>${g.winners.length>1?'De winnaars pakken uit!':'Hoera, een winnaar!'}</h1><div class="prize-icons"><span>🎁</span><span>🎁</span></div>
 <div class="winner-display">${name(need.winner)} kiest cadeau ${g.choice_index+1} van 2</div>
 <h2>${self?'Eén cadeau voor jezelf':need.kind==='other'?'Kies een cadeau voor een ander':'Laatste beschikbare cadeaus'}</h2>
 ${self?`<p>Voor ${name(need.winner)}.</p>`:`<p>Kies iemand van wie nog cadeaus in de zak zitten. De eerlijkste ontvangers staan hieronder.</p>`}
 <div class="choice-grid">${need.eligible.map(pid=>isHost?`<button class="gift-choice" data-act="v2_give" data-value="${pid}">🎁 ${name(pid)}<small>${pl(pid)?.received}/${pl(pid)?.target} ontvangen</small></button>`:`<div class="gift-choice">🎁 ${name(pid)}<small>${pl(pid)?.received}/${pl(pid)?.target} ontvangen</small></div>`).join('')}</div>
 <div class="prize-footer">${g.awarded.length} cadeau${g.awarded.length===1?'':'s'} deze minigame uitgedeeld · ${sh.remaining_gifts} cadeaus over</div>
 ${isHost?button('v2_undo_gift','↩ Laatste cadeau terugdraaien','soft-btn'):''}</div>`;}
const alarmSvg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 18v-6a5 5 0 0 1 10 0v6"/><path d="M5 21h14"/><path d="M12 2v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="M2 12h2"/><path d="m19.07 4.93-1.41 1.41"/><path d="M20 12h2"/><path d="M4 18h16"/></svg>';
function groceryScreen(){const gr=state.show.grocery,mode=state.show.mode;
 if(mode==='grocery_alarm')return `<div class="alarm-screen" role="alert">
  <span class="alarm-beacon alarm-beacon-left" aria-hidden="true">${alarmSvg}</span>
  <span class="alarm-beacon alarm-beacon-right" aria-hidden="true">${alarmSvg}</span>
  <div class="alarm-copy"><p class="eyebrow">ONVERWACHTE ONDERBREKING</p>
  <h1>ALARM!</h1>
  <h2>${gr.phase==='alarm_intro'?'ONTHOUD DE BOODSCHAPPEN!':'WAT STOND ER OP DE LIJST?'}</h2>
  <p>De spelshow wordt even onderbroken…</p>
  ${isHost?button('v2_grocery_show','▶ Start de verrassing','alarm-btn'):''}</div></div>`;
 if(mode==='grocery_study')return `<div class="stage-card groceries"><p class="eyebrow">🛒 Onthoud de boodschappen</p><h1>20 boodschappen · 60 seconden</h1>
 ${isPhone?'<div class="waiting">👀 Kijk naar de televisie en probeer alle boodschappen te onthouden.</div>':`<div class="grocery-list">${(gr.items||[]).map((x,i)=>`<div><span>${i+1}.</span>${html(x)}</div>`).join('')}</div>`}
 <div class="timer-hero"><span data-countdown="${gr.deadline}">01:00</span></div>${isHost?button('v2_grocery_close','Verder naar het rad →','alt','data-after-timer="true"'):''}</div>`;
 if(mode==='grocery_recall')return `<div class="stage-card groceries"><p class="eyebrow">🛒 Het boodschappenspel</p><h1>Wat stond er op de lijst?</h1><p>Typ alle boodschappen die je nog weet. Eén punt per correct, uniek product.</p><div class="timer-hero"><span data-countdown="${gr.deadline}">03:00</span></div>
 ${isPhone?`<textarea id="groceries-answer" class="text-input" rows="9" placeholder="Eén product per regel">${html((gr.my_response||[]).join('\n'))}</textarea>${button('send_groceries','📥 Bewaar mijn lijst','gold')}<p class="subtle">Je mag je lijst aanpassen tot de tijd voorbij is.</p>`:`<div class="waiting">${gr.responses_count} van 4 boodschappenlijstjes ingediend.</div>`}
 ${isHost?button('v2_grocery_close','✅ Naar de uitslag','gold'):''}</div>`;
 if(mode==='grocery_review'){
  const review=gr.review||{};const rows=Object.entries(review).sort((a,b)=>b[1].score-a[1].score);
  const best=rows[0]?.[1]?.score||0;
  return `<div class="stage-card review"><p class="eyebrow">🛒 De boodschappen zijn geteld</p><h1>Wie onthield de meeste?</h1><div class="score-table">${rows.map(([pid,v])=>`<div class="score-line"><span>${name(pid)}</span><b>${v.score} punten ${v.score===best?'🏆':''}</b></div>`).join('')}</div>
 ${!isPhone?`<div class="grocery-list compact">${(gr.items||[]).map((x,i)=>`<div><span>${i+1}.</span>${html(x)}</div>`).join('')}</div>`:''}
 ${isHost?`<div class="host-review"><h2>Controleer de antwoorden</h2>${rows.map(([pid,v])=>`<h3>${name(pid)}</h3>${v.answers.map(a=>`<div class="review-row"><span>${html(a.text)}</span><b class="${a.accepted?'ok':'no'}">${a.accepted?'Goed':'Fout'}</b>${button('v2_grocery_override',a.accepted?'↩ Afkeuren':'✓ Goedkeuren',a.accepted?'soft-btn':'alt',`data-player="${pid}" data-guess="${encodeURIComponent(a.text)}" data-accepted="${a.accepted?'false':'true'}"`)}</div>`).join('')}`).join('')}${button('v2_grocery_confirm','✓ Uitslag bevestigen · cadeaus','gold')}</div>`:''}</div>`;
 }
 return '<div class="stage-card"><h1>Het boodschappenspel</h1></div>';
}
function finished(){return `<div class="stage-card final"><p class="eyebrow">✨ De cadeauzak is leeg</p><div class="final-icon">🎁🎉🎄</div><h1>Fijne pakjesavond!</h1><p>${state.show.gifts_given} cadeaus uitgedeeld, ${state.show.regular_completed} reguliere minigames gespeeld.</p>
 <div class="score-table">${state.players.map(p=>`<div class="score-line"><span>${html(p.name)}</span><b>${p.received} cadeaus · ${p.wins} gewonnen</b></div>`).join('')}</div>${isHost?button('v2_reset','↺ Een nieuwe spelavond','alt'):''}</div>`;}
function unauthorized(){return `<div class="stage-card"><h1>🔒 Spelleiderlink ontbreekt</h1><p>De hostpagina is geopend zonder de geldige toegangssleutel.</p><p>Open op de laptop de volledige hostlink in het venster van start.bat, of gebruik <a href="http://127.0.0.1:${location.port||'8765'}/host">de lokale hostlink</a>.</p></div>`;}
function viewScreen(){if(page==='home')return home();if(!state)return '<div class="loading">Verbinding maken…</div>';
 if(isHost&&!state.host_authorized)return shell(unauthorized());
 if(isPhone&&!state.me)return shell(joinScreen(),false);
 const mode=state.show?.mode||'setup';let content='';
 if(mode==='setup')content=setup();
 else if(mode==='wheel'||mode==='spinning')content=wheel();
 else if(mode==='game')content=gameScreen();
 else if(mode==='gift')content=giftScreen();
 else if(mode.startsWith('grocery_'))content=groceryScreen();
 else content=finished();
 return shell(content,!isPhone && mode!=='grocery_alarm' && mode!=='grocery_study');}
function renderHash(){const s=state,sh=s?.show,g=sh?.game,r=g?.current;
 if(!sh)return 'none';
 if(isPhone)return JSON.stringify([sh.mode,sh.spin_player,sh.enabled_games,sh.disabled_games,sh.gifts_given,g?.category,g?.phase,g?.index,r?.stage,r?.my_answer,r?.my_vote,r?.my_attempts?.length,r?.deadline,r?.chooser,r?.investigator,r?.guess,sh.grocery?.phase,sh.grocery?.my_response?.length,s?.me]);
 return JSON.stringify([sh.mode,sh.spin_player,sh.enabled_games,sh.disabled_games,sh.gifts_given,sh.bag,sh.regular_completed,g?.category,g?.phase,g?.index,g?.scores,r?.stage,r?.submitted,r?.voted,r?.deadline,r?.revealed,r?.all_answers,r?.all_attempts,sh.grocery?.phase,sh.grocery?.responses_count,sh.gift?.winner_index,sh.gift?.choice_index,s?.players.map(p=>p.received),sh.hitster_count,sh.has_story]);
}
function setCountdowns(){document.querySelectorAll('[data-countdown]').forEach(el=>{
 const deadline=Number(el.dataset.countdown);if(!deadline)return;
 const seconds=Math.max(0,Math.ceil(deadline-Date.now()/1000));
 el.textContent=`${Math.floor(seconds/60).toString().padStart(2,'0')}:${(seconds%60).toString().padStart(2,'0')}`;
 if(!seconds)el.classList.add('expired');
 });document.querySelectorAll('[data-after-timer]').forEach(b=>{
 const deadline=state?.show?.grocery?.deadline;
 if(deadline)b.disabled=Date.now()/1000<deadline;
 });}
function animateClassic(){const el=$('[data-classic="reveal"]');if(!el)return;
 const place=el.dataset.place;
 const cols=[...el.querySelectorAll('.timeline-card')];
 const map=place==='left'?[1,2,0]:place==='right'?[0,1,2]:[0,2,1];
 cols.forEach((c,i)=>c.style.setProperty('--slot',i===0?0:i===1?2:1));
 const flip=el.querySelector('.card-flip');flip?.classList.remove('revealed');
 requestAnimationFrame(()=>requestAnimationFrame(()=>{cols.forEach((c,i)=>c.style.setProperty('--slot',map[i]));
  setTimeout(()=>flip?.classList.add('revealed'),380);}));
}
function afterRender(){setCountdowns();if(state?.show?.mode==='game'&&game()?.phase==='reveal'&&game()?.category==='classic'){
 const marker=`${game().category}-${game().index}-${game().phase}`;
 if(lastReveal!==marker){lastReveal=marker;animateClassic();}}
 if(isPhone && game()?.category==='quiz' && game()?.phase==='answer')initSuggestions();
}
function normalizeSearch(s){return String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/\b(and|en)\b|&/g,' ').replace(/^the\s+/,'').replace(/[^a-z0-9 ]/g,' ').replace(/\s+/g,' ').trim();}
function initSuggestions(){const input=$('#quiz-text'),box=$('#suggestions');if(!input||!box)return;
 const source=state.show.suggestions?.[round().question_type]||[];
 input.oninput=()=>{const q=normalizeSearch(input.value);if(q.length<3){box.innerHTML='';return;}
 const matching=source.filter(x=>normalizeSearch(x).includes(q)).slice(0,5);
 box.innerHTML=matching.map(x=>`<button type="button" class="suggestion" data-suggest="${html(x)}">${html(x)}</button>`).join('');};}
let refreshing=false;
async function refresh(force=false){if(refreshing)return;refreshing=true;
 try{const params=new URLSearchParams();if(isHost)params.set('key',key);if(isPhone&&token)params.set('token',token);
  const response=await fetch('/api/state?'+params,{cache:'no-store'});
  if(!response.ok)throw Error('Server niet bereikbaar');
  const prev=state?.show?.mode;state=await response.json();
  const h=renderHash();if(force||h!==lastRender){lastRender=h;$('#app').innerHTML=viewScreen();afterRender();}
  if(page==='screen'){if(state.show?.mode==='grocery_alarm')sound();else stopAlarmSound();}
  if(state.show?.mode==='spinning'&&isHost && !spinHandle){spinHandle=setTimeout(async()=>{spinHandle=null;try{await host('v2_open_game');await refresh(true);}catch(e){toast(e.message)}},6500);}
  if(state.show?.mode!=='spinning'&&spinHandle){clearTimeout(spinHandle);spinHandle=null;}
  setCountdowns();
 }catch(e){
  // A previously loaded state could throw during rendering. Always show why.
  console.error('Sintspel opstart- of weergavefout:',e);
  lastRender='';
  const reason=String(e?.message||e||'Onbekende fout');
  const serverError=state?.error?String(state.error):'';
  const currentMode=state?.show?.mode||'geen geldige spelstand ontvangen';
  const fallback='<main class="entry-screen"><div class="entry-panel boot-error">'
   +'<h1>De spelshow kan niet worden weergegeven</h1>'
   +'<p>De spelgegevens worden niet verwijderd. Herladen of de server opnieuw starten is veilig.</p>'
   +'<p><strong>Oorzaak:</strong> <code>'+html(serverError||reason)+'</code></p>'
   +'<p><strong>Status:</strong> <code>'+html(currentMode)+'</code></p>'
   +'<button type="button" class="btn" id="retry-show">↻ Opnieuw proberen</button>'
   +(isHost?'<p class="fine">De noodbediening rechtsonder blijft apart beschikbaar zodra de spelshow is begonnen.</p>':'')
   +'</div></main>';
  const el=$('#app');if(el&&el.innerHTML!==fallback)el.innerHTML=fallback;
 }
 finally{refreshing=false;}}
function gatherValue(action,b){const r=round();
 if(action==='v2_answer')return b?.dataset.value;
 if(action==='send_quiz')return r.question_type==='artist'||r.question_type==='title'?$('#quiz-text')?.value:$('#quiz-year')?.value;
 if(action==='send_quip')return $('#quippy')?.value;
 if(action==='send_guess')return $('#guess')?.value;
 if(action==='send_dice')return [...document.querySelectorAll('.die-entry')].map(x=>Number(x.value));
 return b?.dataset.value;}
async function act(b){if(busy)return;const action=b.dataset.act;busy=true;b.disabled=true;
 try{
  if(action==='join'){
   const code=$('#join-code')?.value.trim();
   const v=await request('/api/claim',{room:code,player:b.dataset.player,token});
   token=v.token;localStorage.setItem(tokenKey,token);localStorage.setItem('sintspel-room',code);
  }else if(action==='v2_reset'){
   if(prompt('Dit wist de spelstand, maar bewaart de muziekbibliotheek en weetjes. Typ RESET:')!=='RESET')return;
   await host(action,{confirmation:'RESET'});
  }else if(action==='v2_disable_game'){
    const category=game()?.category||state?.show?.gift?.category||$('#disable-select')?.value;
    if(!category)throw Error('Geen spel geselecteerd.');
    if(!confirm(`Spel ${cat(category).name} voor de rest van deze spelavond uitschakelen?`))return;
    await host(action,{category});
  }else if(action==='v2_enable_game'){
    await host(action,{category:$('#enable-select')?.value});
  }else if(action==='v2_spin'){
    if(isPhone)await send(action);else await host(action);
  }else if(action==='v2_choose'){
   const value=b.dataset.value;
   if(isPhone)await send(action,{value});else await host(action,{value});
  }else if(['v2_start_timer'].includes(action)){
   if(isPhone)await send(action);else await host(action);
  }else if(['v2_answer','send_quiz','send_quip','send_dice'].includes(action)){
   const value=gatherValue(action,b);
   await send('v2_answer',{value});
  }else if(action==='v2_vote'||action==='v2_guess_owner'){
   await send(action,{value:b.dataset.value});
  }else if(action==='send_guess'){
   const value=gatherValue(action,b);if(!value?.trim())throw Error('Vul eerst een gok in.');
   await send('v2_guess',{value});
  }else if(action==='send_groceries'){
   await send('v2_grocery_answer',{value:$('#groceries-answer')?.value||''});
  }else if(action==='save_story'){
   await send('v2_story',{value:$('#my-story')?.value||''});
  }else if(action==='host_story'){
   await host('v2_story',{player:$('#story-player')?.value,story:$('#host-story')?.value});
  }else if(action==='v2_start'){
   const form=$('#setup-form');
   if(form){const fd=new FormData(form);await host('v2_configure',{players:Array.from({length:4},(_,i)=>({name:fd.get('name'+i),target:Number(fd.get('target'+i))}))});}
   await host('v2_start');
  }else if(action==='v2_direct'){
   await host(action,{category:$('#quick-game')?.value});
  }else if(action==='v2_override'){
   await host(action,{round:Number(b.dataset.round),player:b.dataset.player,accepted:b.dataset.accepted==='true',remember:true});
  }else if(action==='v2_grocery_override'){
   await host(action,{player:b.dataset.player,guess:decodeURIComponent(b.dataset.guess),accepted:b.dataset.accepted==='true'});
  }else if(action==='v2_give'){
   if(!confirm(`Een cadeau voor ${name(b.dataset.value).replace(/&[^;]+;/g,'')} uit de zak pakken?`))return;
   await host(action,{recipient:b.dataset.value});
  }else if(action==='v2_cancel'){
   if(!confirm('Minigame annuleren zonder cadeau-uitdeling?'))return;
   await host(action);
  }else if(action==='v2_grocery_close'){
   await host(action);
  }else if(action.startsWith('v2_')){
   await host(action);
  }
  await refresh(true);
 }catch(e){toast(e.message)}finally{busy=false;if(b.isConnected)b.disabled=false;}}
document.addEventListener('click',e=>{
 const suggest=e.target.closest('[data-suggest]');if(suggest){const i=$('#quiz-text');if(i){i.value=suggest.dataset.suggest;$('#suggestions').innerHTML='';i.focus()}return;}
 const b=e.target.closest('button[data-act]');if(b)act(b);
});
document.addEventListener('submit',async e=>{
 if(!e.target.matches('#setup-form,#csv-import'))return;
 e.preventDefault();if(busy)return;busy=true;
 try{if(e.target.id==='setup-form'){
  const fd=new FormData(e.target);
  await host('v2_configure',{players:Array.from({length:4},(_,i)=>({name:fd.get('name'+i),target:Number(fd.get('target'+i))}))});
 }else{
  const file=$('#csv-file').files[0];if(!file)throw Error('Kies eerst een CSV-bestand.');
  if(file.size>300000)throw Error('CSV mag maximaal 300 KB zijn.');
  const res=await host('import_hitster',{csv:await file.text()});
  importNotice=`${res.added} kaarten toegevoegd, ${res.duplicates} dubbel, ${res.skipped} overgeslagen.`;
 }
 await refresh(true);}catch(err){toast(err.message)}finally{busy=false;}
});
document.addEventListener('click',e=>{
 if(e.target.closest('#retry-show')){refresh(true);return;}
 if(e.target.closest('[data-enable-sound]')){audioEnabled=!audioEnabled;const x=e.target.closest('button');if(audioEnabled){const A=window.AudioContext||window.webkitAudioContext;if(A){audioContext ||=new A();audioContext.resume().catch(()=>{});}if(state?.show?.mode==='grocery_alarm')sound();}else stopAlarmSound();x.textContent=audioEnabled?'🔊 Geluid aan':'🔈 Geluid aanzetten';x.setAttribute('aria-pressed',String(audioEnabled));}
});
$('#app').innerHTML=page==='home'?home():'<div class="loading">🎁 De spelshow wordt klaargezet…</div>';
refresh(true);setInterval(()=>refresh(),950);setInterval(setCountdowns,180);