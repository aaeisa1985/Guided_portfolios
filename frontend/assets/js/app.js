(function(){
'use strict';
const API=location.origin+'/api/v1';
const state={route:'landing',id:null};
const session={token:localStorage.getItem('emcoin_token'),customer:null};
const $=s=>document.querySelector(s);
const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const num=v=>Number(v||0);
const money=(n,c='AED')=>num(n).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})+' '+c;
const pct=(n)=>{const v=num(n);return (v*100).toFixed(2)+'%';};
const feePct=(n)=>num(n).toFixed(2)+'%';
const dots=n=>'<span class="risk-dots">'+[1,2,3,4,5].map(i=>'<span class="'+(i<=num(n)?'on':'')+'"></span>').join('')+'</span>';
const fmtDate=d=>d?new Date(d).toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'}):'—';
const row=(k,v)=>'<div class="stmt-row"><span class="k">'+esc(k)+'</span><span class="v">'+v+'</span></div>';

async function req(path,opt={}){
 const r=await fetch(API+path,{...opt,headers:{'Content-Type':'application/json',...(session.token?{Authorization:'Bearer '+session.token}:{}),...(opt.headers||{})}});
 let d={};try{d=await r.json()}catch(e){}
 if(!r.ok){if(r.status===401){localStorage.removeItem('emcoin_token');session.token=null;session.customer=null;nav('landing')}throw Error(d.detail||d.message||'Request failed')}
 return d;
}
function toast(message,type='info'){
 const x=document.createElement('div');x.className='toast toast-'+type;
 x.innerHTML='<span class="toast-icon">'+({success:'✓',error:'!',warning:'!',info:'i'}[type]||'i')+'</span><span>'+esc(message)+'</span>';
 $('#toasts').appendChild(x);requestAnimationFrame(()=>x.classList.add('show'));setTimeout(()=>{x.classList.remove('show');setTimeout(()=>x.remove(),220)},3400);
}
async function boot(){
 if(session.token){try{session.customer=await req('/auth/me')}catch(e){}}
 await render();
}
function nav(route,id){state.route=route;state.id=id||null;render();scrollTo({top:0,behavior:'smooth'})}
function top(){
 const c=session.customer;
 const tabs=c?['dashboard','portfolios','subscriptions','activity','profile']:['portfolios'];
 return '<div class="topbar"><div class="topbar-inner"><button class="brand" onclick="nav(\'landing\')"><span class="mark">EmCoin</span> Guided Portfolios</button><div class="tabs">'+tabs.map(x=>'<button class="tab '+(state.route===x?'active':'')+'" onclick="nav(\''+x+'\')">'+x[0].toUpperCase()+x.slice(1)+'</button>').join('')+'</div><div class="top-actions">'+(c?'<span class="avatar">'+esc((c.name||'?').trim()[0])+'</span><button class="btn-ghost" onclick="logout()">Sign out</button>':'<button class="btn-ghost" onclick="auth(\'login\')">Sign in</button><button class="btn btn-primary btn-sm" onclick="auth(\'register\')">Open an account</button>')+'</div></div></div>';
}
async function render(){
 let html=top()+'<main><div id="page" class="page-enter">';
 try{
  if(state.route==='landing')html+=landing();
  else if(state.route==='portfolios')html+=await portfolios();
  else if(state.route==='detail')html+=await detail(state.id);
  else if(state.route==='dashboard')html+=await dashboard();
  else if(state.route==='subscriptions')html+=await subscriptions();
  else if(state.route==='subscription')html+=await subscriptionDetail(state.id);
  else if(state.route==='activity')html+=activity();
  else if(state.route==='profile')html+=profile();
  else html+=landing();
 }catch(e){html+='<div class="card error-card"><div class="section-title">Unable to load</div><h3>'+esc(e.message)+'</h3><button class="btn btn-secondary" onclick="render()">Retry</button></div>'}
 html+='</div></main><footer><div class="wrap">EmCoin Guided Portfolios · institutional-grade MVP interface</div></footer>';
 $('#root').innerHTML=html;
}
function landing(){
 return '<div class="hero"><div class="kicker">EmCoin · United Arab Emirates</div><h1>Guided investing, kept on the record.</h1><p class="lead">A small shelf of model portfolios, a risk profile set at onboarding, and a suitability check before every subscription — so nothing moves until it is logged.</p><div class="hero-actions"><button class="btn btn-primary" onclick="auth(\'register\')">Open an account</button><button class="btn btn-secondary" onclick="nav(\'portfolios\')">View the portfolio shelf</button></div><div class="hero-meta"><span>✓ Suitability-led</span><span>✓ Auditable consent</span><span>✓ UAE-focused</span></div></div><hr class="divider"><div class="section-title">The shelf</div><div class="feature-grid"><div class="card"><div class="feature-number">01</div><h3>Defined risk</h3><p class="hint">Investor risk profile and portfolio risk are checked before subscription.</p></div><div class="card"><div class="feature-number">02</div><h3>Recorded decisions</h3><p class="hint">Consents, suitability checks and subscription events are retained.</p></div><div class="card"><div class="feature-number">03</div><h3>Transparent portfolios</h3><p class="hint">Allocation, holdings, performance and documents sit behind each portfolio.</p></div></div>';
}
async function portfolios(){
 const ps=await req('/portfolios');
 return '<div class="section-title">Portfolio shelf</div><h2>Model portfolios, by risk level</h2><p class="lead">Browse without an account. Sign in to run suitability and subscribe.</p><div class="card shelf-card">'+(ps.length?'<div class="shelf-row shelf-head"><b>Portfolio</b><b>Risk</b><b>Minimum</b><b>Fee</b></div>':'<div class="empty"><div class="empty-icon">◌</div><h3>No portfolios available</h3><p class="hint">The portfolio catalog has not been seeded yet.</p></div>')+ps.map(p=>'<div class="shelf-row" onclick="nav(\'detail\',\''+p.id+'\')"><div><div class="shelf-name">'+esc(p.name)+'</div><div class="shelf-cat">'+esc(p.category)+'</div></div><div>'+dots(p.risk_level)+'</div><div>'+money(p.minimum_investment,p.base_currency)+'</div><div>'+feePct(p.management_fee)+' p.a.</div></div>').join('')+'</div>';
}
function chart(perf){
 if(!perf||!perf.length)return '<div class="chart-empty">Performance history will appear here once NAV observations are recorded.</div>';
 const data=[...perf].sort((a,b)=>new Date(a.date)-new Date(b.date));
 const vals=data.map(x=>num(x.nav));const min=Math.min(...vals),max=Math.max(...vals),range=max-min||1,w=720,h=250,p=28;
 const pts=data.map((x,i)=>{const X=p+(i/(Math.max(data.length-1,1)))*(w-p*2);const Y=h-p-((num(x.nav)-min)/range)*(h-p*2);return [X,Y,x]});
 const line=pts.map(x=>x[0].toFixed(1)+','+x[1].toFixed(1)).join(' ');
 const last=pts[pts.length-1];
 const labels=pts.filter((_,i)=>i===0||i===Math.floor((pts.length-1)/2)||i===pts.length-1);
 return '<div class="chart-wrap"><svg viewBox="0 0 '+w+' '+h+'" role="img" aria-label="NAV performance chart"><line class="gridline" x1="'+p+'" y1="'+(h-p)+'" x2="'+(w-p)+'" y2="'+(h-p)+'"/><line class="gridline" x1="'+p+'" y1="'+(h/2)+'" x2="'+(w-p)+'" y2="'+(h/2)+'"/><line class="gridline" x1="'+p+'" y1="'+p+'" x2="'+(w-p)+'" y2="'+p+'"/><polyline class="nav-line" points="'+line+'"/><circle class="nav-dot" cx="'+last[0]+'" cy="'+last[1]+'" r="4"/>'+labels.map(x=>'<text class="axis-label" x="'+x[0]+'" y="'+(h-7)+'" text-anchor="'+(x===labels[0]?'start':x===labels[labels.length-1]?'end':'middle')+'">'+fmtDate(x[2].date)+'</text>').join('')+'</svg><div class="chart-stat"><span>NAV <b>'+num(last[2].nav).toFixed(4)+'</b></span><span>As of <b>'+fmtDate(last[2].date)+'</b></span></div></div>';
}
async function detail(id){
 const d=await req('/portfolios/'+id),p=d.portfolio;
 return '<button class="btn-ghost" onclick="nav(\'portfolios\')">← Back to shelf</button><div class="pf-head"><div><div class="eyebrow">'+esc(p.category)+' '+dots(p.risk_level)+'</div><h2>'+esc(p.name)+'</h2><p class="lead">'+esc(p.objective)+'</p></div><div class="status-badge">ACTIVE</div></div><div class="pf-layout"><div><div class="card"><div class="section-title">Key terms</div>'+row('Vehicle type',esc(p.vehicle_type))+row('Base currency',esc(p.base_currency))+row('Liquidity',esc(p.liquidity_terms))+row('Benchmark',esc(p.benchmark||'—'))+row('Management fee',feePct(p.management_fee)+' p.a.')+row('Minimum investment',money(p.minimum_investment,p.base_currency))+'</div><div class="card"><div class="section-title">Allocation</div>'+(d.allocations||[]).map(a=>'<div class="allocation-row"><span>'+esc(a.asset_class)+'</span><span><b>'+feePct(a.target_weight)+'</b><i><em style="width:'+Math.min(100,num(a.target_weight))+'%"></em></i></span></div>').join('')||'<div class="hint">No allocation data has been recorded.</div>'+'</div><div class="card"><div class="section-title">Holdings</div>'+((d.holdings||[]).length?(d.holdings||[]).map(h=>row(h.instrument_name,(h.ticker?esc(h.ticker)+' · ':'')+feePct(h.target_weight))).join(''):'<div class="hint">No holdings have been recorded.</div>')+'</div><div class="card"><div class="section-title">NAV performance</div>'+chart(d.performance)+'</div><div class="card"><div class="section-title">Documents</div>'+((d.documents||[]).length?(d.documents||[]).map(x=>'<div class="doc-row"><span>'+esc(x.document_type)+' · v'+esc(x.version)+'</span><span>'+fmtDate(x.published_at)+'</span></div>').join(''):'<div class="hint">No published documents are available.</div>')+'</div></div><div class="sticky"><div class="card"><div class="section-title">Guided steps</div><button class="btn btn-secondary btn-block" onclick="suit(\''+p.id+'\')">Check suitability</button><div id="suit-result"></div><hr class="divider"><div class="field"><label>Investment amount (AED)</label><input id="amt" type="number" min="'+num(p.minimum_investment)+'" value="'+num(p.minimum_investment)+'"></div><div class="field"><label>Time horizon (years)</label><input id="yrs" type="number" min="1" max="50" value="5"></div><button class="btn btn-secondary btn-block" onclick="simulate(\''+p.id+'\')">Run projection</button><div id="sim"></div><hr class="divider"><button class="btn btn-primary btn-block" onclick="subscribe(\''+p.id+'\')">Subscribe to this portfolio</button><p class="hint microcopy">A suitability pass and recorded consent are required before subscription.</p></div></div></div>';
}
async function suit(id){
 if(!session.token){auth('login');return}
 try{const r=await req('/suitability/check',{method:'POST',body:JSON.stringify({portfolio_id:id})});$('#suit-result').innerHTML='<div class="suit-box '+(r.suitable?'suit-ok':'suit-no')+'"><b>'+(r.suitable?'Suitable for your current profile':'Not suitable for your current profile')+'</b><span>'+esc(r.reason)+'</span></div>';toast(r.suitable?'Suitability check passed':'Portfolio is not suitable',r.suitable?'success':'warning')}
 catch(e){toast(e.message,'error')}
}
async function simulate(id){
 try{const r=await req('/simulator',{method:'POST',body:JSON.stringify({portfolio_id:id,amount:num($('#amt').value),years:num($('#yrs').value)})});const s=r.scenarios||{};$('#sim').innerHTML='<div class="hint">Expected net annual return '+pct(r.expectedAnnualReturn)+'</div><div class="grid-3 sim-grid"><div class="scenario"><small>Conservative</small><br><b>'+money(s.conservative)+'</b></div><div class="scenario"><small>Base</small><br><b>'+money(s.base)+'</b></div><div class="scenario"><small>Optimistic</small><br><b>'+money(s.optimistic)+'</b></div></div><p class="hint">'+esc(r.disclaimer)+'</p>'}
 catch(e){toast(e.message,'error')}
}
function subscribe(id){
 if(!session.token){auth('login');return}
 openSubscribeModal(id);
}
async function openSubscribeModal(id){
 const d=await req('/portfolios/'+id),p=d.portfolio;
 document.body.insertAdjacentHTML('beforeend','<div class="modal-backdrop" id="modal"><div class="modal modal-wide"><button class="modal-close" onclick="closeModal()">×</button><div class="section-title">Subscription</div><h2>'+esc(p.name)+'</h2><div class="field"><label>Investment amount ('+esc(p.base_currency)+')</label><input id="subamt" type="number" min="'+num(p.minimum_investment)+'" value="'+num(p.minimum_investment)+'"></div><div class="consent-box"><b>Portfolio disclosure & subscription terms</b><p>I confirm that I have reviewed the portfolio information, understand the stated risks and fees, and consent to the subscription process.</p><label class="check"><input id="consent" type="checkbox"> I accept these terms.</label></div><button class="btn btn-primary btn-block" onclick="confirmSubscribe(\''+id+'\')">Confirm subscription</button></div></div>');
}
async function confirmSubscribe(id){
 if(!$('#consent').checked){toast('Please accept the disclosure terms first','warning');return}
 try{
  const text='I confirm that I have reviewed the portfolio information, understand the stated risks and fees, and consent to the subscription process.';
  await req('/consents',{method:'POST',body:JSON.stringify({portfolio_id:id,consent_type:'PORTFOLIO_SUBSCRIPTION',consent_text:text,accepted:true})});
  const r=await req('/subscriptions',{method:'POST',body:JSON.stringify({portfolio_id:id,amount:num($('#subamt').value)})});
  closeModal();toast('Subscription created · '+r.status,'success');nav('subscriptions');
 }catch(e){toast(e.message,'error')}
}
async function dashboard(){
 const d=await req('/dashboard');
 const aum=d.marketValue??d.aum??0,pnl=d.profitLoss??0,pending=d.pendingSubscriptions??d.pending??0,count=d.portfolioCount??d.count??0;
 return '<div class="section-title">Dashboard</div><h2>Welcome back, '+esc((session.customer?.name||'Investor').split(' ')[0])+'</h2><div class="metric-grid"><div class="card metric"><div class="section-title">Portfolio value</div><h2>'+money(aum)+'</h2><span class="metric-sub">Current reported value</span></div><div class="card metric"><div class="section-title">Profit / loss</div><h2 class="'+(pnl>=0?'positive':'negative')+'">'+(pnl>=0?'+':'')+money(pnl)+'</h2><span class="metric-sub">Based on recorded positions</span></div><div class="card metric"><div class="section-title">Pending</div><h2>'+money(pending)+'</h2><span class="metric-sub">'+count+' subscription'+(count===1?'':'s')+'</span></div></div><div class="card"><div class="section-title">Account status</div>'+row('Customer ID',esc(session.customer.customerId||'—'))+row('KYC',chip(session.customer.kycStatus||'PENDING'))+row('AML',chip(session.customer.amlStatus||'PENDING'))+row('Risk profile',session.customer.riskProfile?esc(session.customer.riskProfile.category)+' · score '+esc(session.customer.riskProfile.score):'Not assessed')+'</div>';
}
function chip(v){const x=String(v),cl=x.includes('APPROVED')||x.includes('ACTIVE')||x.includes('COMPLETED')?'chip-teal':x.includes('PENDING')?'chip-brass':'chip-rust';return '<span class="chip '+cl+'"><span class="chip-dot"></span>'+esc(x)+'</span>'}
async function subscriptions(){
 const xs=await req('/subscriptions');
 return '<div class="section-title">Subscriptions</div><h2>Your subscriptions</h2><div class="card">'+(xs.length?xs.map(s=>'<div class="subscription-row" onclick="nav(\\'subscription\\',\\''+s.id+'\\')"><div><b>'+esc(s.portfolio_name||'Portfolio')+'</b><div class="hint">'+fmtDate(s.created_at)+' · '+esc(s.currency||'AED')+'</div></div><div class="subscription-value">'+money(s.subscription_amount,s.currency||'AED')+'<br>'+chip(s.status)+'</div></div>').join(''):'<div class="empty"><div class="empty-icon">◌</div><h3>No subscriptions yet</h3><p class="hint">Explore the portfolio shelf to start your first guided investment.</p><button class="btn btn-primary" onclick="nav(\\'portfolios\\')">Explore portfolios</button></div>')+'</div>';
}
async function subscriptionDetail(id){
 const d=await req('/subscriptions/'+id),s=d.subscription;
 return '<button class="btn-ghost" onclick="nav(\\'subscriptions\\')">← Back to subscriptions</button><div class="section-title">Subscription record</div><h2>'+esc(String(s.id).slice(0,8).toUpperCase())+'</h2><div class="card">'+row('Amount',money(s.subscription_amount))+row('Status',chip(s.status))+row('Created',fmtDate(s.created_at))+'</div><div class="card"><div class="section-title">Lifecycle</div>'+((d.events||[]).map(e=>'<div class="doc-row"><span><b>'+esc(e.event_type)+'</b></span><span>'+fmtDate(e.created_at)+'</span></div>').join('')||'<div class="hint">No events recorded.</div>')+'</div>';
}
async function activity(){const xs=await req('/activity');return '<div class="section-title">Activity</div><h2>Your activity log</h2><div class="card">'+(xs.length?xs.map(x=>'<div class="doc-row"><span><b>'+esc(x.action)+'</b><div class="hint">'+esc(x.entity_type)+(x.entity_id?' · '+esc(String(x.entity_id).slice(0,8)):'')+'</div></span><span>'+fmtDate(x.created_at)+'</span></div>').join(''):'<div class="empty"><div class="empty-icon">◌</div><h3>No activity yet</h3><p class="hint">Your suitability, consent and subscription events will appear here.</p></div>')+'</div>'}
function profile(){const c=session.customer||{};return '<div class="section-title">Profile</div><h2>'+esc(c.name||'Investor')+'</h2><div class="grid-2"><div class="card">'+row('Customer ID',esc(c.customerId||'—'))+row('Email',esc(c.email||'—'))+row('Investor type',esc(c.investorType||'—'))+'</div><div class="card">'+row('KYC',chip(c.kycStatus||'—'))+row('AML',chip(c.amlStatus||'—'))+row('Role',esc(c.role||'—'))+'</div></div>'}
function auth(mode){
 const login=mode==='login';
 document.body.insertAdjacentHTML('beforeend','<div class="modal-backdrop" id="modal"><div class="modal"><button class="modal-close" onclick="closeModal()">×</button><div class="section-title">'+(login?'Welcome back':'Open an account')+'</div><h2>'+(login?'Sign in':'Start your journey')+'</h2><form id="authform">'+(login?'':'<div class="field"><label>Full name</label><input id="name" required></div>')+'<div class="field"><label>Email</label><input id="email" type="email" required></div>'+(login?'':'<div class="field"><label>Mobile</label><input id="mobile"></div>')+'<div class="field"><label>Password</label><input id="password" type="password" minlength="8" required></div><button class="btn btn-primary btn-block">Continue</button><p class="hint" id="autherr"></p></form></div></div>');
 $('#authform').onsubmit=async e=>{e.preventDefault();try{const body=login?{email:$('#email').value,password:$('#password').value}:{full_name:$('#name').value,email:$('#email').value,password:$('#password').value,mobile:$('#mobile').value};const r=await req('/auth/'+(login?'login':'register'),{method:'POST',body:JSON.stringify(body)});session.token=r.access_token;localStorage.setItem('emcoin_token',session.token);session.customer=await req('/auth/me');closeModal();toast(login?'Signed in successfully':'Account created successfully','success');nav('dashboard')}catch(x){$('#autherr').textContent=x.message}}
}
function closeModal(){$('#modal')?.remove()}
function logout(){localStorage.removeItem('emcoin_token');session.token=null;session.customer=null;toast('Signed out','info');nav('landing')}
window.nav=nav;window.auth=auth;window.closeModal=closeModal;window.logout=logout;window.suit=suit;window.simulate=simulate;window.subscribe=subscribe;window.confirmSubscribe=confirmSubscribe;window.render=render;
boot();
})();