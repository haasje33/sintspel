/* De Grote Sinterklaas Spellenavond — native browser client, no dependencies. */
'use strict';
const $ = selector => document.querySelector(selector);
const path = location.pathname;
const view = path === '/host' ? 'host' : path === '/screen' ? 'screen' : path === '/play' ? 'phone' : 'home';
const adminKey = new URLSearchParams(location.search).get('key') || '';
let state = null, lastKey = '', music = null, lastTrack = '', spinningStamp = '', pollRunning = false;
let savedToken = localStorage.getItem('sint-party-token') || '';
let busy = false, messageTimer = 0, nextTick = 0, lastSidebarVersion = -1, importSummary = '';

function esc(s) { return String(s ?? '').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function player(id) { return state?.players.find(p=>p.id===id); }
function pname(id) { return esc(player(id)?.name || 'Onbekend'); }
function toast(message, error=false) {
  const t=$('#toast');t.textContent=message;t.style.background=error?'#ffe0d7':'#f1e8d7';
  t.classList.add('on');clearTimeout(messageTimer);messageTimer=setTimeout(()=>t.classList.remove('on'),3300);
}
function roundInfo() { return state.game?`Opdracht ${state.game.round} van ${state.game.total}`:''; }
function formatPts(n) { return n===1?'1 punt':`${n} punten`; }
function statusBadge(phase) {return ({answer:'Antwoorden verzamelen',vote:'Stemmen!',reveal:'Uitslag',manual:'Fysiek spel'})[phase]||phase;}
function roundCounts(g) {
  if(!g)return [0,4,'antwoorden'];
  if(g.kind==='physical')return [0,0,''];
  if(g.kind==='creative'&&g.phase==='vote')return [g.voted.length,4,'stemmen'];
  if(g.kind==='who')return [g.voted.length,4,'stemmen'];
  if(g.kind==='performance')return [g.submitted.length,3,'gokkers'];
  return [g.submitted.length,4,'antwoorden'];
}
function namesRow() { return state.players.map((p,i)=>`<span>${['🌟','🎁','🎄','🔔'][i]} ${esc(p.name)}: ${p.received} 🎁</span>`).join(''); }
function header() {
 return `<div class="topline"><div class="brand"><div class="brand-icon">🎁</div><div>DE GROTE<br>SINTERKLAAS SPELLENAVOND</div></div>
 <div class="stats"><span class="pill">${view==='host'?'🎛️ Spelleider':view==='screen'?'📺 TV-scherm':'📱 Speler'}</span><span class="code-pill">CODE ${esc(state.room)}</span></div></div>`;
}
function joinHelp(short=false) {
 const url=esc(state.join_url);
 return `<div class="join-info"><img class="qr" src="/qr.png?url=${encodeURIComponent(state.join_url)}" alt="QR-code: ga naar ${url}" onerror="this.style.display='none'"/>
 <div><div class="kicker">${short?'Doe mee':'Vier telefoons, één spel'}</div>
 <p class="address">${url}</p><p class="muted small">Zelfde wifi · Scan de QR-code of typ het adres over · code <strong>${esc(state.room)}</strong></p></div></div>`;
}
function scoreboard(full=true) {
 let rows=state.players.map((p,i)=>`<div class="score-row ${state.eligible.includes(p.id)?'eligible':''}">
 <div class="avatar">${['🎄','⭐','🎁','🔔'][i]}</div>
 <div><div class="score-name">${esc(p.name)}${p.joined?'<span class="ready">● online</span>':''}</div>
 <div class="score-info">${p.wins}× gewonnen · ${p.target?`${p.received} van ${p.target}`:'Geen limiet ingesteld'}${view==='host'&&p.joined?' · <button class="linkbutton" data-action="release_seat" data-player="'+p.id+'">Ontkoppel telefoon</button>':''}</div></div>
 <div class="score-right">${p.received} 🎁<div class="score-mini">cadeautjes</div></div></div>`).join('');
 const last=state.last_games.slice(-4).reverse().map(item=>`<div class="small" style="padding:7px 0">${esc(state.categories.find(c=>c.id===item.category)?.icon||'🎲')} ${esc(state.categories.find(c=>c.id===item.category)?.name||item.category)} <span class="muted">· ${item.winner?pname(item.winner):'gelijkspel'}</span></div>`).join('');
 return `<aside class="panel sidebar"><h3>🎁 Pakjesstand</h3>${rows}<div class="divider"></div>
 <div class="small muted">Tot nu toe <b style="color:var(--gold)">${state.gifts_given}</b> cadeautjes uitgedeeld. Iedere beurt krijgt iemand met de laagste cadeaustand een cadeau.</div>
 ${last?`<div class="divider"></div><h3>🏆 Laatste winnaars</h3>${last}`:''}
 ${view==='host'?`<div class="divider"></div><p class="small muted">TV-weergave: <a href="${esc(state.screen_url)}" target="_blank" rel="noopener">${esc(state.screen_url)}</a></p>`:''}</aside>`;
}
function panel(content) {return `<div class="panel main-panel"><div class="panel-pad">${content}</div></div>`;}
function renderSetup() {
 const rows=state.players.map((p,i)=>`<div class="input-grid"><input class="input" id="name-${i}" maxlength="28" value="${esc(p.name)}" aria-label="Naam speler ${i+1}"/>
 <input class="input" id="target-${i}" type="number" min="0" max="99" value="${p.target}" aria-label="Cadeaus voor speler ${i+1}"/></div>`).join('');
 const files=state.audio_files?.map(m=>`<div class="saved"><span class="small">🎧 ${esc(m.artist)} – ${esc(m.title)} (${m.year})</span>
 <button class="btn ghost tinybtn" data-action="delete_audio" data-id="${m.id}">Wissen</button></div>`).join('')||'';

 const cards=(state.hitster_cards||[]).slice().reverse();
 const cardRows=cards.slice(0,75).map(c=>`<div class="hitster-row"><div><strong>${esc(c.artist)} — ${esc(c.title)}</strong><div class="small muted">${c.year} · ${esc(c.url.length>85?c.url.slice(0,85)+'…':c.url)}</div></div><div class="hitster-actions"><a class="btn secondary tinybtn" target="_blank" rel="noopener noreferrer" href="/hitster/test?id=${encodeURIComponent(c.id)}&key=${encodeURIComponent(adminKey)}">📺 Test QR</a><button class="btn ghost tinybtn" data-action="delete_hitster" data-id="${c.id}">Wissen</button></div></div>`).join('');
 return panel(`<div class="kicker">Welkom thuis, pakjesavond begint zo</div><h1>Vier spelers.<br><span style="color:var(--gold)">Eén zak vol verrassingen.</span></h1>
 <p class="muted" style="font-size:1.13rem;margin-top:17px">Stel de vier namen in. Een rad kiest steeds een minigame; de winnaar mag een cadeau verdelen.</p>
 <section><h3>👥 Deelnemers en cadeaus</h3><p class="small muted">Vul het aantal cadeaus per persoon in als jullie dat weten. Laat alle aantallen op 0 als je alleen wilt bijhouden wie het minst heeft.</p>
 <div class="form-grid"><div class="input-grid small muted"><strong>Naam</strong><strong>Aantal cadeaus</strong></div>${rows}</div>
 <div class="actions"><button class="btn" data-action="configure">💾 Namen opslaan</button><button class="btn mint" data-action="start">🎉 Start de spelshow</button></div></section>
 <section class="callout gold"><h3>📱 Zo spelen jullie samen</h3>${joinHelp()}
 <p class="small muted" style="margin-top:13px">Gebruik de hostpagina om de rondes te begeleiden. Open voor de TV eventueel het aparte TV-scherm. Deze pagina toont géén geheime opdrachten.</p></section>
 <section><h3>🎵 Hitster QR-bibliotheek</h3>
 <p class="small muted">${state.hitster_count||0} kaarten opgeslagen. Importeer CSV met <strong>URL, artiest, titel, jaar</strong> (één kaart per regel). Sintspel bewaart de ongewijzigde QR-inhoud en maakt de QR-code pas bij het tonen. Geen foto's en geen Spotify-koppeling nodig.</p>
 <form id="hitster-import" class="upload-box"><label class="field-label" for="hitster-csv">CSV-bestand uit Apple Opdrachten</label>
 <input class="input" type="file" name="csv" id="hitster-csv" accept=".csv,.txt,text/csv,text/plain" required>
 <div class="actions"><button class="btn mint" type="submit">📥 Importeer Hitster-kaarten</button></div></form>
 ${importSummary?`<div class="callout" role="status">${esc(importSummary)}</div>`:''}
 ${cardRows||'<p class="small muted" style="margin-top:14px">Nog geen Hitster-kaarten geïmporteerd.</p>'}
 ${cards.length>75?`<p class="small muted">Eerste 75 van ${cards.length} kaarten zichtbaar.</p>`:''}
 <p class="small muted" style="margin-top:16px">Klik na import op <strong>Test QR</strong> bij een kaart, open die weergave op de TV en scan met de officiële Hitster-app. Controleer of het juiste nummer wordt geopend. De testpagina toont geen titel of artiest.</p></section>
 <section><h3>🎵 Optioneel: eigen muziekfragmenten</h3>
 <p class="small muted">${state.music_count} tracks toegevoegd. Bij Hitster gebruik je standaard de officiële app en jullie fysieke kaarten. Voeg eventueel eigen audiobestanden toe om de muziekronde automatisch te laten afspelen, zonder titel/jaar op TV te tonen.</p>
 <form id="upload" class="upload-box"><div class="form-row"><input class="input" name="artist" maxlength="100" placeholder="Artiest" required/>
 <input class="input" name="title" maxlength="100" placeholder="Titel" required/></div>
 <div class="form-row"><input class="input" type="number" name="year" min="1800" max="2100" placeholder="Releasejaar" required/>
 <input class="input" type="file" name="audio" accept=".mp3,.m4a,.ogg,.wav,audio/*" required/></div>
 <button class="btn secondary" type="submit">+ Audio toevoegen</button></form>${files}</section>`);
}
function wheelHTML() {
 const cats=state.categories;const size=360/cats.length;
 const gradient=cats.map((c,i)=>`${c.color} ${(i*size).toFixed(3)}deg ${((i+1)*size).toFixed(3)}deg`).join(',');
 const labels=cats.map((c,i)=>`<div class="wheel-label" style="transform:translate(-50%,-50%) rotate(${(i+.5)*size}deg) translateY(calc(var(--wheel-radius, 162px) * -1)) rotate(${-(i+.5)*size}deg)">${esc(c.icon)}<br>${esc(c.name)}</div>`).join('');
 return `<div class="wheel-wrap"><div class="wheel-stage"><div class="wheel-pointer"></div><div id="spinningWheel" class="wheel" style="background:conic-gradient(${gradient})">${labels}</div><div class="wheel-center">🎁</div></div>
 <div class="wheel-result" id="wheel-title">${state.mode==='spinning'?'Het rad draait…':'Wat wordt het volgende spel?'}</div></div>`;
}
function manualChooser() {
 if(view!=='host'||state.mode!=='wheel')return '';
 const choices=state.categories.map(c=>`<option value="${esc(c.id)}">${esc(c.icon)} ${esc(c.name)}</option>`).join('');
 return `<section class="callout" style="margin-top:24px">
 <h3>🧪 Minigame direct kiezen</h3>
 <p class="small muted">Test bijvoorbeeld Hitster zonder op het rad te wachten. Annuleer de minigame om zonder punten of cadeau terug te keren.</p>
 <div class="form-row" style="margin-top:12px">
 <select class="input" id="quick-category" aria-label="Kies minigame">${choices}</select>
 <button class="btn secondary" data-action="start_selected">▶ Start gekozen minigame</button>
 </div></section>`;
}
function wheelScreen() {
 return panel(`<div class="kicker">${state.gifts_given} cadeaus uitgedeeld</div><h2>${state.mode==='spinning'?'Welk spel wordt het?':'Draai aan het rad!'}</h2>
 ${wheelHTML()}
 ${manualChooser()}
 ${view==='host'?`<div class="actions" style="justify-content:center">${state.mode==='wheel'?`<button class="btn" data-action="spin">🎡 Draai aan het rad!</button>`:
 `<button class="btn" data-action="start_game">✨ Start het gekozen spel</button>`}
 ${state.mode==='wheel'&&state.gifts_given?`<button class="btn ghost" data-action="undo_gift">↩ Laatste cadeau terugdraaien</button>`:''}
 <button class="btn ghost" data-action="finish">Zak leeg · afsluiten</button></div>`:''}
 ${view==='screen'?`<p class="muted" style="text-align:center">De spelleider draait aan het rad.</p>`:''}`);
}
function resultRows(g) {
 const r=g.result;if(!r)return '';
 if(g.kind==='estimate'||g.kind==='music'){
  const rows=state.players.map(p=>{let s=r.scores?.[p.id];return `<div class="result-item"><strong>${esc(p.name)}</strong>
    <span class="answer-col">${s?`${s.guess}${g.kind==='music'?'':' · verschil '+fmtNumber(s.difference)}`:'Geen antwoord'}</span><b>+${s?.points||0}</b></div>`}).join('');
  const correct=g.kind==='music'?`${r.answer}${r.artist?' · '+esc(r.artist):''}${r.song?' – '+esc(r.song):''}`:esc(r.explain||r.answer);
  return `<div class="kicker">Het goede antwoord</div><div class="big-answer">${correct}</div><div class="result-list">${rows}</div>`;
 }
 if(g.kind==='creative'){
   return `<div class="result-list">${state.players.map(p=>`<div class="result-item"><strong>${esc(p.name)}</strong><span class="answer-col">${esc(r.answers[p.id]||'—')}</span><b>${r.votes?.[p.id]||0} ♥</b></div>`).join('')}</div>`;
 }
 if(g.kind==='who'){
   return `<div class="result-list">${state.players.map(p=>`<div class="result-item"><strong>${esc(p.name)}</strong><span class="answer-col">${r.majorities.includes(p.id)?'Meeste stemmen!':''}</span><b>${r.votes[p.id]||0}×</b></div>`).join('')}</div>`;
 }
 if(g.kind==='performance'){
   return `<div class="kicker">Het geheime woord was</div><div class="big-answer">${esc(r.answer)}</div>
   <p style="margin-top:15px">${Object.keys(r.correct||{}).length?Object.keys(r.correct).map(p=>`${pname(p)} had het goed!`).join(' · '):'Niemand had het geraden.'}</p>`;
 }
 return '';
}
function fmtNumber(n) {return Number.isFinite(n)?new Intl.NumberFormat('nl-NL',{maximumFractionDigits:2}).format(n):n;}
function pointBoard(g) {
 return `<div class="stats" style="margin-top:21px">${state.players.map(p=>`<span class="pill">${esc(p.name)} <strong>${g.points[p.id]||0} p</strong></span>`).join('')}</div>`;
}
function gameScreen() {
 const g=state.game;if(!g)return panel('<h2>Ronde wordt voorbereid…</h2>');
 const cat=state.categories.find(c=>c.id===g.category),counts=roundCounts(g);
 let question='';
 if(g.kind==='physical'){
  question=`<div class="kicker">${esc(cat.icon)} Speel met je eigen spelmateriaal</div><h2 style="margin:12px 0">${esc(g.question.title)}</h2>
  <div class="callout"><p style="font-size:clamp(1.1rem,2.2vw,1.5rem)">${esc(g.question.task)}</p></div>
  <div class="callout gold" style="margin-top:14px"><strong>Hoe win je?</strong><p>${esc(g.question.rules)}</p></div>
  ${view==='host'?`<h3 style="margin-top:24px">Wie heeft gewonnen?</h3>${winnerChoices('physical_result','winner')}`:''}`;
 } else if(g.phase==='reveal'){
  question=`${resultRows(g)}${pointBoard(g)}${view==='host'?`<div class="actions"><button class="btn" data-action="next">${g.round===g.total?'🎁 Naar de cadeautjes!':'Volgende opdracht →'}</button></div>`:''}`;
 } else if(g.kind==='performance'){
  const performer=pname(g.performer),verb=g.category==='pictionary'?'tekent':g.category==='uitbeelden'?'beeldt uit':'omschrijft';
  question=`<div class="kicker">👀 Geen spieken op de telefoon van de uitvoerder</div><div class="question">${performer} ${verb} een geheim woord!</div>
  <div class="callout"><strong>${g.category==='pictionary'?'✏️ Teken op papier; geen letters of cijfers.':g.category==='uitbeelden'?'🎭 Geen praten, geluiden of voorwerpen.':'🗣️ Geen verboden woorden of delen van het antwoord gebruiken.'}</strong></div>
  <div class="stats" style="margin-top:17px"><span class="count-chip" id="live-count">${counts[0]} van ${counts[1]} ${counts[2]}</span>
  <span class="timer" id="live-timer">01:25</span></div>
  ${view==='host'?`<div class="actions"><button class="btn" data-action="reveal">👁️ Onthul het woord</button></div>`:''}`;
 } else if(g.kind==='music'){
  question=`<div class="kicker">🎵 Hitster – nummer ${g.round} van ${g.total}</div><div class="question">Raad het jaar waarin dit nummer uitkwam.</div>
  <div class="callout gold"><h3>${g.source==='audio'?'🎧 Eigen audiobestand':g.source==='card'?'📺 Scan de QR-code op het scherm':'📱 Pak een fysieke Hitster-kaart'}</h3>
  <p>${g.source==='audio'?'Het fragment is klaargezet. De titel en artiest blijven geheim tot de onthulling.':g.source==='card'?'Gebruik de officiële Hitster-app om de QR-code vanaf de televisie te scannen.':'Laat één speler een fysieke kaart scannen met de Hitster-app en speel het nummer af via de speaker. Draai de kaart nog niet om.'}</p>
  ${g.source==='card'?`<div class="hitster-playing"><img src="${esc(g.qr_image_url)}" alt="Hitster-code voor het huidige nummer"></div>`:''}
  ${g.source==='audio'?`<div class="actions"><button class="btn mint" data-action="play_audio">▶ Speel muziek</button><button class="btn ghost" data-action="stop_audio">■ Stop</button></div>`:''}</div>
  <p class="muted" style="margin-top:17px">Vul op je telefoon het jaartal in, en eventueel de artiest.</p>
  <div style="margin-top:19px" class="count-chip" id="live-count">${counts[0]} van ${counts[1]} antwoorden binnen</div>
  ${view==='host'?`<div class="callout" style="margin-top:20px"><h3>Antwoord onthullen</h3>${g.source==='hitster'?`<p class="small muted" style="margin:8px 0 14px">Kijk op de achterkant van de Hitster-kaart. Vul het juiste jaar in.</p>
   <div class="form-row"><input class="input" id="correct-year" type="number" min="1800" max="2100" placeholder="Juiste jaartal"/><input class="input" id="correct-artist" placeholder="Artiest (optioneel)"/></div>`:`<p class="small muted">Het antwoord staat al in de muziekbank. Je kunt het nu onthullen.</p>`}
  <div class="actions"><button class="btn" data-action="reveal">✅ Antwoord onthullen</button></div></div>`:''}`;
 } else if(g.kind==='estimate'){
  question=`<div class="kicker">🎯 Schattingsvraag</div><div class="question">${esc(g.question)}</div>
  <p class="muted">Iedereen vult het antwoord in op zijn eigen telefoon. Het dichtstbijzijnde antwoord krijgt 3 punten, de nummer 2 krijgt 1 punt.</p>
  <div style="margin-top:24px" class="count-chip" id="live-count">${counts[0]} van ${counts[1]} antwoorden binnen</div>
  ${view==='host'?`<div class="actions"><button class="btn" data-action="reveal">✅ Onthul het antwoord</button></div>`:''}`;
 } else if(g.kind==='creative'){
  question=`<div class="kicker">${g.category==='levensweg'?'🚗 De levenskeuze':'💬 Originele Party & Co-opdracht'}</div>
  <div class="question">${esc(g.question)}</div>
  <p class="muted">${g.phase==='answer'?'Iedereen schrijft zijn grappigste antwoord op de telefoon. Daarna kiest iedereen anoniem zijn favoriet.':'De antwoorden staan op jullie telefoons. Stem op je favoriet (niet op jezelf)!'}</p>
  <div style="margin-top:24px" class="count-chip" id="live-count">${counts[0]} van ${counts[1]} ${counts[2]} binnen</div>
  ${g.phase==='vote'&&g.options?.length?`<div class="result-list">${g.options.map((o,i)=>`<div class="callout"><strong>${String.fromCharCode(65+i)}.</strong> ${esc(o.text)}</div>`).join('')}</div>`:''}
  ${view==='host'?`<div class="actions"><button class="btn" data-action="${g.phase==='answer'?'open_vote':'reveal'}">${g.phase==='answer'?'🗳️ Start stemmen':'🏆 Toon de uitslag'}</button></div>`:''}`;
 } else if(g.kind==='who'){
  question=`<div class="kicker">👀 Wie van jullie…?</div><div class="question">${esc(g.question)}</div>
  <p class="muted">Iedereen wijst via de telefoon één persoon aan. De meeste stemmen bepalen het populaire antwoord. Wie daarop stemde, verdient 1 punt.</p>
  <div style="margin-top:24px" class="count-chip" id="live-count">${counts[0]} van ${counts[1]} stemmen binnen</div>
  ${view==='host'?`<div class="actions"><button class="btn" data-action="reveal">👀 Onthul de stemmen</button></div>`:''}`;
 }
 return panel(`<div class="round-header"><span class="pill">${esc(cat.icon)} ${esc(cat.name)}</span><span class="pill">${roundInfo()}</span><span class="pill ${g.phase==='reveal'?'good':'warn'}">${statusBadge(g.phase)}</span></div>
 ${view==='host'?'<div class="actions" style="margin-bottom:16px"><button class="btn ghost" data-action="cancel_game">↩ Annuleer minigame (zonder cadeau)</button></div>':''}
 ${question}`);
}
function winnerChoices(action, field) {
 return `<div class="card-grid">${state.players.map(p=>`<button class="choice" data-action="${action}" data-${field}="${p.id}"><span class="choice-name">🎁 ${esc(p.name)}</span><span class="choice-secondary">${p.wins} spelletjes gewonnen</span></button>`).join('')}</div>`;
}
function giftScreen() {
 const gift=state.gift;if(!gift)return panel('<h2>Het cadeau wordt klaargemaakt…</h2>');
 if(!gift.winner) {
  return panel(`<div class="kicker">🏆 Beslissingsronde</div><h1>Gelijkspel!</h1><p style="font-size:1.2rem;margin-top:16px">Laat de gelijkstaande spelers ieder één echte dobbelsteen gooien. De hoogste worp wint. Bij gelijkstand opnieuw.</p>
  ${view==='host'?`<h3 style="margin-top:23px">Wie won het dobbelduel?</h3><div class="card-grid">${gift.tied.map(id=>`<button class="choice" data-action="choose_winner" data-winner="${id}"><span class="choice-name">🎲 ${pname(id)}</span></button>`).join('')}</div>`:
  `<div class="callout" style="margin-top:25px">Gelijk: ${gift.tied.map(pname).join(' · ')}</div>`}`);
 }
 const choices=state.players.filter(p=>state.eligible.includes(p.id));
 return panel(`<div class="kicker">🎁 Tijd voor een cadeautje</div><div class="large-icon" style="margin-top:15px">🏆</div><h1>${pname(gift.winner)} wint!</h1>
 <p style="font-size:1.2rem;margin-top:20px">${pname(gift.winner)} mag kiezen <strong>voor wie</strong> er een cadeautje uit de zak wordt gehaald.</p>
 <div class="callout gold" style="margin-top:22px"><strong>⚖️ Eerlijke verdeling</strong><p>Alleen spelers met de laagste cadeaustand zijn nu aan de beurt. Na vier cadeaus heeft iedereen er één extra.</p></div>
 ${view==='host'?`<h3 style="margin-top:28px">Kies de ontvanger van het cadeau</h3><div class="card-grid">${choices.map(p=>`<button class="choice ${p.id===gift.winner?'featured':''}" data-action="give_gift" data-recipient="${p.id}"><span class="choice-name">🎁 ${esc(p.name)}</span><span class="choice-secondary">Heeft ${p.received} cadeautje${p.received===1?'':'s'} ${p.id===gift.winner?'· winnaar':''}</span></button>`).join('')}</div>`:
 `<div class="card-grid">${choices.map(p=>`<div class="choice ${p.id===gift.winner?'featured':''}"><span class="choice-name">🎁 ${esc(p.name)}</span><span class="choice-secondary">Kan nu een cadeau krijgen</span></div>`).join('')}</div>`}
 <p class="small muted" style="margin-top:17px">Pak het cadeau van de gekozen persoon en pak het samen uit. Daarna draait het rad opnieuw.</p>`);
}
function finishScreen() {
 return panel(`<div class="kicker">✨ De zak is leeg</div><div class="huge" style="margin:20px 0">🎁 🎊 🎄</div><h1>Fijne pakjesavond!</h1>
 <p style="font-size:1.15rem;margin-top:14px">Er zijn <strong>${state.gifts_given}</strong> cadeautjes uitgedeeld en ${state.games_played} minigames gespeeld.</p>
 <h3 style="margin-top:26px">🏆 Eindklassement minigames</h3>
 <div class="result-list">${state.players.slice().sort((a,b)=>b.wins-a.wins).map((p,i)=>`<div class="result-item"><strong>${['🥇','🥈','🥉','🎖️'][i]} ${esc(p.name)}</strong><span class="answer-col">${p.received} cadeaus ontvangen</span><b>${p.wins}× winnaar</b></div>`).join('')}</div>
 ${view==='host'?`<div class="actions"><button class="btn ghost" data-action="undo_gift">↩ Laatste cadeau terugdraaien</button><button class="btn secondary" data-action="reset">Opnieuw beginnen</button></div>`:''}`);
}
function renderHostOrScreen() {
 document.body.className='';
 let content = state.mode==='setup'?(view==='host'?renderSetup():panel(`<div class="hero"><div class="kicker">🎁 Klaar voor de Sinterklaas Spellenavond?</div><h1>Pak de pepernoten.<br>Pak je telefoon.</h1>
 <p>De spelleider stelt de deelnemers in. Straks bepaalt het rad wat jullie gaan spelen!</p>${joinHelp()}</div>`)):
 ['wheel','spinning'].includes(state.mode)?wheelScreen():state.mode==='game'?gameScreen():state.mode==='gift'?giftScreen():finishScreen();
 $('#app').innerHTML=`<main>${header()}<div class="layout">${content}${scoreboard()}</div></main><footer>Een feestelijke spelshow, geen nieuwe bordspellen nodig · Privé op jullie eigen wifi</footer>`;
 if(state.mode==='spinning') animateWheel();
 if(state.mode==='game' && state.game.kind==='music') manageAudio(); else stopMusic();
}
function renderPhone() {
 document.body.className='phone';
 if(!state.me){
  const seats=state.players.map((p,i)=>`<button class="choice" data-action="join" data-player="${p.id}" ${p.joined?'disabled':''}>
   <span class="choice-name">${['🎄','⭐','🎁','🔔'][i]} ${esc(p.name)}</span><span class="choice-secondary">${p.joined?'Al aangemeld':'Ik ben '+esc(p.name)}</span></button>`).join('');
  $('#app').innerHTML=`<main>${header()}<div class="panel"><div class="panel-pad"><div class="kicker">📱 Aanmelden</div><h2>Wie ben jij?</h2>
  <p class="muted" style="margin-top:12px">Vul de spelcode van de televisie in en kies je eigen naam.</p>
  <div class="formfield"><label class="field-label" for="joincode">Spelcode</label><input class="input" type="text" inputmode="numeric" id="joincode" maxlength="4" value="${esc(localStorage.getItem('sint-party-code')||'')}" placeholder="Vier cijfers"/></div>
  <div class="card-grid">${seats}</div></div></div></main>`;
  return;
 }
 const myself=player(state.me);
 let body='';
 if(state.mode==='setup'){
  body=`<div class="kicker">✅ Je bent binnen</div><h2>Hoi ${esc(myself.name)}!</h2><p class="muted" style="margin-top:14px">De spelleider maakt alles klaar. Je kunt dit scherm open laten.</p><div class="huge" style="margin-top:25px">🎁</div>`;
 }else if(['wheel','spinning'].includes(state.mode)){
  body=`<div class="kicker">🎡 Het rad bepaalt</div><h2>${state.mode==='spinning'?'Het rad draait!':'Op naar het volgende cadeau'}</h2><p class="muted" style="margin-top:12px">Kijk naar de televisie om te zien wat jullie spelen.</p><div class="huge" style="margin-top:30px">🎡</div>`;
 }else if(state.mode==='gift'){
  const gift=state.gift;
  body=`<div class="kicker">🎁 Cadeautijd</div><div class="huge" style="margin-top:20px">🏆</div><h2>${gift?.winner?pname(gift.winner)+' wint!':'Gelijkspel: dobbel!'}</h2>
  <p style="margin-top:15px">${gift?.winner?'De winnaar wijst aan wie nu een cadeau uit de zak krijgt.':'De spelleider laat de gelijkstaande spelers dobbelen.'}</p>
  <div class="callout gold" style="margin-top:24px">${state.eligible.map(pname).join(' · ')} ${state.eligible.length?'mag nu een cadeau ontvangen.':''}</div>`;
 }else if(state.mode==='finished'){
  body=`<div class="huge">🎉</div><h2>Fijne pakjesavond!</h2><p style="margin-top:14px">Jij hebt ${myself.received} cadeautje${myself.received===1?'':'s'} gekregen en ${myself.wins} minigames gewonnen.</p>`;
 }else{
  body=phoneGame(state.game);
 }
 $('#app').innerHTML=`<main>${header()}<div class="phone-layout"><div class="panel"><div class="panel-pad">${body}</div></div>
 <div class="panel" style="padding:18px"><div class="kicker">Mijn cadeaustand</div><h3 style="margin-top:7px">${esc(myself.name)} · ${myself.received} 🎁 · ${myself.wins} 🏆</h3><div class="small-score" style="margin-top:14px">${namesRow()}</div></div></div></main>`;
}
function phoneGame(g) {
 const cat=state.categories.find(c=>c.id===g.category);
 let text=`<div class="round-header"><span class="pill">${esc(cat.icon)} ${esc(cat.name)}</span><span class="pill">${g.round}/${g.total}</span></div>`;
 if(g.kind==='physical')return text+`<div class="kicker">🎲 Fysieke opdracht</div><h2 style="margin-top:10px">${esc(g.question.title)}</h2><p class="muted" style="margin-top:15px">${esc(g.question.task)}</p><div class="callout gold" style="margin-top:18px">${esc(g.question.rules)}</div><p style="margin-top:15px" class="muted">Spelverloop en winnaar worden op het TV-scherm bepaald.</p>`;
 if(g.phase==='reveal')return text+`<div class="kicker">✨ De uitslag</div><h2 style="margin:12px 0">Volgende opdracht?</h2>${resultRows(g)}${pointBoard(g)}
 <p class="muted" style="margin-top:21px">Kijk naar de televisie om verder te gaan.</p>`;
 text+=`<div class="kicker">${g.kind==='performance'?'De uitvoering':g.kind==='music'?'Muziekquiz':g.kind==='creative'?'De grappigste wint':g.kind==='who'?'De groepsstemming':'Schatvraag'}</div>
 <div class="question">${g.kind==='performance'?`${pname(g.performer)} is aan de beurt!`:esc(g.question)}</div>`;
 if(g.kind==='estimate'){
   if(g.my_submission!==undefined&&g.my_submission!==null)text+=answered('Je schatting is opgeslagen!');
   else text+=`<form id="answerform"><label class="field-label">Jouw schatting</label><input class="input" name="value" inputmode="decimal" type="number" step="any" required placeholder="Typ een getal" autofocus/><button class="btn mint" type="submit" style="width:100%;margin-top:12px">Verstuur schatting →</button></form>`;
 } else if(g.kind==='music'){
   if(g.my_submission)text+=answered('Je jaartal is opgeslagen!');
   else text+=`<p class="muted">Luister naar de muziek op de TV of via de Hitster-app. Je hoeft de artiest niet te weten.</p>
   <form id="answerform"><div class="formfield"><label class="field-label">Welk jaartal?</label><input class="input" name="year" type="number" min="1800" max="2100" inputmode="numeric" placeholder="Bijvoorbeeld 1987" required/></div>
   <div class="formfield"><label class="field-label">Artiest (optioneel)</label><input class="input" name="artist" maxlength="80" placeholder="Extra bonuspunt"/></div>
   <button class="btn mint" style="width:100%;margin-top:17px">🎵 Verstuur antwoord</button></form>`;
 } else if(g.kind==='creative'){
   if(g.phase==='answer'){
     if(g.my_submission)text+=answered('Jouw antwoord is binnen. Straks gaan we stemmen!');
     else text+=`<form id="answerform"><label class="field-label">Jouw grappigste antwoord</label><textarea class="input" name="value" required maxlength="200" placeholder="Schrijf iets creatiefs…"></textarea>
     <button class="btn mint" style="width:100%;margin-top:12px">💬 Versturen</button></form>`;
   }else if(g.phase==='vote'){
     if(g.my_vote)text+=answered('Je stem is opgeslagen!');
     else text+=`<div class="kicker" style="margin-bottom:13px">Stem op je favoriet</div><div class="card-grid">${g.options.map((o,i)=>`<button class="choice" data-action="vote" data-value="${o.id}" ${o.mine?'disabled':''}>
     <span class="choice-name">${String.fromCharCode(65+i)}. ${esc(o.text)}</span><span class="choice-secondary">${o.mine?'Jouw eigen antwoord': 'Stem op dit antwoord'}</span></button>`).join('')}</div>`;
   }
 } else if(g.kind==='who'){
   if(g.my_vote)text+=answered('Je stem is geteld!');
   else text+=`<p class="muted">Wie van jullie past het beste bij deze omschrijving?</p><div class="card-grid">${state.players.map(p=>`<button class="choice" data-action="vote" data-value="${p.id}">
   <span class="choice-name">👀 ${esc(p.name)}</span></button>`).join('')}</div>`;
 }else if(g.kind==='performance'){
   if(g.performer===state.me){
    text+=`<div class="prompt-box"><div class="kicker">🤫 Alleen jij mag dit zien</div><div class="secret">${esc(g.private_word)}</div>
    ${g.forbidden?.length?`<p class="forbidden">Niet zeggen: ${g.forbidden.map(esc).join(' · ')}</p>`:''}</div>
    <p class="muted" style="margin-top:17px">${g.category==='pictionary'?'Teken dit op papier. Geen letters of cijfers.':g.category==='uitbeelden'?'Beeld dit woord uit zonder te praten.':'Omschrijf het woord, zonder de verboden woorden te zeggen.'}</p>`;
   }else if(g.my_correct){
    text+=answered('🎉 Helemaal goed! Wacht tot de ronde voorbij is.');
   }else{
    text+=`<p class="muted">Kijk naar ${pname(g.performer)} en typ het geheime woord.</p>
    ${g.my_submission?`<p class="small error" style="margin-top:12px">'${esc(g.my_submission.guess)}' was nog niet goed. Probeer opnieuw!</p>`:''}
    <form id="answerform"><div class="formfield"><input class="input" name="value" type="text" maxlength="100" autocomplete="off" placeholder="Jouw gok…" required/></div>
    <button class="btn mint" style="width:100%;margin-top:13px">🔍 Probeer dit woord</button></form>`;
   }
   text+=`<div class="timer" id="live-timer" style="margin-top:24px">01:25</div>`;
 }
 text+=`<div style="margin-top:20px" class="pill">${statusBadge(g.phase)}</div>`;
 return text;
}
function answered(message){return `<div class="prompt-box"><div style="font-size:2.3rem">✅</div><h3 style="margin-top:8px">${esc(message)}</h3><p class="muted" style="margin-top:9px">Kijk op de televisie voor de volgende stap.</p></div>`;}
function buildKey() {
 if(!state)return '';
 const g=state.game;
 if(view==='phone')return [view,state.room,state.me,state.mode,g?.category,g?.round,g?.phase,
   g?.my_submission===undefined?'':JSON.stringify(g.my_submission),g?.my_vote,g?.performer,
   state.gift?.winner,state.gifts_given].join('|');
 if(view==='host' && state.mode==='setup')return [view,state.mode,state.room,state.music_count,state.hitster_count,state.players.map(p=>p.name+p.target)].join('|');
 return [view,state.mode,state.room,state.spin?.stamp,g?.category,g?.round,g?.phase,state.gift?.winner,state.gifts_given].join('|');
}
async function api(path,body,admin=false,upload=false){
 const headers=admin?{'X-Admin-Key':adminKey}:{};
 if(!upload)headers['Content-Type']='application/json';
 const res=await fetch(path,{method:'POST',headers,body:upload?body:JSON.stringify(body)});
 const data=await res.json();
 if(!res.ok)throw new Error(data.error||'Er ging iets mis.');
 return data;
}
async function admin(action,extra={}){return api('/api/admin',{action,...extra},true);}
async function refresh() {
 if(pollRunning)return;pollRunning=true;
 try{
  const qs=new URLSearchParams();
  if(view==='host')qs.set('key',adminKey);
  if(view==='phone'&&savedToken)qs.set('token',savedToken);
  const res=await fetch('/api/state?'+qs.toString(),{cache:'no-store'});
  if(!res.ok)throw new Error('Kan de server niet bereiken.');
  state=await res.json();
  const key=buildKey();
  if(key!==lastKey){lastKey=key;if(view==='phone')renderPhone();else if(view==='home')renderHome();else renderHostOrScreen();}
  const sidebar=document.querySelector('aside.sidebar');
  if(sidebar && state.version!==lastSidebarVersion && (view==='host'||view==='screen')){
    sidebar.outerHTML=scoreboard();lastSidebarVersion=state.version;
  }
  const g=state.game;
  if(g){const counts=roundCounts(g);const el=$('#live-count');if(el)el.textContent=`${counts[0]} van ${counts[1]} ${counts[2]} binnen`;}
  updateCountdown();
  if(state.mode==='spinning' && view==='host' && Date.now()-state.spin.at*1000 > 5100 && !busy){
     busy=true;admin('start_game').then(refresh).catch(e=>toast(e.message,true)).finally(()=>busy=false);
  }
  if(state.mode==='game'&&g?.kind==='music')manageAudio();
 }catch(e){if(!state)$('#app').innerHTML=`<main><div class="panel panel-pad"><h2>Geen verbinding met de spelserver</h2><p style="margin-top:14px">Controleer of server.py draait en probeer de pagina opnieuw te laden.</p></div></main>`;}
 finally{pollRunning=false;}
}
function updateCountdown(){
 const e=$('#live-timer');if(!e||!state?.game?.deadline)return;
 const secs=Math.max(0,Math.ceil(state.game.deadline-Date.now()/1000));
 e.textContent=`${String(Math.floor(secs/60)).padStart(2,'0')}:${String(secs%60).padStart(2,'0')}`;
 if(secs===0)e.style.color='#ff9c97';
}
function animateWheel(){
 if(!state?.spin||spinningStamp===state.spin.stamp)return;
 spinningStamp=state.spin.stamp;
 const e=$('#spinningWheel');if(!e)return;
 const idx=state.categories.findIndex(c=>c.id===state.spin.category);
 const angle=360/state.categories.length;
 const rotate=360*7-((idx+.5)*angle);
 requestAnimationFrame(()=>requestAnimationFrame(()=>{e.style.transform=`rotate(${rotate}deg)`;}));
 const chosen=state.categories[idx];
 setTimeout(()=>{const title=$('#wheel-title');if(title&&state?.spin?.stamp===spinningStamp)title.textContent=`${chosen.icon} ${chosen.name}!`;},4400);
}
function stopMusic(){if(music){music.pause();music.currentTime=0;music=null;lastTrack='';}}
function manageAudio(){
 const g=state?.game;
 if(!g||g.kind!=='music'||g.phase==='reveal'||!g.audio_url){stopMusic();return;}
 if(lastTrack!==g.audio_url){stopMusic();lastTrack=g.audio_url;music=new Audio(g.audio_url);music.preload='auto';
  // Browser policies can block autoplay; explicit play button remains available.
  if(view==='screen')music.play().catch(()=>{});
 }
}
function renderHome(){
 document.body.className='';
 $('#app').innerHTML=`<main><div class="panel panel-pad"><div class="hero"><div class="kicker">🎁 De grote Sinterklaas Spellenavond</div><h1>Welkom bij de<br>pakjesavond!</h1>
 <p>Kies de juiste weergave. De spelleider gebruikt de geheime hostlink uit de terminal; de overige spelers hun telefoon.</p>
 <div class="actions"><a class="btn" href="/play" style="text-decoration:none">📱 Ik speel mee</a><a class="btn secondary" href="/screen" style="text-decoration:none">📺 TV-scherm</a></div>
 <p class="muted small">Host? Open de beveiligde hostlink die het startprogramma toont.</p></div></div></main>`;
}
async function actButton(button){
 if(busy)return;
 const a=button.dataset.action;busy=true;button.disabled=true;
 try{
  let result;
  if(a==='join'){
    const room=$('#joincode')?.value.trim();
    result=await api('/api/claim',{room,player:button.dataset.player,token:savedToken});
    savedToken=result.data.token;localStorage.setItem('sint-party-token',savedToken);localStorage.setItem('sint-party-code',room);
  }else if(a==='configure'||a==='start'){
    const players=[0,1,2,3].map(i=>({name:$(`#name-${i}`).value,target:Number($(`#target-${i}`).value||0)}));
    await admin('configure',{players});
    if(a==='start')await admin('start');
  }else if(a==='reset'){
    if(window.prompt('Dit verwijdert alle cadeaustanden en scores, maar bewaart de muziekbibliotheek. Typ RESET om door te gaan.')!=='RESET')return;
    await admin('reset',{confirmation:'RESET'});
  }else if(a==='finish'){
    if(!window.confirm('Is de zak echt leeg? Dan wordt de spelavond afgesloten.'))return;
    await admin('finish');
  }else if(a==='start_selected'){
    const category=$('#quick-category')?.value;
    if(!category)throw new Error('Kies een minigame.');
    await admin('start_selected',{category});
  }else if(a==='cancel_game'){
    if(!window.confirm('Minigame annuleren? Er wordt geen winnaar gekozen en geen cadeau uitgedeeld.'))return;
    await admin('cancel_game');
  }else if(a==='open_vote'||a==='spin'||a==='start_game'||a==='next'||a==='undo_gift'){
    await admin(a);
  }else if(a==='reveal'){
    let extra={};
    if(state.game?.kind==='music'&&state.game?.source==='hitster'){
      extra={year:$('#correct-year')?.value||'',artist:$('#correct-artist')?.value||''};
    }
    await admin('reveal',extra);
  }else if(a==='choose_winner'||a==='physical_result'){
    await admin(a,{winner:button.dataset.winner});
  }else if(a==='give_gift'){
    if(!window.confirm(`${pname(button.dataset.recipient).replaceAll(/&[^;]+;/g,'')} krijgt nu een cadeau. Klopt dat?`))return;
    await admin('give_gift',{recipient:button.dataset.recipient});
  }else if(a==='vote'){
    await api('/api/submit',{token:savedToken,value:button.dataset.value});
  }else if(a==='play_audio'){
    manageAudio();if(music)await music.play();else throw new Error('Geen audiobestand voor deze ronde.');
  }else if(a==='stop_audio'){
    if(music){music.pause();music.currentTime=0;}
  }else if(a==='release_seat'){
    if(!window.confirm('Telefoon van '+pname(button.dataset.player)+' ontkoppelen? Deze speler kan zich opnieuw aanmelden.'))return;
    await admin('release_seat',{player:button.dataset.player});
  }else if(a==='delete_hitster'){
    if(!window.confirm('Deze Hitster-kaart verwijderen?'))return;
    await admin('delete_hitster',{id:button.dataset.id});
    importSummary='Kaart verwijderd.';
  }else if(a==='delete_audio'){
    if(!window.confirm('Deze audiotrack verwijderen?'))return;
    await admin('delete_audio',{id:button.dataset.id});
  }else throw new Error('Onbekende actie.');
  if(a!=='play_audio'&&a!=='stop_audio'){lastKey='';await refresh();}
 }catch(e){toast(e.message,true);}finally{busy=false;button.disabled=false;}
}
async function submitForm(form){
 if(busy)return;busy=true;
 try{
  if(form.id==='hitster-import'){
    const file=form.querySelector('input[type=file]')?.files[0];
    if(!file)throw new Error('Kies eerst een CSV-bestand.');
    if(file.size>300000)throw new Error('CSV is te groot (maximaal 300 KB).');
    const result=await admin('import_hitster',{csv:await file.text()});
    const d=result.data;
    importSummary=`${d.added} kaarten toegevoegd; ${d.duplicates} duplicaten overgeslagen; ${d.skipped} ongeldige regels. Totaal: ${d.total}.`
      +(d.errors?.length?' Fouten: '+d.errors.join(' | '):'');
    lastKey='';await refresh();
    toast('✅ CSV-import afgerond');
  }else if(form.id==='upload'){
    const data=new FormData(form);
    const res=await api('/api/upload',data,true,true);
    toast('🎵 Muziek toegevoegd: '+res.title);
    lastKey='';await refresh();
  }else if(form.id==='answerform'){
    const data=new FormData(form);
    const payload={token:savedToken};for(const [k,v] of data.entries())payload[k]=v;
    if(state.game.kind==='estimate'||state.game.kind==='creative'||state.game.kind==='performance')payload.value=data.get('value');
    const response=await api('/api/submit',payload);
    if(state.game.kind==='performance')toast(response.data.correct?'🎉 Goed geraden!':'Nog niet goed, probeer opnieuw.');
    else toast('✅ Antwoord opgeslagen!');
    lastKey='';await refresh();
  }
 }catch(e){toast(e.message,true);}finally{busy=false;}
}

document.addEventListener('click',event=>{const b=event.target.closest('button[data-action]');if(b)actButton(b);});
document.addEventListener('submit',event=>{if(event.target.matches('#answerform,#upload,#hitster-import')){event.preventDefault();submitForm(event.target);}});
if(view==='home')renderHome();
refresh();
setInterval(refresh,1000);
setInterval(updateCountdown,250);
