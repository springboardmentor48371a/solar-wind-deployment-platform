import React, { Component, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route, NavLink, Navigate, useNavigate } from "react-router-dom";
import { Sun, Wind, LayoutDashboard, MapPinned, FolderKanban, FileBarChart, Bell, Settings, LogOut, Plus, ArrowRight, ShieldCheck, Zap, TrendingUp, Activity, Search, Menu, X, Download, Brain, Trophy } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, CartesianGrid } from "recharts";
import "./styles.css";

const API = "http://localhost:8000";
const n = (v, fallback = 0) => {
  const x = Number(v);
  return Number.isFinite(x) ? x : fallback;
};
const fmt = (v, digits = 1) => n(v).toFixed(digits);

async function api(path, options = {}) {
  const token = localStorage.getItem("token");
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  let res;
  try {
    res = await fetch(API + path, { ...options, headers });
  } catch {
    throw new Error("Cannot connect to the backend. Start FastAPI on http://localhost:8000 and try again.");
  }
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try { msg = (await res.json()).detail || msg; } catch {}
    if (res.status === 401 && !["/login", "/register"].includes(window.location.pathname)) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    throw new Error(msg);
  }
  return res.json();
}

class ErrorBoundary extends Component {
  state = { hasError: false, message: "" };
  static getDerivedStateFromError(error) { return { hasError: true, message: error?.message || "Unexpected application error" }; }
  componentDidCatch(error) { console.error("UI error:", error); }
  render() {
    if (!this.state.hasError) return this.props.children;
    return <div className="app-error"><div><h1>Something went wrong</h1><p>{this.state.message}</p><button className="primary" onClick={() => window.location.reload()}>Reload application</button></div></div>;
  }
}

function Auth({ mode }) {
  const nav = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", role: "Renewable Energy Planner" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const register = mode === "register";
  const submit = async e => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      const body = register ? form : { email: form.email, password: form.password };
      const data = await api(register ? "/auth/register" : "/auth/login", { method: "POST", body: JSON.stringify(body) });
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      nav("/dashboard", { replace: true });
    } catch (err) { setError(err.message); } finally { setLoading(false); }
  };
  return <div className="auth-page"><div className="auth-left">
    <div className="brand"><div className="brand-mark"><Sun size={22}/></div><span className="brand-name">Solar and Wind Prediction</span></div>
    <div className="auth-copy"><div className="eyebrow">SOLAR AND WIND PREDICTION</div><h1>Plan smarter.<br/><em>Deploy cleaner.</em></h1><p>Turn environmental, geographic and infrastructure data into renewable deployment decisions.</p><div className="mini-stats"><span><strong>35%</strong> resource weighting</span><span><strong>Random Forest</strong> ML</span></div></div>
  </div><div className="auth-card-wrap"><div className="auth-card">
    <div className="mobile-brand brand"><div className="brand-mark"><Sun size={18}/></div><span className="brand-name">Solar and Wind Prediction</span></div>
    <h2>{register ? "Create your account" : "Welcome back"}</h2><p className="muted">{register ? "Start building renewable site intelligence." : "Sign in to continue to your deployment workspace."}</p>
    {error && <div className="error">{error}</div>}
    <form onSubmit={submit}>
      {register && <><label>Full name<input value={form.full_name} onChange={e => setForm({...form, full_name:e.target.value})} placeholder="Your name" required/></label><label>Role<select value={form.role} onChange={e => setForm({...form, role:e.target.value})}><option>Renewable Energy Planner</option><option>GIS Analyst</option><option>Project Manager</option><option>Administrator</option></select></label></>}
      <label>Email address<input type="email" value={form.email} onChange={e => setForm({...form,email:e.target.value})} placeholder="you@example.com" required/></label>
      <label>Password<input type="password" value={form.password} onChange={e => setForm({...form,password:e.target.value})} placeholder="Minimum 6 characters" required minLength="6"/></label>
      <button className="primary wide" disabled={loading}>{loading ? "Please wait..." : register ? "Create account" : "Sign in"}<ArrowRight size={17}/></button>
    </form>
    <div className="auth-switch">{register ? "Already have an account?" : "Don't have an account?"} <button onClick={() => nav(register ? "/login" : "/register")}>{register ? "Sign in" : "Create one"}</button></div>
    <div className="security"><ShieldCheck size={16}/> Passwords are securely hashed before storage.</div>
  </div></div></div>;
}

function AppShell({ children }) {
  const nav = useNavigate();
  const [user, setUser] = useState(() => { try { return JSON.parse(localStorage.getItem("user") || "null"); } catch { return null; } });
  const [open, setOpen] = useState(false);
  const logout = () => { localStorage.clear(); setUser(null); nav("/login", { replace:true }); };
  const links = [["/dashboard","Dashboard",LayoutDashboard],["/projects","Projects & Sites",FolderKanban],["/recommendations","Recommendations",MapPinned],["/analytics","Analytics",TrendingUp],["/ml-prediction","ML Prediction",Brain],["/reports","Reports",FileBarChart]];
  return <div className="app"><aside className={open ? "open" : ""}><div className="brand"><div className="brand-mark"><Sun size={20}/></div><span className="brand-name">Solar and Wind Prediction</span></div>
    <div className="side-label">WORKSPACE</div>{links.map(([to,label,I]) => <NavLink onClick={() => setOpen(false)} className={({isActive}) => isActive ? "active" : ""} to={to} key={to}><I size={18}/>{label}</NavLink>)}
    <div className="side-label">SYSTEM</div><NavLink onClick={() => setOpen(false)} to="/profile"><Settings size={18}/>Profile</NavLink><div className="side-bottom"><div className="user-mini"><div className="avatar">{(user?.full_name || "U")[0]}</div><div><strong>{user?.full_name || "User"}</strong><small>{user?.role || "Planner"}</small></div></div><button className="logout" onClick={logout}><LogOut size={17}/></button></div>
  </aside><main><header><button className="menu-btn" onClick={() => setOpen(!open)}>{open ? <X/> : <Menu/>}</button><div className="search"><Search size={17}/><input placeholder="Search projects, sites, regions..."/></div><div className="header-actions"><button className="icon-btn"><Bell size={18}/><i/></button><div className="avatar">{(user?.full_name || "U")[0]}</div></div></header><div className="content">{children}</div></main></div>;
}
function PageTitle({eyebrow,title,sub,action}) { return <div className="page-title"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{sub}</p></div>{action}</div>; }
function Panel({title,subtitle,action,children}) { return <section className="panel"><div className="panel-head"><div><h3>{title}</h3>{subtitle&&<p>{subtitle}</p>}</div>{action}</div>{children}</section>; }
function Stat({icon:I,label,value,trend}) { return <div className="stat"><div className="stat-icon"><I size={20}/></div><div><span>{label}</span><strong>{value}</strong><small>{trend}</small></div></div>; }
function SiteTable({sites=[]}) {
  if (!sites.length) return <div className="empty">No sites yet. Create a project and register your first site.</div>;
  return <div className="table-wrap"><table><thead><tr><th>Rank / Site</th><th>Region</th><th>Resource</th><th>Infrastructure</th><th>Score</th><th>Status</th></tr></thead><tbody>{sites.map((s,i)=><tr key={s.id ?? `${s.name}-${i}`}><td><strong>{s.rank ? `#${s.rank} ` : ""}{s.name || "Unnamed site"}</strong><small>{fmt(s.latitude,3)}, {fmt(s.longitude,3)}</small></td><td>{s.region || "—"}</td><td>{fmt(s.solar_irradiance)} kWh/m²/day · {fmt(s.wind_speed)} m/s</td><td>{s.infrastructure || "—"}</td><td><b className="score">{fmt(s.overall_score)}%</b></td><td><span className={`badge ${s.category === "Excellent" || s.category === "Highly Suitable" ? "good" : ""}`}>{s.category || "Pending"}</span></td></tr>)}</tbody></table></div>;
}

function Dashboard() {
  const [data,setData]=useState(null),[error,setError]=useState("");
  useEffect(()=>{api("/dashboard").then(setData).catch(e=>setError(e.message));},[]);
  const rec=data?.recommended_sites||[];
  const chart=rec.map(s=>({name:String(s.name||"Site").slice(0,12),score:n(s.overall_score),energy:Math.round(n(s.ml_total_mwh_year,n(s.estimated_total_mwh_year)))}));
  return <><PageTitle eyebrow="OVERVIEW" title="Deployment intelligence" sub="Compare renewable candidate sites and identify the strongest deployment opportunities." action={<NavLink className="primary" to="/projects"><Plus size={17}/> New project</NavLink>}/>{error&&<div className="error">{error}</div>}
  <div className="stats"><Stat icon={FolderKanban} label="Active projects" value={data?.projects??"—"} trend="Project pipeline"/><Stat icon={MapPinned} label="Sites analysed" value={data?.sites??"—"} trend="Across your workspace"/><Stat icon={ShieldCheck} label="Avg suitability" value={data?`${fmt(data.average_score)}%`:"—"} trend="Weighted model"/><Stat icon={Zap} label="ML annual energy" value={data?`${(n(data.ml_annual_energy_mwh,n(data.annual_energy_mwh))/1000).toFixed(1)} GWh`:"—"} trend="Random Forest estimate"/></div>
  <div className="grid-2"><Panel title="Top site suitability" subtitle="Weighted deployment score"><div className="chart"><ResponsiveContainer width="100%" height={270}><BarChart data={chart}><CartesianGrid vertical={false} strokeDasharray="3 3"/><XAxis dataKey="name"/><YAxis domain={[0,100]}/><Tooltip/><Bar dataKey="score" radius={[6,6,0,0]}/></BarChart></ResponsiveContainer></div></Panel><Panel title="ML annual energy outlook" subtitle="Random Forest predicted MWh/year"><div className="chart"><ResponsiveContainer width="100%" height={270}><AreaChart data={chart}><CartesianGrid vertical={false} strokeDasharray="3 3"/><XAxis dataKey="name"/><YAxis/><Tooltip/><Area type="monotone" dataKey="energy" fillOpacity={.18} strokeWidth={2}/></AreaChart></ResponsiveContainer></div></Panel></div>
  <Panel title="Recommended deployment sites" subtitle="All candidate sites ranked against one another" action={<NavLink className="text-link" to="/recommendations">View comparison <ArrowRight size={14}/></NavLink>}><SiteTable sites={rec}/></Panel></>;
}

const emptySite={project_id:"",name:"",latitude:17.385,longitude:78.486,region:"Telangana, India",land_area:100,elevation:500,infrastructure:"Good",land_ownership:"Private",solar_irradiance:5.6,wind_speed:7.2,wind_direction:180,temperature:27,rainfall:800,cloud_cover:25,slope:4,vegetation_index:.35,roads_distance:4,transmission_distance:8,protected_zone:false,water_body:false,agricultural_land:false};
function Projects(){
  const [projects,setProjects]=useState([]),[sites,setSites]=useState([]),[show,setShow]=useState(false),[siteShow,setSiteShow]=useState(false),[active,setActive]=useState(null),[error,setError]=useState("");
  const [p,setP]=useState({name:"",region:"",technology:"Hybrid Solar + Wind"}); const [s,setS]=useState(emptySite);
  const load=async()=>{try{const [a,b]=await Promise.all([api("/projects"),api("/sites")]);setProjects(a);setSites(b);setError("");}catch(e){setError(e.message)}};
  useEffect(()=>{load()},[]);
  const createP=async e=>{e.preventDefault();try{await api("/projects",{method:"POST",body:JSON.stringify(p)});setP({name:"",region:"",technology:"Hybrid Solar + Wind"});setShow(false);await load()}catch(e){setError(e.message)}};
  const createS=async e=>{e.preventDefault();try{await api("/sites",{method:"POST",body:JSON.stringify({...s,project_id:Number(s.project_id),latitude:Number(s.latitude),longitude:Number(s.longitude),land_area:Number(s.land_area),elevation:Number(s.elevation),solar_irradiance:Number(s.solar_irradiance),wind_speed:Number(s.wind_speed),wind_direction:Number(s.wind_direction),temperature:Number(s.temperature),rainfall:Number(s.rainfall),cloud_cover:Number(s.cloud_cover),slope:Number(s.slope),vegetation_index:Number(s.vegetation_index),roads_distance:Number(s.roads_distance),transmission_distance:Number(s.transmission_distance)})});setSiteShow(false);setS(emptySite);await load()}catch(e){setError(e.message)}};
  const fields={project_id:"Project",name:"Site name",latitude:"Latitude",longitude:"Longitude",region:"Region",land_area:"Land area (ha)",elevation:"Elevation (m)",infrastructure:"Infrastructure",land_ownership:"Land ownership",solar_irradiance:"Solar irradiance",wind_speed:"Wind speed",wind_direction:"Wind direction",temperature:"Temperature",rainfall:"Rainfall",cloud_cover:"Cloud cover",slope:"Land slope",vegetation_index:"Vegetation index",roads_distance:"Road distance (km)",transmission_distance:"Transmission distance (km)"};
  return <><PageTitle eyebrow="PLANNING" title="Projects & sites" sub="Create projects, add multiple candidate sites and compare their renewable-energy potential." action={<><button className="secondary" onClick={()=>setSiteShow(true)} disabled={!projects.length}><MapPinned size={17}/> Register site</button><button className="primary" onClick={()=>setShow(true)}><Plus size={17}/> New project</button></>}/>{error&&<div className="error">{error}</div>}
  <div className="project-grid">{projects.map(pr=><div className="project-card" key={pr.id}><div className="project-top"><div className="project-icon"><Sun size={21}/></div><span className="badge good">{pr.status}</span></div><h3>{pr.name}</h3><p>{pr.region}</p><div className="project-meta"><span>{pr.technology}</span><b>{sites.filter(x=>x.project_id===pr.id).length} sites</b></div><button className="text-link" onClick={()=>{setActive(pr.id);setS({...emptySite,project_id:String(pr.id)})}}>View site data <ArrowRight size={14}/></button></div>)}</div>
  <Panel title={active?"Site comparison":"All analysed sites"} subtitle="Environmental, geographic, infrastructure and ML results"><SiteTable sites={active?sites.filter(x=>x.project_id===active):sites}/></Panel>
  {show&&<Modal title="Create project" onClose={()=>setShow(false)}><form onSubmit={createP} className="form-grid"><Field label="Project name" value={p.name} onChange={v=>setP({...p,name:v})}/><Field label="Region" value={p.region} onChange={v=>setP({...p,region:v})}/><Field label="Technology" value={p.technology} onChange={v=>setP({...p,technology:v})} select options={["Hybrid Solar + Wind","Solar","Wind"]}/><div className="modal-actions"><button type="button" className="secondary" onClick={()=>setShow(false)}>Cancel</button><button className="primary">Create project</button></div></form></Modal>}
  {siteShow&&<Modal title="Register candidate site" onClose={()=>setSiteShow(false)}><form onSubmit={createS} className="form-grid wide-form">{Object.entries(fields).map(([k,l])=><Field key={k} label={l} value={s[k]} onChange={v=>setS({...s,[k]:v})} type={k!=="project_id"&&k!=="name"&&k!=="region"&&k!=="infrastructure"&&k!=="land_ownership"?"number":"text"} select={k==="project_id"} options={k==="project_id"?projects.map(x=>({value:x.id,label:x.name})):k==="infrastructure"?["Excellent","Good","Moderate","Poor"]:k==="land_ownership"?["Private","Public","Leased"]:[]}/>) }<div className="checks">{["protected_zone","water_body","agricultural_land"].map(k=><label key={k} className="check"><input type="checkbox" checked={s[k]} onChange={e=>setS({...s,[k]:e.target.checked})}/>{k.replaceAll("_"," ")}</label>)}</div><div className="modal-actions"><button type="button" className="secondary" onClick={()=>setSiteShow(false)}>Cancel</button><button className="primary">Analyse with ML</button></div></form></Modal>}
  </>;
}
function Field({label,value,onChange,select,options=[],type="text"}){return <label>{label}{select?<select value={value} onChange={e=>onChange(e.target.value)} required><option value="">Select</option>{options.map(o=>typeof o==="object"?<option key={o.value} value={o.value}>{o.label}</option>:<option key={o}>{o}</option>)}</select>:<input type={type} step={type==="number"?"any":undefined} value={value??""} onChange={e=>onChange(e.target.value)} required/>}</label>}
function Modal({title,onClose,children}){return <div className="overlay"><div className="modal"><div className="modal-head"><h2>{title}</h2><button type="button" className="icon-btn" onClick={onClose}><X size={18}/></button></div>{children}</div></div>}

function Recommendations(){
  const [projects,setProjects]=useState([]),[projectId,setProjectId]=useState("all"),[sites,setSites]=useState([]),[error,setError]=useState("");
  useEffect(()=>{Promise.all([api("/projects"),api("/sites")]).then(([p,s])=>{setProjects(p);setSites(s)}).catch(e=>setError(e.message))},[]);
  const filtered=useMemo(()=>{const x=projectId==="all"?sites:sites.filter(s=>String(s.project_id)===String(projectId));return [...x].sort((a,b)=>n(b.overall_score)-n(a.overall_score)).map((s,i)=>({...s,rank:i+1}))},[sites,projectId]);
  const best=filtered[0];
  return <><PageTitle eyebrow="SITE INTELLIGENCE" title="Deployment recommendations" sub="Compare all candidate sites and rank the strongest location using the weighted suitability model." action={<select className="project-filter" value={projectId} onChange={e=>setProjectId(e.target.value)}><option value="all">All projects</option>{projects.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select>}/>{error&&<div className="error">{error}</div>}
    {best&&<div className="best-card"><div><span className="eyebrow">BEST CURRENT SITE</span><h2><Trophy size={20}/> {best.name}</h2><p>{best.region} · Rank #1 of {filtered.length} sites</p></div><div className="best-score">{fmt(best.overall_score)}<small>/100</small></div></div>}
    <Panel title="Site comparison" subtitle="Higher score = stronger overall deployment candidate"><SiteTable sites={filtered}/></Panel>
    <div className="rec-grid">{filtered.map(s=><div className="rec-card" key={s.id}><div className="rank">{String(s.rank).padStart(2,"0")}</div><div className="rec-main"><div className="rec-title"><div><h3>{s.name}</h3><p>{s.region} · {fmt(s.latitude,3)}, {fmt(s.longitude,3)}</p></div><div className="big-score">{fmt(s.overall_score)}<small>/100</small></div></div><div className="progress"><span style={{width:`${Math.max(0,Math.min(100,n(s.overall_score)))}%`}}/></div><div className="score-grid"><MiniScore l="Resource" v={s.resource_score}/><MiniScore l="Geographic" v={s.geographic_score}/><MiniScore l="Infrastructure" v={s.infrastructure_score}/><MiniScore l="Environmental" v={s.environmental_score}/><MiniScore l="Economic" v={s.economic_score}/></div><div className="rec-foot"><span className="badge good">{s.category}</span><span><Brain size={14}/> ML: {n(s.ml_total_mwh_year,n(s.estimated_total_mwh_year)).toLocaleString()} MWh/year</span></div></div></div>)}</div>{!filtered.length&&<div className="empty">No analysed sites for this project. Add candidate sites from Projects & Sites.</div>}</>;
}
function MiniScore({l,v}){return <div><span>{l}</span><strong>{fmt(v)}</strong></div>}

function Analytics(){
  const [sites,setSites]=useState([]),[error,setError]=useState("");
  useEffect(()=>{api("/sites").then(setSites).catch(e=>setError(e.message))},[]);
  const data=sites.map(s=>({name:String(s.name||"Site").slice(0,10),solar:n(s.solar_irradiance),wind:n(s.wind_speed),score:n(s.overall_score),ml:n(s.ml_total_mwh_year,n(s.estimated_total_mwh_year))}));
  return <><PageTitle eyebrow="ANALYTICS" title="Resource & feasibility analytics" sub="Compare solar, wind, ML energy predictions and suitability across your sites."/>{error&&<div className="error">{error}</div>}
  <div className="grid-2"><Panel title="Solar irradiance" subtitle="Candidate site resource"><div className="chart"><ResponsiveContainer width="100%" height={300}><BarChart data={data}><CartesianGrid vertical={false} strokeDasharray="3 3"/><XAxis dataKey="name"/><YAxis/><Tooltip/><Bar dataKey="solar" radius={[5,5,0,0]}/></BarChart></ResponsiveContainer></div></Panel><Panel title="Wind resource" subtitle="Average wind speed (m/s)"><div className="chart"><ResponsiveContainer width="100%" height={300}><BarChart data={data}><CartesianGrid vertical={false} strokeDasharray="3 3"/><XAxis dataKey="name"/><YAxis/><Tooltip/><Bar dataKey="wind" radius={[5,5,0,0]}/></BarChart></ResponsiveContainer></div></Panel></div>
  <Panel title="ML predicted annual energy" subtitle="Random Forest solar + wind prediction"><div className="chart"><ResponsiveContainer width="100%" height={280}><BarChart data={data}><CartesianGrid vertical={false} strokeDasharray="3 3"/><XAxis dataKey="name"/><YAxis/><Tooltip/><Bar dataKey="ml" radius={[5,5,0,0]}/></BarChart></ResponsiveContainer></div></Panel>
  <Panel title="Site factors" subtitle="Actual values from registered sites"><div className="factor-grid">{sites.slice(0,10).map(s=><div className="factor" key={s.id}><span>{s.name}</span><b>Score {fmt(s.overall_score)} · ML {Math.round(n(s.ml_total_mwh_year,n(s.estimated_total_mwh_year))).toLocaleString()} MWh</b></div>)}</div>{!sites.length&&<div className="empty">No site data available yet.</div>}</Panel></>;
}

function MLPrediction(){
  const [sites,setSites]=useState([]),[metrics,setMetrics]=useState(null),[error,setError]=useState("");
  useEffect(()=>{Promise.all([api("/sites"),api("/ml/info")]).then(([s,m])=>{setSites(s);setMetrics(m)}).catch(e=>setError(e.message))},[]);
  const ranked=[...sites].sort((a,b)=>n(b.ml_total_mwh_year,n(b.estimated_total_mwh_year))-n(a.ml_total_mwh_year,n(a.estimated_total_mwh_year)));
  return <><PageTitle eyebrow="AI / ML" title="Solar & wind ML prediction" sub="Random Forest regressors estimate annual solar and wind energy for each candidate site."/>{error&&<div className="error">{error}</div>}
  <div className="stats"><Stat icon={Brain} label="Model" value="Random Forest" trend="Two regression models"/><Stat icon={Activity} label="Training rows" value={metrics?.training_rows??"—"} trend="Development dataset"/><Stat icon={TrendingUp} label="Solar R²" value={metrics?fmt(metrics.solar_r2,3):"—"} trend="Hold-out test"/><Stat icon={Wind} label="Wind R²" value={metrics?fmt(metrics.wind_r2,3):"—"} trend="Hold-out test"/></div>
  <Panel title="Predicted site energy" subtitle="Sites ranked by ML-predicted combined annual energy"><SiteTable sites={ranked.map((s,i)=>({...s,rank:i+1}))}/></Panel>
  <Panel title="Model information" subtitle="How the ML component works"><div className="ml-info"><p><strong>Model:</strong> Random Forest Regressor, with separate models for solar and wind annual energy.</p><p><strong>Inputs:</strong> irradiance, wind speed, temperature, rainfall, cloud cover, elevation, slope, vegetation index, road/transmission distance, land area, latitude, longitude and wind direction.</p><p><strong>Workflow:</strong> site inputs → preprocessing → trained Random Forest models → solar prediction + wind prediction → combined ML energy estimate → site comparison.</p><p><strong>Important:</strong> the bundled training data is a synthetic development dataset created to demonstrate the ML pipeline. Replace it with validated historical observations before making real-world engineering or investment decisions.</p></div></Panel></>;
}

function Reports(){
  const [error,setError]=useState("");
  const download=async()=>{try{const token=localStorage.getItem("token");const r=await fetch(API+"/reports/sites.csv",{headers:{Authorization:`Bearer ${token}`}});if(!r.ok)throw new Error("Could not generate report");const b=await r.blob();const u=URL.createObjectURL(b);const a=document.createElement("a");a.href=u;a.download="site-assessment-report.csv";document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),1000)}catch(e){setError(e.message)}};
  return <><PageTitle eyebrow="REPORTING" title="Reports & exports" sub="Generate assessment outputs for planners and decision-makers."/>{error&&<div className="error">{error}</div>}<div className="report-grid">{[["Site assessment report","Candidate site scores, environmental inputs, ML predictions and suitability categories"],["Solar potential report","Solar resource and predicted annual energy output"],["Wind potential report","Wind resource and predicted annual production"],["Feasibility report","Environmental, infrastructure and economic assessment"],["Investment report","Suitability rankings and deployment priorities"]].map(([t,d])=><div className="report-card" key={t}><div className="report-icon"><FileBarChart size={20}/></div><h3>{t}</h3><p>{d}</p><button className="secondary" onClick={download}><Download size={15}/> Export CSV</button></div>)}</div><Panel title="Deployment workflow" subtitle="End-to-end workflow"><div className="workflow">{["Create project","Register multiple sites","Collect site data","Run ML prediction","Compare suitability","Rank best site","Export report"].map((x,i)=><div key={x}><span>{i+1}</span><b>{x}</b>{i<6&&<ArrowRight size={15}/>}</div>)}</div></Panel></>;
}
function Profile(){const user=JSON.parse(localStorage.getItem("user")||"{}");return <><PageTitle eyebrow="ACCOUNT" title="Profile" sub="Your workspace identity and role-based access."/><Panel title="Account details"><div className="profile"><div className="profile-avatar">{(user.full_name||"U")[0]}</div><div><h2>{user.full_name||"User"}</h2><p>{user.email||"—"}</p><span className="badge good">{user.role||"Planner"}</span></div></div></Panel></>}
function Protected({children}){return localStorage.getItem("token") ? <AppShell>{children}</AppShell> : <Navigate to="/login" replace/>;}
function HomeRedirect(){return localStorage.getItem("token") ? <Navigate to="/dashboard" replace/> : <Navigate to="/login" replace/>;}
function App(){return <Routes><Route path="/" element={<HomeRedirect/>}/><Route path="/login" element={<Auth mode="login"/>}/><Route path="/register" element={<Auth mode="register"/>}/><Route path="/dashboard" element={<Protected><Dashboard/></Protected>}/><Route path="/projects" element={<Protected><Projects/></Protected>}/><Route path="/recommendations" element={<Protected><Recommendations/></Protected>}/><Route path="/analytics" element={<Protected><Analytics/></Protected>}/><Route path="/ml-prediction" element={<Protected><MLPrediction/></Protected>}/><Route path="/reports" element={<Protected><Reports/></Protected>}/><Route path="/profile" element={<Protected><Profile/></Protected>}/><Route path="*" element={<HomeRedirect/>}/></Routes>}
createRoot(document.getElementById("root")).render(<BrowserRouter><ErrorBoundary><App/></ErrorBoundary></BrowserRouter>);
