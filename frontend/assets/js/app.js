(function(){
'use strict';
const API=location.origin+'/api/v1';
const state={route:'landing',id:null};
const session={token:localStorage.getItem('xcompany_token'),customer:null};
const adminSession={token:localStorage.getItem('xcompany_admin_token'),principal:null};
const $=s=>document.querySelector(s);
const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const num=v=>Number(v||0);
const money=(n,c='AED')=>num(n).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})+' '+c;
const pct=(n)=>{const v=num(n);return (v*100).toFixed(2)+'%';};
const feePct=(n)=>num(n).toFixed(2)+'%';
const dots=n=>'<span class="risk-dots">'+[1,2,3,4,5].map(i=>'<span class="'+(i<=num(n)?'on':'')+'"></span>').join('')+'</span>';
const fmtDate=d=>d?new Date(d).toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'}):'—';
const row=(k,v)=>'<div class="stmt-row"><span class="k">'+esc(k)+'</span><span class="v">'+v+'</span></div>';

async function adminReq(path,opt={}){
 const r=await fetch(API+path,{...opt,headers:{'Content-Type':'application/json',...(adminSession.token?{Authorization:'Bearer '+adminSession.token}:{}),...(opt.headers||{})}});
 let d={};try{d=await r.json()}catch(e){}
 if(!r.ok){if(r.status===401||r.status===403){localStorage.removeItem('xcompany_admin_token');adminSession.token=null;adminSession.principal=null;state.route='landing'}throw Error(d.detail||d.message||'Request failed')}
 return d;
}
async function req(path,opt={}){
 const r=await fetch(API+path,{...opt,headers:{'Content-Type':'application/json',...(session.token?{Authorization:'Bearer '+session.token}:{}),...(opt.headers||{})}});
 let d={};try{d=await r.json()}catch(e){}
 if(!r.ok){if(r.status===401){localStorage.removeItem('xcompany_token');session.token=null;session.customer=null;nav('landing')}throw Error(d.detail||d.message||'Request failed')}
 return d;
}
function toast(message,type='info'){
 const x=document.createElement('div');x.className='toast toast-'+type;
 x.innerHTML='<span class="toast-icon">'+({success:'✓',error:'!',warning:'!',info:'i'}[type]||'i')+'</span><span>'+esc(message)+'</span>';
 $('#toasts').appendChild(x);requestAnimationFrame(()=>x.classList.add('show'));setTimeout(()=>{x.classList.remove('show');setTimeout(()=>x.remove(),220)},3400);
}
async function boot(){
 if(session.token){
  try{session.customer=await req('/auth/me');if(session.customer?.role==='MANAGER')state.route='manager'}catch(e){}
 }
 if(adminSession.token){try{adminSession.principal=await adminReq('/admin/auth/me');state.route='admin'}catch(e){}}
 await render();
}
function nav(route,id){state.route=route;state.id=id||null;render();scrollTo({top:0,behavior:'smooth'})}
function top(){
 const c=session.customer;
 const a=adminSession.principal;
 const tabs=c?['dashboard','portfolios','subscriptions','activity','profile']:['portfolios'];
 const managerBtn=c?.role==='MANAGER'&&!a?'<button class="btn-ghost" onclick="nav(\'manager\')">Manager Console</button>':'';
 return '<div class="topbar"><div class="topbar-inner"><button class="brand" onclick="nav(\'landing\')"><span class="mark">X Company</span> Guided Portfolios</button><div class="tabs">'+tabs.map(x=>'<button class="tab '+(state.route===x?'active':'')+'" onclick="nav(\''+x+'\')">'+x[0].toUpperCase()+x.slice(1)+'</button>').join('')+'</div><div class="top-actions">'+managerBtn+(a?'<span class="avatar">A</span><button class="btn-ghost" onclick="adminLogout()">Admin sign out</button>':'<button class="btn-ghost" onclick="adminAuth()">Admin</button>')+(c?'<span class="avatar">'+esc((c.name||'?').trim()[0])+'</span><button class="btn-ghost" onclick="logout()">Sign out</button>':'<button class="btn-ghost" onclick="auth(\'login\')">Sign in</button><button class="btn btn-primary btn-sm" onclick="auth(\'register\')">Open an account</button>')+'</div></div></div>';
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
  else if(state.route==='admin')html+=await adminPage();
  else if(state.route==='manager')html+=await managerPage();
  else html+=landing();
 }catch(e){html+='<div class="card error-card"><div class="section-title">Unable to load</div><h3>'+esc(e.message)+'</h3><button class="btn btn-secondary" onclick="render()">Retry</button></div>'}
 html+='</div></main><footer><div class="wrap">X Company Guided Portfolios · institutional-grade MVP interface</div></footer>';
 $('#root').innerHTML=html;
}
function landing(){
 return '<div class="hero"><div class="kicker">X Company · United Arab Emirates</div><h1>Guided investing, kept on the record.</h1><p class="lead">A small shelf of model portfolios, a risk profile set at onboarding, and a suitability check before every subscription — so nothing moves until it is logged.</p><div class="hero-actions"><button class="btn btn-primary" onclick="auth(\'register\')">Open an account</button><button class="btn btn-secondary" onclick="nav(\'portfolios\')">View the portfolio shelf</button></div><div class="hero-meta"><span>✓ Suitability-led</span><span>✓ Auditable consent</span><span>✓ UAE-focused</span></div></div><hr class="divider"><div class="section-title">The shelf</div><div class="feature-grid"><div class="card"><div class="feature-number">01</div><h3>Defined risk</h3><p class="hint">Investor risk profile and portfolio risk are checked before subscription.</p></div><div class="card"><div class="feature-number">02</div><h3>Recorded decisions</h3><p class="hint">Consents, suitability checks and subscription events are retained.</p></div><div class="card"><div class="feature-number">03</div><h3>Transparent portfolios</h3><p class="hint">Allocation, holdings, performance and documents sit behind each portfolio.</p></div></div>';
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
  const r=await req('/subscriptions',{method:'POST',headers:{'X-Idempotency-Key':crypto.randomUUID()},body:JSON.stringify({portfolio_id:id,amount:num($('#subamt').value)})});
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
 return '<div class="section-title">Subscriptions</div><h2>Your subscriptions</h2><div class="card">'+(xs.length?xs.map(s=>'<div class="subscription-row" onclick="nav(\'subscription\',\''+s.id+'\')"><div><b>'+esc(s.portfolio_name||'Portfolio')+'</b><div class="hint">'+fmtDate(s.created_at)+' · '+esc(s.currency||'AED')+'</div></div><div class="subscription-value">'+money(s.subscription_amount,s.currency||'AED')+'<br>'+chip(s.status)+'</div></div>').join(''):'<div class="empty"><div class="empty-icon">◌</div><h3>No subscriptions yet</h3><p class="hint">Explore the portfolio shelf to start your first guided investment.</p><button class="btn btn-primary" onclick="nav(\'portfolios\')">Explore portfolios</button></div>')+'</div>';
}
async function subscriptionDetail(id){
 const d=await req('/subscriptions/'+id),s=d.subscription;
 return '<button class="btn-ghost" onclick="nav(\'subscriptions\')">← Back to subscriptions</button><div class="section-title">Subscription record</div><h2>'+esc(String(s.id).slice(0,8).toUpperCase())+'</h2><div class="card">'+row('Amount',money(s.subscription_amount))+row('Status',chip(s.status))+row('Created',fmtDate(s.created_at))+'</div><div class="card"><div class="section-title">Lifecycle</div>'+((d.events||[]).map(e=>'<div class="doc-row"><span><b>'+esc(e.event_type)+'</b></span><span>'+fmtDate(e.created_at)+'</span></div>').join('')||'<div class="hint">No events recorded.</div>')+'</div>';
}
async function activity(){const xs=await req('/activity');return '<div class="section-title">Activity</div><h2>Your activity log</h2><div class="card">'+(xs.length?xs.map(x=>'<div class="doc-row"><span><b>'+esc(x.action)+'</b><div class="hint">'+esc(x.entity_type)+(x.entity_id?' · '+esc(String(x.entity_id).slice(0,8)):'')+'</div></span><span>'+fmtDate(x.created_at)+'</span></div>').join(''):'<div class="empty"><div class="empty-icon">◌</div><h3>No activity yet</h3><p class="hint">Your suitability, consent and subscription events will appear here.</p></div>')+'</div>'}
function profile(){const c=session.customer||{};return '<div class="section-title">Profile</div><h2>'+esc(c.name||'Investor')+'</h2><div class="grid-2"><div class="card">'+row('Customer ID',esc(c.customerId||'—'))+row('Email',esc(c.email||'—'))+row('Investor type',esc(c.investorType||'—'))+'</div><div class="card">'+row('KYC',chip(c.kycStatus||'—'))+row('AML',chip(c.amlStatus||'—'))+row('Role',esc(c.role||'—'))+'</div></div>'}
function pageLoading(message){
 $('#root').innerHTML='<main><div class="card" style="max-width:720px;margin:12vh auto;text-align:center"><div class="section-title">Guided Portfolios</div><h2>'+esc(message)+'</h2><p class="hint">We are securely loading your workspace.</p><div class="loading-line" aria-hidden="true"><span></span></div></div></main>';
}
function auth(mode){
 const login=mode==='login';
 document.body.insertAdjacentHTML('beforeend','<div class="modal-backdrop" id="modal"><div class="modal"><button class="modal-close" onclick="closeModal()">×</button><div class="section-title">'+(login?'Welcome back':'Open an account')+'</div><h2>'+(login?'Sign in':'Start your journey')+'</h2><form id="authform">'+(login?'':'<div class="field"><label>Full name</label><input id="name" required></div>')+'<div class="field"><label>Email</label><input id="email" type="email" required></div>'+(login?'':'<div class="field"><label>Mobile</label><input id="mobile"></div>')+'<div class="field"><label>Password</label><input id="password" type="password" minlength="8" required></div><button type="submit" class="btn btn-primary btn-block">Continue</button><p class="hint" id="authstatus"></p><p class="hint" id="autherr"></p></form></div></div>');
 $('#authform').onsubmit=async e=>{
  e.preventDefault();
  const btn=e.currentTarget.querySelector('button[type="submit"]');
  const status=$('#authstatus'),err=$('#autherr');
  if(btn.disabled)return;
  btn.disabled=true;
  btn.textContent=login?'Signing in…':'Creating your account…';
  status.textContent=login?'Checking your account securely…':'Setting up your guided investing workspace…';
  err.textContent='';
  try{
   const body=login?{email:$('#email').value,password:$('#password').value}:{full_name:$('#name').value,email:$('#email').value,password:$('#password').value,mobile:$('#mobile').value};
   const r=await req('/auth/'+(login?'login':'register'),{method:'POST',body:JSON.stringify(body)});
   session.token=r.access_token;
   localStorage.setItem('xcompany_token',session.token);
   status.textContent='Account created. Loading your workspace…';
   session.customer=await req('/auth/me');
   closeModal();
   pageLoading(login?'Loading your workspace…':'Setting up your dashboard…');
   toast(login?'Signed in successfully':'Account created successfully','success');
   nav('dashboard');
  }catch(x){
   btn.disabled=false;
   btn.textContent='Continue';
   status.textContent='';
   err.textContent=x.message;
  }
 } 
} 
async function adminPage(){
 const users=await adminReq('/admin/users');
 const managers=users.filter(u=>u.role==='MANAGER').length;
 const pending=users.filter(u=>(u.kycStatus||'PENDING')!=='APPROVED'||(u.amlStatus||'PENDING')!=='APPROVED').length;
 return '<div class="section-title">Administration</div><div class="admin-header"><div><h2>User & access control</h2><p class="lead">Manage investor records, KYC/AML status and role assignment. Portfolio operations belong to the Manager Console.</p></div><span class="status-badge">ADMIN</span></div>'+
 '<div class="metric-grid"><div class="card metric"><div class="section-title">Users</div><h2>'+num(users.length)+'</h2><span class="metric-sub">All customer records</span></div><div class="card metric"><div class="section-title">Managers</div><h2>'+num(managers)+'</h2><span class="metric-sub">Investment operations users</span></div><div class="card metric"><div class="section-title">KYC / AML review</div><h2>'+num(pending)+'</h2><span class="metric-sub">Records not fully approved</span></div></div>'+
 '<div class="card"><div class="section-title">Customer management</div><p class="hint">Role options: INVESTOR, MANAGER, ADMIN. Use MANAGER for investment-team users who operate portfolios, products and corporate actions.</p><div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Customer</th><th>Investor type</th><th>KYC</th><th>AML</th><th>Role</th><th>Update</th></tr></thead><tbody>'+
 users.map(u=>'<tr><td><b>'+esc(u.fullName)+'</b><div class="hint">'+esc(u.email)+' · '+esc(u.customerId)+'</div></td><td>'+esc(u.investorType||'—')+'</td><td><select id="kyc-'+u.id+'"><option'+(u.kycStatus==='PENDING'?' selected':'')+'>PENDING</option><option'+(u.kycStatus==='APPROVED'?' selected':'')+'>APPROVED</option><option'+(u.kycStatus==='REJECTED'?' selected':'')+'>REJECTED</option></select></td><td><select id="aml-'+u.id+'"><option'+(u.amlStatus==='PENDING'?' selected':'')+'>PENDING</option><option'+(u.amlStatus==='APPROVED'?' selected':'')+'>APPROVED</option><option'+(u.amlStatus==='REJECTED'?' selected':'')+'>REJECTED</option></select></td><td><select id="role-'+u.id+'"><option'+(u.role==='INVESTOR'?' selected':'')+'>INVESTOR</option><option'+(u.role==='MANAGER'?' selected':'')+'>MANAGER</option><option'+(u.role==='ADMIN'?' selected':'')+'>ADMIN</option></select></td><td><button class="btn-ghost" onclick="adminUpdateUser(\''+u.id+'\')">Save</button></td></tr>').join('')+
 '</tbody></table></div></div><div class="card"><div class="section-title">Access model</div><div class="grid-3"><div><b>INVESTOR</b><p class="hint">Suitability, subscriptions and portfolio viewing.</p></div><div><b>MANAGER</b><p class="hint">Portfolio construction, products, documents, NAV, versions and corporate actions.</p></div><div><b>ADMIN</b><p class="hint">Customer records, KYC/AML and role administration.</p></div></div></div><button class="btn-ghost" onclick="adminLogout()">Sign out admin</button>';
}

async function managerPage(){
 const tab=state.managerTab||'overview';
 const navs=[['overview','Overview'],['portfolios','Portfolios'],['instruments','Products / Instruments'],['corporate','Corporate Actions'],['documents','Fact Sheets & Documents'],['audit','Governance / Audit']];
 const html='<div class="section-title">Investment Management</div><div class="admin-header"><div><h2>Portfolio Management Console</h2><p class="lead">Build, maintain, govern and publish the investment shelf without engineering involvement.</p></div><span class="status-badge">MANAGER</span></div><div class="admin-shell"><div class="admin-side">'+navs.map(x=>'<div class="admin-side-item '+(tab===x[0]?'active':'')+'" onclick="managerTab(\''+x[0]+'\')">'+x[1]+'</div>').join('')+'</div><div class="admin-main" id="manager-main"></div></div>';
 setTimeout(()=>renderManagerTab(tab),0);
 return html;
}
async function renderManagerTab(tab){
 const main=$('#manager-main'); if(!main)return;
 try{
  if(tab==='overview'){
   const o=await managerReq('/manager/overview');
   main.innerHTML='<div class="section-title">Overview</div><h2>Investment operations</h2><div class="metric-grid"><div class="card metric"><div class="section-title">Portfolios</div><h2>'+num(o.portfolios)+'</h2><span class="metric-sub">'+num(o.activePortfolios)+' active · '+num(o.draftPortfolios)+' draft</span></div><div class="card metric"><div class="section-title">Products</div><h2>'+num(o.instruments)+'</h2><span class="metric-sub">Instrument universe</span></div><div class="card metric"><div class="section-title">Corporate actions</div><h2>'+num(o.corporateActions)+'</h2><span class="metric-sub">'+num(o.pendingCorporateActions)+' pending / processing</span></div><div class="card metric"><div class="section-title">Documents</div><h2>'+num(o.documents)+'</h2><span class="metric-sub">Published investor documents</span></div></div><div class="card"><div class="section-title">Operating model</div><div class="grid-3"><div><b>Build</b><p class="hint">Create portfolio terms, risk, fees and benchmark.</p></div><div><b>Construct</b><p class="hint">Attach products and reconcile asset, sector and geographic weights.</p></div><div><b>Govern</b><p class="hint">Publish fact sheets, record NAV, versions and corporate actions.</p></div></div></div>';
  } else if(tab==='portfolios') await renderManagerPortfolios(main);
  else if(tab==='instruments') await renderManagerInstruments(main);
  else if(tab==='corporate') await renderManagerCorporate(main);
  else if(tab==='documents') await renderManagerDocuments(main);
  else if(tab==='audit') await renderManagerAudit(main);
 }catch(e){main.innerHTML='<div class="card error-card"><div class="section-title">Unable to load</div><h3>'+esc(e.message)+'</h3><button class="btn btn-secondary" onclick="renderManagerTab(\''+tab+'\')">Retry</button></div>'}
}
function managerTab(tab){state.managerTab=tab;document.querySelectorAll('.admin-shell .admin-side-item').forEach(el=>el.classList.toggle('active',el.textContent.toLowerCase().includes(tab==='instruments'?'products / instruments':tab==='corporate'?'corporate actions':tab==='documents'?'fact sheets':tab==='audit'?'governance':' '+tab)));renderManagerTab(tab)}
async function renderManagerPortfolios(main){
 const ps=await managerReq('/manager/portfolios');
 main.innerHTML='<div class="manager-section-head"><div><div class="section-title">Portfolio catalog</div><h2>Investment portfolios</h2><p class="lead">Draft, edit, govern and publish the same data investors see.</p></div><button class="btn btn-primary" onclick="managerNewPortfolio()">+ New portfolio</button></div><div class="card"><div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Name</th><th>Category</th><th>Risk</th><th>Minimum</th><th>Fee</th><th>Status</th><th></th></tr></thead><tbody>'+(ps.length?ps.map(p=>'<tr><td><b>'+esc(p.name)+'</b><div class="hint">'+esc(p.slug)+'</div></td><td>'+esc(p.category)+'</td><td>'+esc(p.riskLevel)+'/5</td><td>'+money(p.minimumInvestment,p.baseCurrency)+'</td><td>'+feePct(p.managementFee)+'</td><td>'+chip(p.status)+'</td><td><button class="btn-ghost" onclick="managerEditPortfolio(\''+p.id+'\')">Edit</button></td></tr>').join(''):'<tr><td colspan="7" style="padding:28px;text-align:center" class="hint">No portfolios yet.</td></tr>')+'</tbody></table></div></div>';
}
function managerEsc(v){return esc(v??'')}
function managerRowsHtml(kind,items){return (items||[]).map((x)=>managerRow(kind,x)).join('')}
function managerRow(kind,x){
 if(kind==='holdings') return '<div class="holding-editor-row holdings-type"><input placeholder="Product / holding name" value="'+managerEsc(x.instrumentName)+'" data-field="name"><input placeholder="Ticker / type" value="'+managerEsc(x.ticker||x.instrumentType)+'" data-field="type"><input type="number" min="0" max="100" step="0.1" value="'+num(x.targetWeight)+'" data-field="weight"><select data-field="instrument" data-selected="'+managerEsc(x.instrumentId||'')+'"></select><button class="icon-btn" onclick="this.closest(\'.holding-editor-row\').remove();managerUpdateTotals()">×</button></div>';
 return '<div class="holding-editor-row"><input placeholder="'+(kind==='asset'?'Asset class':kind==='sector'?'Sector':'Region')+'" value="'+managerEsc(x.label)+'" data-field="label"><input type="number" min="0" max="100" step="0.1" value="'+num(x.targetWeight)+'" data-field="weight"><button class="icon-btn" onclick="this.closest(\'.holding-editor-row\').remove();managerUpdateTotals()">×</button></div>';
}
async function managerEditPortfolio(id){const d=await managerReq('/manager/portfolios/'+id);state.managerInstruments=await managerReq('/manager/instruments');managerRenderEditor(d)}
function managerNewPortfolio(){state.managerEditing=null;state.managerInstruments=[];managerRenderEditor({portfolio:{id:null,name:'',slug:'',vehicleType:'MODEL_PORTFOLIO',category:'BALANCED',objective:'',riskLevel:3,minimumInvestment:1000,managementFee:0.75,performanceFee:0,costBasisMethod:'AVERAGE_COST',benchmark:'',baseCurrency:'AED',liquidityTerms:'Daily',status:'DRAFT'},composition:{assets:[],sectors:[],geography:[],holdings:[]},performance:[],documents:[]})}
function managerRenderEditor(d){
 const p=d.portfolio,c=d.composition||{},main=$('#manager-main'); if(!main)return;
 main.innerHTML='<div class="manager-section-head"><div><button class="btn-ghost" onclick="managerTab(\'portfolios\')">← Portfolio catalog</button><div class="section-title">'+(p.id?'Edit portfolio':'New portfolio')+'</div><h2>'+esc(p.name||'New portfolio')+'</h2></div><span class="status-badge">'+esc(p.status)+'</span></div>'+
 '<div class="card"><div class="section-title">Portfolio terms</div><div class="editor-grid"><div class="field"><label>Name</label><input id="mp-name" value="'+managerEsc(p.name)+'"></div><div class="field"><label>Slug</label><input id="mp-slug" value="'+managerEsc(p.slug)+'" '+(p.id?'disabled':'')+' pattern="[a-z0-9-]+"></div><div class="field"><label>Category</label><input id="mp-category" value="'+managerEsc(p.category)+'"></div><div class="field"><label>Risk level (1–5)</label><input id="mp-risk" type="number" min="1" max="5" value="'+num(p.riskLevel)+'"></div><div class="field field-full"><label>Objective</label><textarea id="mp-objective" rows="3">'+managerEsc(p.objective)+'</textarea></div><div class="field field-full"><label>Investment strategy</label><textarea id="mp-strategy" rows="4" placeholder="Mandate, selection process, concentration limits, liquidity approach, risk controls…">'+managerEsc(p.strategy||'')+'</textarea></div><div class="field"><label>Investment style</label><input id="mp-style" value="'+managerEsc(p.investmentStyle||'ACTIVE')+'"></div><div class="field"><label>Shariah status</label><select id="mp-shariah"><option value="NOT_APPLICABLE">Not applicable</option><option value="COMPLIANT" '+(p.shariahStatus==='COMPLIANT'?'selected':'')+'>Shariah compliant</option><option value="PENDING_REVIEW" '+(p.shariahStatus==='PENDING_REVIEW'?'selected':'')+'>Pending review</option></select></div><div class="field"><label>Distribution policy</label><input id="mp-distribution" value="'+managerEsc(p.distributionPolicy||'ACCUMULATING')+'"></div><div class="field"><label>Review frequency</label><input id="mp-review" value="'+managerEsc(p.reviewFrequency||'QUARTERLY')+'"></div><div class="field"><label>Target horizon (years)</label><input id="mp-horizon" type="number" min="1" max="50" value="'+(p.targetHorizonYears?num(p.targetHorizonYears):'')+'"></div><div class="field"><label>Inception date</label><input id="mp-inception" type="date" value="'+(p.inceptionDate?String(p.inceptionDate).slice(0,10):'')+'"></div><div class="field"><label>Status</label><div class="hint" style="padding:11px 0">'+esc(p.status==='ACTIVE'?'ACTIVE — controlled publication':'DRAFT — not visible to investors until published')+'</div></div><div class="field"><label>Minimum investment</label><input id="mp-min" type="number" min="0" value="'+num(p.minimumInvestment)+'"></div><div class="field"><label>Management fee %</label><input id="mp-fee" type="number" step="0.01" min="0" value="'+num(p.managementFee)+'"></div><div class="field"><label>Performance fee %</label><input id="mp-perf" type="number" step="0.01" min="0" value="'+num(p.performanceFee)+'"></div><div class="field"><label>Vehicle type</label><input id="mp-vehicle" value="'+managerEsc(p.vehicleType)+'"></div><div class="field"><label>Base currency</label><input id="mp-currency" maxlength="3" value="'+managerEsc(p.baseCurrency)+'"></div><div class="field"><label>Liquidity</label><input id="mp-liquidity" value="'+managerEsc(p.liquidityTerms)+'"></div><div class="field"><label>Benchmark</label><input id="mp-benchmark" value="'+managerEsc(p.benchmark||'')+'"></div><div class="field"><label>Cost basis</label><input id="mp-cost" value="'+managerEsc(p.costBasisMethod)+'"></div></div></div>'+
 managerCompositionCard('asset','Asset allocation',c.assets)+managerCompositionCard('sector','Sector breakdown',c.sectors)+managerCompositionCard('geo','Geographic breakdown',c.geography)+
 '<div class="card"><div class="section-title">Products / Holdings</div><p class="hint">Attach products to the portfolio and set target weights.</p><div id="mp-holdings">'+managerRowsHtml('holdings',c.holdings)+'</div><button class="btn btn-ghost btn-small" onclick="managerAddRow(\'holdings\')">+ Add product</button><div id="mp-holdings-total" class="allocation-summary"></div></div>'+
 '<div class="card"><div class="section-title">NAV / Performance</div><div class="grid-4"><div class="field"><label>NAV</label><input id="mp-nav" type="number" min="0" step="0.0001" value="'+(d.performance?.length?num(d.performance[d.performance.length-1].nav):100)+'"></div><div class="field"><label>Daily return</label><input id="mp-daily" type="number" step="0.0001" value="0"></div><div class="field"><label>Monthly return</label><input id="mp-monthly" type="number" step="0.0001" value="0"></div><div class="field"><label>YTD return</label><input id="mp-ytd" type="number" step="0.0001" value="0"></div></div><button class="btn btn-ghost btn-small" onclick="managerAddNav(\''+(p.id||'')+'\')">Record NAV observation</button></div>'+
 '<div class="card"><div class="section-title">Fact sheets & documents</div><div id="mp-docs">'+((d.documents||[]).map(x=>'<div class="doc-row"><span><b>'+esc(x.documentType)+'</b> · v'+esc(x.version)+'</span><button class="btn-ghost" onclick="managerOpenDocument(\''+x.id+'\')">Open</button></div>').join('')||'<div class="hint">No documents published.</div>')+'</div><div class="grid-3"><div class="field"><label>Document type</label><input id="mp-doc-type" value="FACT_SHEET"></div><div class="field"><label>Version</label><input id="mp-doc-version" value="1.0"></div><div class="field"><label>PDF upload</label><input id="mp-doc-file" type="file" accept="application/pdf"></div></div><div class="field"><label>Legacy / external URL (optional)</label><input id="mp-doc-url" placeholder="Use only when the document is hosted elsewhere"></div><button class="btn btn-ghost btn-small" onclick="managerAddDocument(\''+(p.id||'')+'\')">Upload & publish document</button></div>'+
 '<div class="card"><div class="section-title">Version & publication governance</div><p class="hint">A portfolio remains private until a second Manager approves a version and the publication checklist passes.</p><div id="mp-readiness" class="governance-checklist">Loading publication checklist…</div><div id="mp-versions" style="margin-top:16px;"></div><div class="btnrow"><button class="btn btn-ghost btn-small" '+(p.id?'':'disabled')+' onclick="managerCreateVersion(\''+(p.id||'')+'\')">Create draft version</button><button class="btn btn-primary btn-small" '+(p.id?'':'disabled')+' onclick="managerPublishPortfolio(\''+(p.id||'')+'\')">Publish to investors</button></div></div>'+
 '<div class="btnrow"><button class="btn btn-primary" onclick="managerSavePortfolio(\''+(p.id||'')+'\')">'+(p.id?'Save changes':'Create portfolio')+'</button><button class="btn btn-ghost" onclick="managerTab(\'portfolios\')">Cancel</button></div>';
 managerHydrateInstrumentSelectors();managerUpdateTotals();if(p.id)managerLoadReadiness(p.id);
}
function managerCompositionCard(kind,title,items){return '<div class="card"><div class="section-title">'+title+'</div><div id="mp-'+kind+'">'+managerRowsHtml(kind,items)+'</div><button class="btn btn-ghost btn-small" onclick="managerAddRow(\''+kind+'\')">+ Add '+(kind==='asset'?'asset class':kind==='sector'?'sector':'region')+'</button><div id="mp-'+kind+'-total" class="allocation-summary"></div></div>'}
function managerAddRow(kind){const holder=$('#mp-'+kind);if(!holder)return;holder.insertAdjacentHTML('beforeend',managerRow(kind,kind==='holdings'?{instrumentName:'',instrumentType:'',ticker:'',instrumentId:'',targetWeight:0}:{label:'',targetWeight:0}));managerHydrateInstrumentSelectors();managerUpdateTotals()}
function managerHydrateInstrumentSelectors(){document.querySelectorAll('#mp-holdings select[data-field="instrument"]').forEach(sel=>{const selected=sel.dataset.selected||sel.value||'';sel.innerHTML='<option value="">Select instrument</option>'+(state.managerInstruments||[]).map(x=>'<option value="'+x.id+'" '+(String(selected)===String(x.id)?'selected':'')+'>'+esc(x.name)+(x.symbol?' · '+esc(x.symbol):'')+'</option>').join('')})}
function managerCollect(kind){const map={asset:'mp-asset',sector:'mp-sector',geo:'mp-geo',holdings:'mp-holdings'},root=$('#'+map[kind]);if(!root)return[];return Array.from(root.querySelectorAll('.holding-editor-row')).map(r=>{const w=num(r.querySelector('[data-field="weight"]')?.value);if(kind==='holdings')return{instrument_id:r.querySelector('[data-field="instrument"]')?.value||null,instrument_name:r.querySelector('[data-field="name"]')?.value.trim()||'',instrument_type:r.querySelector('[data-field="type"]')?.value.trim()||'OTHER',ticker:null,target_weight:w};return{dimension:kind==='asset'?'ASSET':kind==='sector'?'SECTOR':'GEO',label:r.querySelector('[data-field="label"]')?.value.trim()||'',target_weight:w}})}
function managerUpdateTotals(){[['asset','mp-asset-total'],['sector','mp-sector-total'],['geo','mp-geo-total'],['holdings','mp-holdings-total']].forEach(([k,id])=>{const rows=managerCollect(k),total=Math.round(rows.reduce((a,x)=>a+num(x.target_weight),0)*10)/10,el=$('#'+id);if(!el)return;el.textContent=rows.length?'Total: '+total+'%'+(Math.abs(total-100)<0.2?' ✓ Balanced':' · should total 100%'):'No items added yet.';el.className='allocation-summary'+(rows.length&&Math.abs(total-100)>=0.2?' warn':'')})}
async function managerSavePortfolio(id){
 const body={name:$('#mp-name').value.trim(),slug:id?undefined:$('#mp-slug').value.trim(),category:$('#mp-category').value.trim(),objective:$('#mp-objective').value.trim(),strategy:$('#mp-strategy').value.trim(),investment_style:$('#mp-style').value.trim(),shariah_status:$('#mp-shariah').value,distribution_policy:$('#mp-distribution').value.trim(),review_frequency:$('#mp-review').value.trim(),target_horizon_years:$('#mp-horizon').value?num($('#mp-horizon').value):null,inception_date:$('#mp-inception').value?$('#mp-inception').value:null,risk_level:num($('#mp-risk').value),minimum_investment:num($('#mp-min').value),management_fee:num($('#mp-fee').value),performance_fee:num($('#mp-perf').value),vehicle_type:$('#mp-vehicle').value.trim(),base_currency:$('#mp-currency').value.trim().toUpperCase(),liquidity_terms:$('#mp-liquidity').value.trim(),benchmark:$('#mp-benchmark').value.trim()||null,cost_basis_method:$('#mp-cost').value.trim(),status:$('#mp-status').value,composition:{allocations:[...managerCollect('asset'),...managerCollect('sector'),...managerCollect('geo')],holdings:managerCollect('holdings')}};
 try{if(!id){await managerReq('/manager/portfolios',{method:'POST',body:JSON.stringify(body)})}else{delete body.slug;const composition=body.composition;delete body.composition;await managerReq('/manager/portfolios/'+id,{method:'PATCH',body:JSON.stringify(body)});await managerReq('/manager/portfolios/'+id+'/composition',{method:'PUT',body:JSON.stringify(composition)})}toast('Portfolio saved successfully','success');managerTab('portfolios')}catch(e){toast(e.message,'error')}
}
async function managerAddNav(id){if(!id)return toast('Save the portfolio first','warning');try{await managerReq('/manager/portfolios/'+id+'/performance',{method:'POST',body:JSON.stringify({nav:num($('#mp-nav').value),daily_return:num($('#mp-daily').value),monthly_return:num($('#mp-monthly').value),ytd_return:num($('#mp-ytd').value)})});toast('NAV observation recorded','success')}catch(e){toast(e.message,'error')}}
async function managerAddDocument(id){
 if(!id)return toast('Save the portfolio first','warning');
 try{
  const file=$('#mp-doc-file')?.files?.[0];
  let fileUrl=$('#mp-doc-url')?.value.trim()||'';
  if(file){
   if(file.type!=='application/pdf')throw Error('Only PDF documents are supported');
   if(file.size>10*1024*1024)throw Error('Maximum document size is 10 MB');
   const q='/manager/portfolios/'+id+'/documents/upload-url?filename='+encodeURIComponent(file.name)+'&content_type='+encodeURIComponent(file.type);
   const signed=await managerReq(q);
   if(!signed.signedUrl)throw Error('Storage upload URL was not generated');
   const up=await fetch(signed.signedUrl,{method:'PUT',body:file,headers:{'content-type':file.type,'x-upsert':'false','cache-control':'max-age=3600'}});
   if(!up.ok)throw Error('Document upload failed');
   fileUrl='storage://'+signed.bucket+'/'+signed.path;
  }
  if(!fileUrl)throw Error('Choose a PDF or provide an external URL');
  await managerReq('/manager/portfolios/'+id+'/documents',{method:'POST',body:JSON.stringify({document_type:$('#mp-doc-type').value.trim(),version:$('#mp-doc-version').value.trim(),file_url:fileUrl,published:true})});
  toast('Document uploaded and published','success');managerEditPortfolio(id)
 }catch(e){toast(e.message,'error')}
}
async function managerOpenDocument(id){
 try{
  const r=await managerReq('/manager/documents/'+id+'/signed-url');
  if(!r.signedUrl)throw Error('Document URL unavailable');
  window.open(r.signedUrl,'_blank','noopener')
 }catch(e){toast(e.message,'error')}
}
async function managerCreateVersion(id){const notes=prompt('Version notes / release rationale:','');try{await managerReq('/manager/portfolios/'+id+'/versions',{method:'POST',body:JSON.stringify({notes:notes||''})});toast('Draft version created','success');managerEditPortfolio(id)}catch(e){toast(e.message,'error')}}
async function managerLoadReadiness(id){
 if(!id)return;
 try{
  const r=await managerReq('/manager/portfolios/'+id+'/readiness');
  const labels={strategy:'Investment strategy',assetAllocation:'Asset allocation',holdings:'Holdings = 100%',activeVersion:'Approved active version',factSheet:'Published FACT_SHEET'};
  const el=$('#mp-readiness');
  if(el)el.innerHTML=Object.entries(labels).map(([k,v])=>'<div class="check-row '+(r.checks[k]?'check-ok':'check-no')+'"><span>'+(r.checks[k]?'✓':'○')+'</span><b>'+v+'</b><small>'+(r.checks[k]?'Complete':'Action required')+'</small></div>').join('')+(r.ready?'<div class="publish-ready">Ready for controlled publication.</div>':'<div class="hint">Complete all checks before publishing.</div>');
  const vs=await managerReq('/manager/versions?portfolio_id='+encodeURIComponent(id));
  const ve=$('#mp-versions');
  if(ve)ve.innerHTML='<div class="section-title">Version history</div>'+((vs||[]).length?vs.map(v=>'<div class="version-row"><div><b>v'+esc(v.versionNumber)+'</b> · '+esc(v.status)+'<div class="hint">'+esc(v.notes||'No notes')+'</div></div><div>'+(v.status==='DRAFT'&&String(v.createdBy)!==String(session.customer?.id)?'<button class="btn-ghost btn-small" onclick="managerApproveVersion(\''+v.portfolioId+'\',\''+v.id+'\')">Approve</button>':'')+'</div></div>').join(''):'<div class="hint">No versions created yet.</div>');
 }catch(e){const el=$('#mp-readiness');if(el)el.textContent=e.message}
}
async function managerApproveVersion(portfolioId,versionId){try{await managerReq('/manager/portfolios/'+portfolioId+'/versions/'+versionId+'/approve',{method:'POST'});toast('Version approved','success');managerLoadReadiness(portfolioId)}catch(e){toast(e.message,'error')}}
async function managerPublishPortfolio(id){try{await managerReq('/manager/portfolios/'+id+'/publish',{method:'POST'});toast('Portfolio published to investors','success');managerEditPortfolio(id)}catch(e){toast(e.message,'error')}}
async function renderManagerInstruments(main){
 const xs=await managerReq('/manager/instruments');
 main.innerHTML='<div class="manager-section-head"><div><div class="section-title">Investment products</div><h2>Products / instruments</h2><p class="lead">Maintain the approved product universe used by portfolio construction.</p></div><button class="btn btn-primary" onclick="managerShowInstrumentForm()">+ Add product</button></div><div id="instrument-form"></div><div class="card"><div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Name</th><th>Symbol</th><th>Type</th><th>Asset class</th><th>ISIN</th><th>Status</th></tr></thead><tbody>'+(xs.length?xs.map(x=>'<tr><td><b>'+esc(x.name)+'</b></td><td>'+esc(x.symbol||'—')+'</td><td>'+esc(x.instrumentType)+'</td><td>'+esc(x.assetClass)+'</td><td>'+esc(x.isin||'—')+'</td><td>'+chip(x.status)+'</td></tr>').join(''):'<tr><td colspan="6" class="hint" style="padding:28px;text-align:center">No products yet.</td></tr>')+'</tbody></table></div></div>';
}
function managerShowInstrumentForm(){const holder=$('#instrument-form');if(!holder)return;holder.innerHTML='<div class="card"><div class="section-title">Add investment product</div><div class="editor-grid"><div class="field"><label>Name</label><input id="mi-name"></div><div class="field"><label>Symbol</label><input id="mi-symbol"></div><div class="field"><label>Instrument type</label><input id="mi-type" value="FUND"></div><div class="field"><label>Asset class</label><input id="mi-asset" value="Equity"></div><div class="field"><label>Currency</label><input id="mi-currency" maxlength="3" value="AED"></div><div class="field"><label>ISIN</label><input id="mi-isin"></div></div><button class="btn btn-primary" onclick="managerCreateInstrument()">Save product</button></div>'}
async function managerCreateInstrument(){try{await managerReq('/manager/instruments',{method:'POST',body:JSON.stringify({name:$('#mi-name').value.trim(),symbol:$('#mi-symbol').value.trim()||null,instrument_type:$('#mi-type').value.trim(),asset_class:$('#mi-asset').value.trim(),currency:$('#mi-currency').value.trim().toUpperCase(),isin:$('#mi-isin').value.trim()||null,status:'ACTIVE'})});toast('Product created','success');managerTab('instruments')}catch(e){toast(e.message,'error')}}
async function renderManagerCorporate(main){
 const xs=await managerReq('/manager/corporate-actions');
 const rows=xs.map(a=>'<tr><td><b>'+esc(a.actionType)+'</b><div class="hint">'+esc(a.description||'—')+'</div></td><td>'+fmtDate(a.exDate)+'</td><td>'+fmtDate(a.effectiveDate)+'</td><td>'+chip(a.status)+'</td><td>'+((a.status==='DRAFT'&&String(a.createdBy)!==String(session.customer?.id))?'<button class="btn-ghost" onclick="managerApproveCA(\''+a.id+'\')">Approve</button> ':'')+((a.status==='APPROVED')?'<button class="btn-ghost" onclick="managerExecuteCA(\''+a.id+'\')">Execute</button> ':'')+'<button class="btn-ghost" onclick="managerCAEvents(\''+a.id+'\')">Events</button></td></tr>').join('');
 main.innerHTML='<div class="manager-section-head"><div><div class="section-title">Corporate actions</div><h2>Corporate actions engine</h2><p class="lead">Splits, dividends, rights issues and mergers with approval and execution records.</p></div></div>'+
 '<div class="card"><div class="section-title">Create action</div><div class="editor-grid"><div class="field"><label>Instrument ID</label><input id="ca-instrument" placeholder="UUID from Products"></div><div class="field"><label>Action type</label><select id="ca-type"><option>SPLIT</option><option>REVERSE_SPLIT</option><option>CASH_DIVIDEND</option><option>STOCK_DIVIDEND</option><option>RIGHTS_ISSUE</option><option>MERGER</option></select></div><div class="field"><label>Ex date</label><input id="ca-ex" type="datetime-local"></div><div class="field"><label>Effective date</label><input id="ca-effective" type="datetime-local"></div><div class="field"><label>Record date</label><input id="ca-record" type="datetime-local"></div><div class="field"><label>Payment date</label><input id="ca-payment" type="datetime-local"></div><div class="field"><label>Ratio numerator</label><input id="ca-num" type="number" step="0.00000001"></div><div class="field"><label>Ratio denominator</label><input id="ca-den" type="number" step="0.00000001"></div><div class="field"><label>Dividend / share</label><input id="ca-div" type="number" min="0" step="0.00000001"></div><div class="field"><label>Subscription price</label><input id="ca-price" type="number" min="0" step="0.00000001"></div><div class="field"><label>Replacement instrument ID</label><input id="ca-replacement"></div><div class="field"><label>Exchange ratio</label><input id="ca-exchange" type="number" step="0.00000001"></div><div class="field field-full"><label>Description</label><textarea id="ca-desc" rows="2"></textarea></div></div><button class="btn btn-primary" onclick="managerCreateCA()">Create draft action</button></div>'+
 '<div class="card"><div class="section-title">Action register</div><div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Action</th><th>Ex date</th><th>Effective</th><th>Status</th><th>Action</th></tr></thead><tbody>'+(rows||'<tr><td colspan="5" class="hint" style="padding:28px;text-align:center">No corporate actions yet.</td></tr>')+'</tbody></table></div></div>';
}
function caDate(id){const v=$('#'+id)?.value;return v?new Date(v).toISOString():null}
async function managerCreateCA(){
 try{const payload={instrument_id:$('#ca-instrument').value,action_type:$('#ca-type').value,ex_date:caDate('ca-ex'),effective_date:caDate('ca-effective'),record_date:caDate('ca-record'),payment_date:caDate('ca-payment'),ratio_numerator:$('#ca-num').value?num($('#ca-num').value):null,ratio_denominator:$('#ca-den').value?num($('#ca-den').value):null,dividend_per_share:$('#ca-div').value?num($('#ca-div').value):null,subscription_price:$('#ca-price').value?num($('#ca-price').value):null,replacement_instrument_id:$('#ca-replacement').value||null,exchange_ratio:$('#ca-exchange').value?num($('#ca-exchange').value):null,description:$('#ca-desc').value.trim()};await managerReq('/manager/corporate-actions',{method:'POST',body:JSON.stringify(payload)});toast('Corporate action created as DRAFT','success');managerTab('corporate')}catch(e){toast(e.message,'error')}}
async function managerApproveCA(id){try{await managerReq('/manager/corporate-actions/'+id+'/approve',{method:'POST'});toast('Corporate action approved','success');managerTab('corporate')}catch(e){toast(e.message,'error')}}
async function managerExecuteCA(id){try{const r=await managerReq('/manager/corporate-actions/'+id+'/execute',{method:'POST'});toast('Corporate action executed · '+num(r.eventsProcessed)+' events','success');managerTab('corporate')}catch(e){toast(e.message,'error')}}
async function managerCAEvents(id){try{const r=await managerReq('/manager/corporate-actions/'+id+'/events');alert(r.length?JSON.stringify(r,null,2):'No events recorded.')}catch(e){toast(e.message,'error')}}
async function renderManagerDocuments(main){
 const ps=await managerReq('/manager/portfolios');
 main.innerHTML='<div class="section-title">Fact sheets & documents</div><h2>Published documents</h2><p class="lead">Open a portfolio to publish a fact sheet, KID or other investor-facing document.</p><div class="card">'+ps.map(p=>'<div class="subscription-row" onclick="managerEditPortfolio(\''+p.id+'\')"><div><b>'+esc(p.name)+'</b><div class="hint">'+esc(p.category)+' · '+esc(p.status)+'</div></div><span class="btn-ghost">Open editor →</span></div>').join('')+'</div>';
}
async function renderManagerAudit(main){
 const xs=await managerReq('/manager/audit');
 main.innerHTML='<div class="section-title">Governance</div><h2>Change log</h2><p class="lead">Audit records for portfolio and investment operations.</p><div class="card">'+(xs.length?xs.map(x=>'<div class="audit-row"><span><b>'+esc(x.action||'—')+'</b><div class="hint">'+esc(x.entity_type||'—')+(x.entity_id?' · '+esc(String(x.entity_id).slice(0,8)):'')+'</div></span><span class="t">'+fmtDate(x.created_at)+'</span></div>').join(''):'<div class="hint">No manager activity yet.</div>')+'</div>';
}
function managerReq(path,opt={}){
 return (async()=>{const r=await fetch(API+path,{...opt,headers:{'Content-Type':'application/json',...(session.token?{Authorization:'Bearer '+session.token}:{}),...(opt.headers||{})}});let d={};try{d=await r.json()}catch(e){}if(!r.ok){if(r.status===401||r.status===403){localStorage.removeItem('xcompany_token');session.token=null;session.customer=null;state.route='landing'}throw Error(d.detail||d.message||'Request failed')}return d})()
}
function adminAuth(){
 document.body.insertAdjacentHTML('beforeend','<div class="modal-backdrop" id="modal"><div class="modal"><button class="modal-close" onclick="closeModal()">×</button><div class="section-title">Restricted access</div><h2>Admin sign in</h2><form id="adminform"><div class="field"><label>Username</label><input id="admin-user" autocomplete="username" required></div><div class="field"><label>Password</label><input id="admin-pass" type="password" autocomplete="current-password" required></div><button class="btn btn-primary btn-block">Sign in</button><p class="hint" id="adminerr"></p></form></div></div>');
 $('#adminform').onsubmit=async e=>{e.preventDefault();const b=e.currentTarget.querySelector('button');const err=$('#adminerr');b.disabled=true;b.textContent='Signing in…';try{const r=await fetch(API+'/admin/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:$('#admin-user').value,password:$('#admin-pass').value})});let d={};try{d=await r.json()}catch(x){}if(!r.ok)throw Error(d.detail||'Admin sign in failed');adminSession.token=d.access_token;localStorage.setItem('xcompany_admin_token',adminSession.token);adminSession.principal=await adminReq('/admin/auth/me');closeModal();state.route='admin';await render();toast('Admin signed in','success')}catch(x){err.textContent=x.message;b.disabled=false;b.textContent='Sign in'}};
}
function adminLogout(){localStorage.removeItem('xcompany_admin_token');adminSession.token=null;adminSession.principal=null;state.route='landing';toast('Admin signed out','info');nav('landing')}
async function adminCreatePortfolio(e){
 e.preventDefault();const b=e.currentTarget.querySelector('button[type="submit"]'),st=$('#portfolio-form-status');b.disabled=true;b.textContent='Creating…';st.textContent='';
 try{await adminReq('/admin/portfolios',{method:'POST',body:JSON.stringify({name:$('#p-name').value,slug:$('#p-slug').value,category:$('#p-category').value,objective:$('#p-objective').value,risk_level:num($('#p-risk').value),minimum_investment:num($('#p-min').value),management_fee:num($('#p-fee').value),performance_fee:num($('#p-perf').value),benchmark:$('#p-benchmark').value||null,base_currency:$('#p-currency').value.toUpperCase(),liquidity_terms:$('#p-liquidity').value,status:$('#p-status').value,primary_allocation:num($('#p-allocation').value)})});st.textContent='Portfolio created.';await render();toast('Portfolio created successfully','success')}catch(x){st.textContent=x.message;b.disabled=false;b.textContent='Create portfolio'}
}
async function adminTogglePortfolio(id,status){
 try{await adminReq('/admin/portfolios/'+id,{method:'PATCH',body:JSON.stringify({status})});await render();toast(status==='ACTIVE'?'Portfolio activated':'Portfolio archived','success')}catch(e){toast(e.message,'error')}
}
async function adminUpdateUser(id){
 try{await adminReq('/admin/users/'+id,{method:'PATCH',body:JSON.stringify({kyc_status:$('#kyc-'+id).value,aml_status:$('#aml-'+id).value,role:$('#role-'+id).value})});toast('Customer updated','success');await render()}catch(e){toast(e.message,'error')}
}

function closeModal(){$('#modal')?.remove()}
function logout(){localStorage.removeItem('xcompany_token');session.token=null;session.customer=null;toast('Signed out','info');nav('landing')}
window.nav=nav;window.auth=auth;window.adminAuth=adminAuth;window.adminLogout=adminLogout;window.adminUpdateUser=adminUpdateUser;window.managerTab=managerTab;window.managerNewPortfolio=managerNewPortfolio;window.managerEditPortfolio=managerEditPortfolio;window.managerAddRow=managerAddRow;window.managerUpdateTotals=managerUpdateTotals;window.managerSavePortfolio=managerSavePortfolio;window.managerAddNav=managerAddNav;window.managerAddDocument=managerAddDocument;window.managerOpenDocument=managerOpenDocument;window.managerCreateVersion=managerCreateVersion;window.managerApproveVersion=managerApproveVersion;window.managerPublishPortfolio=managerPublishPortfolio;window.managerShowInstrumentForm=managerShowInstrumentForm;window.managerCreateInstrument=managerCreateInstrument;window.managerCreateCA=managerCreateCA;window.managerApproveCA=managerApproveCA;window.managerExecuteCA=managerExecuteCA;window.managerCAEvents=managerCAEvents;window.closeModal=closeModal;window.logout=logout;window.suit=suit;window.simulate=simulate;window.subscribe=subscribe;window.confirmSubscribe=confirmSubscribe;window.render=render;
boot();
})();