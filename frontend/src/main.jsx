
import React, {useEffect, useMemo, useState} from "react";
import {createRoot} from "react-dom/client";
import {BrowserRouter, Routes, Route, NavLink, Navigate, useNavigate} from "react-router-dom";
import {Sun, Wind, LayoutDashboard, MapPinned, FolderKanban, FileBarChart, Bell, Settings, LogOut, Plus, ArrowRight, ShieldCheck, Zap, TrendingUp, Activity, Search, Menu, X, Download} from "lucide-react";
import {AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, CartesianGrid} from "recharts";
import "./styles.css";

const API="http://localhost:8000";
const api=async(path, options={})=>{
  const token=localStorage.getItem("token");
  const headers={"Content-Type":"application/json", ...(options.headers||{})};
  if(token) headers.Authorization=`Bearer ${token}`;
  const res=await fetch(API+path,{...options,headers});
  if(!res.ok){
    let msg="Request failed";
    try{msg=(await res.json()).detail||msg}catch{}
    if(res.status===401 && !["/login","/register"].includes(window.location.pathname)){
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href="/login";
    }
    throw new Error(msg);
  }
  return res.json();
};

function Auth({mode}) {
  const nav=useNavigate();
  const [form,setForm]=useState({full_name:"",email:"",password:"",role:"Renewable Energy Planner"});
  const [error,setError]=useState("");
  const [loading,setLoading]=useState(false);
  const register=mode==="register";
  const submit=async e=>{
    e.preventDefault(); setError(""); setLoading(true);
    try{
      const data=await api(register?"/auth/register":"/auth/login",{method:"POST",body:JSON.stringify(register?form:{email:form.email,password:form.password})});
      localStorage.setItem("token",data.access_token); localStorage.setItem("user",JSON.stringify(data.user)); nav("/dashboard");
    }catch(err){setError(err.message)} finally{setLoading(false)}
  };
  return <div className="auth-page"><div className="auth-left">
    <div className="brand"><div className="brand-mark"><Sun size={22}/></div><span className="brand-name">Solar and Wind Prediction</span></div>
    <div className="auth-copy"><div className="eyebrow">SOLAR AND WIND PREDICTION</div><h1>Plan smarter.<br/><em>Deploy cleaner.</em></h1><p>Turn environmental, geographic and infrastructure data into confident renewable deployment decisions.</p>
      <div className="mini-stats"><span><strong>35%</strong> resource weighting</span><span><strong>5</strong> suitability bands</span></div>
    </div>
  </div><div className="auth-card-wrap"><div className="auth-card">
    <div className="mobile-brand brand"><div className="brand-mark"><Sun size={18}/></div><span className="brand-name">Solar and Wind Prediction</span></div>
    <h2>{register?"Create your account":"Welcome back"}</h2><p className="muted">{register?"Start building renewable site intelligence.":"Sign in to continue to your deployment workspace."}</p>
    {error&&<div className="error">{error}</div>}
    <form onSubmit={submit}>
      {register&&<><label>Full name<input value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})} placeholder="Your name" required/></label>
      <label>Role<select value={form.role} onChange={e=>setForm({...form,role:e.target.value})}><option>Renewable Energy Planner</option><option>GIS Analyst</option><option>Project Manager</option><option>Administrator</option></select></label></>}
      <label>Email address<input type="email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})} placeholder="you@example.com" required/></label>
      <label>Password<input type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} placeholder="Minimum 6 characters" required minLength="6"/></label>
      <button className="primary wide" disabled={loading}>{loading?"Please wait...":register?"Create account":"Sign in"} <ArrowRight size={17}/></button>
    </form>
    <div className="auth-switch">{register?"Already have an account?":"Don't have an account?"} <button onClick={()=>nav(register?"/login":"/register")}>{register?"Sign in":"Create one"}</button></div>
    <div className="security"><ShieldCheck size={16}/> Passwords are securely hashed before storage.</div>
  </div></div></div>
}

function AppShell({children}){
  const nav=useNavigate(); const [user,setUser]=useState(JSON.parse(localStorage.getItem("user")||"null")); const [open,setOpen]=useState(false);
  useEffect(()=>{if(!localStorage.getItem("token"))nav("/login")},[]);
  const logout=()=>{localStorage.clear();nav("/login")};
  const links=[["/dashboard","Dashboard",LayoutDashboard],["/projects","Projects & Sites",FolderKanban],["/recommendations","Recommendations",MapPinned],["/analytics","Analytics",TrendingUp],["/reports","Reports",FileBarChart]];
  return <div className="app"><aside className={open?"open":""}><div className="brand"><div className="brand-mark"><Sun size={20}/></div><span className="brand-name">Solar and Wind Prediction</span></div>
    <div className="side-label">WORKSPACE</div>{links.map(([to,label,I])=><NavLink onClick={()=>setOpen(false)} className={({isActive})=>isActive?"active":""} to={to} key={to}><I size={18}/>{label}</NavLink>)}
    <div className="side-label">SYSTEM</div><NavLink to="/profile"><Settings size={18}/>Profile</NavLink><div className="side-bottom"><div className="user-mini"><div className="avatar">{(user?.full_name||"U")[0]}</div><div><strong>{user?.full_name||"User"}</strong><small>{user?.role||"Planner"}</small></div></div><button className="logout" onClick={logout}><LogOut size={17}/></button></div>
  </aside><main><header><button className="menu-btn" onClick={()=>setOpen(!open)}>{open?<X/>:<Menu/>}</button><div className="search"><Search size={17}/><input placeholder="Search projects, sites, regions..."/></div><div className="header-actions"><button className="icon-btn"><Bell size={18}/><i/></button><div className="avatar">{(user?.full_name||"U")[0]}</div></div></header><div className="content">{children}</div></main></div>
}

function Dashboard(){
 const [data,setData]=useState(null);
 useEffect(()=>{api("/dashboard").then(setData).catch(()=>{})},[]);
 const rec=data?.recommended_sites||[];
 const chart=rec.map((s,i)=>({name:s.name.length>12?s.name.slice(0,12)+"…":s.name,score:s.overall_score,energy:Math.round(s.estimated_total_mwh_year)}));
 return <><PageTitle eyebrow="OVERVIEW" title="Deployment intelligence" sub="A live workspace for renewable site planning and investment decisions." action={<NavLink className="primary" to="/projects"><Plus size={17}/> New project</NavLink>}/>
 <div className="stats"><Stat icon={FolderKanban} label="Active projects" value={data?.projects??"—"} trend="Project pipeline"/><Stat icon={MapPinned} label="Sites analysed" value={data?.sites??"—"} trend="Across your workspace"/><Stat icon={ShieldCheck} label="Avg suitability" value={data?`${data.average_score}%`:"—"} trend="Weighted model"/><Stat icon={Zap} label="Est. annual energy" value={data?`${(data.annual_energy_mwh/1000).toFixed(1)} GWh`:"—"} trend="Current sites"/></div>
 <div className="grid-2"><Panel title="Top site suitability" subtitle="Weighted deployment score"><div className="chart"><ResponsiveContainer width="100%" height={270}><BarChart data={chart}><CartesianGrid vertical={false} strokeDasharray="3 3"/><XAxis dataKey="name" tick={{fontSize:12}}/><YAxis domain={[0,100]}/><Tooltip/><Bar dataKey="score" radius={[6,6,0,0]} /></BarChart></ResponsiveContainer></div></Panel>
 <Panel title="Annual energy outlook" subtitle="Estimated MWh/year"><div className="chart"><ResponsiveContainer width="100%" height={270}><AreaChart data={chart}><CartesianGrid vertical={false} strokeDasharray="3 3"/><XAxis dataKey="name" tick={{fontSize:12}}/><YAxis/><Tooltip/><Area type="monotone" dataKey="energy" fillOpacity={.18} strokeWidth={2}/></AreaChart></ResponsiveContainer></div></Panel></div>
 <Panel title="Recommended deployment sites" subtitle="Ranked using the PDF weighted scoring model" action={<NavLink className="text-link" to="/recommendations">View all <ArrowRight size={14}/></NavLink>}><SiteTable sites={rec}/></Panel>
 </>;
}
function Stat({icon:I,label,value,trend}){return <div className="stat"><div className="stat-icon"><I size={20}/></div><div><span>{label}</span><strong>{value}</strong><small>{trend}</small></div></div>}
function PageTitle({eyebrow,title,sub,action}){return <div className="page-title"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{sub}</p></div>{action}</div>}
function Panel({title,subtitle,action,children}){return <section className="panel"><div className="panel-head"><div><h3>{title}</h3>{subtitle&&<p>{subtitle}</p>}</div>{action}</div>{children}</section>}
function SiteTable({sites}){if(!sites?.length)return <div className="empty">No sites yet. Create a project and register your first site.</div>;return <div className="table-wrap"><table><thead><tr><th>Site</th><th>Region</th><th>Resource</th><th>Infrastructure</th><th>Score</th><th>Status</th></tr></thead><tbody>{sites.map(s=><tr key={s.id}><td><strong>{s.name}</strong><small>{s.latitude.toFixed(3)}, {s.longitude.toFixed(3)}</small></td><td>{s.region}</td><td>{s.solar_irradiance.toFixed(1)} kWh/m²/day · {s.wind_speed.toFixed(1)} m/s</td><td>{s.infrastructure}</td><td><b className="score">{s.overall_score}%</b></td><td><span className={`badge ${s.category==="Excellent"||s.category==="Highly Suitable"?"good":""}`}>{s.category}</span></td></tr>)}</tbody></table></div>}

function Projects(){
 const [projects,setProjects]=useState([]),[sites,setSites]=useState([]),[show,setShow]=useState(false),[siteShow,setSiteShow]=useState(false),[active,setActive]=useState(null);
 const blank={name:"",region:"",technology:"Hybrid Solar + Wind"};
 const [p,setP]=useState(blank);
 const [s,setS]=useState({project_id:"",name:"",latitude:17.385,longitude:78.486,region:"Telangana, India",land_area:100,elevation:500,infrastructure:"Good",land_ownership:"Private",solar_irradiance:5.6,wind_speed:7.2,wind_direction:180,temperature:27,rainfall:800,cloud_cover:25,slope:4,vegetation_index:.35,roads_distance:4,transmission_distance:8,protected_zone:false,water_body:false,agricultural_land:false});
 const load=()=>{api("/projects").then(setProjects);api("/sites").then(setSites)}; useEffect(load,[]);
 const createP=async e=>{e.preventDefault();await api("/projects",{method:"POST",body:JSON.stringify(p)});setP(blank);setShow(false);load()};
 const createS=async e=>{e.preventDefault();await api("/sites",{method:"POST",body:JSON.stringify({...s,project_id:Number(s.project_id)})});setSiteShow(false);load()};
 return <><PageTitle eyebrow="PLANNING" title="Projects & sites" sub="Create projects, register candidate locations and assess deployment feasibility." action={<><button className="secondary" onClick={()=>setSiteShow(true)}><MapPinned size={17}/> Register site</button><button className="primary" onClick={()=>setShow(true)}><Plus size={17}/> New project</button></>}/>
 <div className="project-grid">{projects.map(pr=><div className="project-card" key={pr.id}><div className="project-top"><div className="project-icon"><Sun size={21}/></div><span className="badge good">{pr.status}</span></div><h3>{pr.name}</h3><p>{pr.region}</p><div className="project-meta"><span>{pr.technology}</span><b>{sites.filter(x=>x.project_id===pr.id).length} sites</b></div><button className="text-link" onClick={()=>{setActive(pr.id);setS({...s,project_id:pr.id});}}>View site data <ArrowRight size={14}/></button></div>)}</div>
 <Panel title={active?"Site register":"All analysed sites"} subtitle="Environmental, geographic and infrastructure inputs"><SiteTable sites={active?sites.filter(x=>x.project_id===active):sites}/></Panel>
 {show&&<Modal title="Create project"><form onSubmit={createP} className="form-grid"><Field label="Project name" value={p.name} onChange={v=>setP({...p,name:v})}/><Field label="Region" value={p.region} onChange={v=>setP({...p,region:v})}/><Field label="Technology" value={p.technology} onChange={v=>setP({...p,technology:v})} select options={["Hybrid Solar + Wind","Solar","Wind"]}/><div className="modal-actions"><button type="button" className="secondary" onClick={()=>setShow(false)}>Cancel</button><button className="primary">Create project</button></div></form></Modal>}
 {siteShow&&<Modal title="Register candidate site"><form onSubmit={createS} className="form-grid wide-form">{Object.entries({project_id:"Project",name:"Site name",latitude:"Latitude",longitude:"Longitude",region:"Region",land_area:"Land area (ha)",elevation:"Elevation (m)",infrastructure:"Infrastructure",land_ownership:"Land ownership",solar_irradiance:"Solar irradiance",wind_speed:"Wind speed",wind_direction:"Wind direction",temperature:"Temperature",rainfall:"Rainfall",cloud_cover:"Cloud cover",slope:"Land slope",vegetation_index:"Vegetation index",roads_distance:"Road distance (km)",transmission_distance:"Transmission distance (km)"}).map(([k,l])=><Field key={k} label={l} value={s[k]} onChange={v=>setS({...s,[k]:v})} select={k==="project_id"} options={k==="project_id"?projects.map(x=>({value:x.id,label:x.name})):k==="infrastructure"?["Excellent","Good","Moderate","Poor"]:k==="land_ownership"?["Private","Public","Leased"]:undefined}/>)}<div className="checks">{["protected_zone","water_body","agricultural_land"].map(k=><label key={k} className="check"><input type="checkbox" checked={s[k]} onChange={e=>setS({...s,[k]:e.target.checked})}/>{k.replaceAll("_"," ")}</label>)}</div><div className="modal-actions"><button type="button" className="secondary" onClick={()=>setSiteShow(false)}>Cancel</button><button className="primary">Analyse site</button></div></form></Modal>}
 </>;
}
function Field({label,value,onChange,select,options=[]}){return <label>{label}{select?<select value={value} onChange={e=>onChange(e.target.value)} required><option value="">Select</option>{options.map(o=>typeof o==="object"?<option key={o.value} value={o.value}>{o.label}</option>:<option key={o}>{o}</option>)}</select>:<input value={value} onChange={e=>onChange(e.target.value)} required/>}</label>}
function Modal({title,children}){return <div className="overlay"><div className="modal"><div className="modal-head"><h2>{title}</h2><span onClick={()=>{}}> </span></div>{children}</div></div>}

function Recommendations(){
 const [sites,setSites]=useState([]);useEffect(()=>api("/sites").then(x=>setSites(x.sort((a,b)=>b.overall_score-a.overall_score))),[]);
 return <><PageTitle eyebrow="SITE INTELLIGENCE" title="Deployment recommendations" sub="Ranked candidate locations using the documented 35/25/15/15/10 weighted scoring model."/>
 <div className="rec-grid">{sites.map((s,i)=><div className="rec-card" key={s.id}><div className="rank">0{i+1}</div><div className="rec-main"><div className="rec-title"><div><h3>{s.name}</h3><p>{s.region} · {s.latitude.toFixed(3)}, {s.longitude.toFixed(3)}</p></div><div className="big-score">{s.overall_score}<small>/100</small></div></div><div className="progress"><span style={{width:`${s.overall_score}%`}}/></div><div className="score-grid"><MiniScore l="Resource" v={s.resource_score}/><MiniScore l="Geographic" v={s.geographic_score}/><MiniScore l="Infrastructure" v={s.infrastructure_score}/><MiniScore l="Environmental" v={s.environmental_score}/><MiniScore l="Economic" v={s.economic_score}/></div><div className="rec-foot"><span className={`badge ${s.category.includes("Suitable")||s.category==="Excellent"?"good":""}`}>{s.category}</span><span><Zap size={14}/> {s.estimated_total_mwh_year.toLocaleString()} MWh/year est.</span></div></div></div>)}</div>{!sites.length&&<div className="empty">No analysed sites. Add candidate sites from Projects & Sites.</div>}</>
}
function MiniScore({l,v}){return <div><span>{l}</span><strong>{v}</strong></div>}

function Analytics(){
 const [sites,setSites]=useState([]);useEffect(()=>api("/sites").then(setSites),[]);
 const data=sites.map(s=>({name:s.name.slice(0,10),solar:+s.solar_irradiance.toFixed(1),wind:+s.wind_speed.toFixed(1),score:s.overall_score}));
 return <><PageTitle eyebrow="ANALYTICS" title="Resource & feasibility analytics" sub="Compare solar, wind, geography, infrastructure and environmental constraints."/>
 <div className="grid-2"><Panel title="Solar irradiance" subtitle="Candidate site resource"><div className="chart"><ResponsiveContainer width="100%" height={300}><BarChart data={data}><CartesianGrid vertical={false} strokeDasharray="3 3"/><XAxis dataKey="name"/><YAxis/><Tooltip/><Bar dataKey="solar" radius={[5,5,0,0]}/></BarChart></ResponsiveContainer></div></Panel><Panel title="Wind resource" subtitle="Average wind speed (m/s)"><div className="chart"><ResponsiveContainer width="100%" height={300}><BarChart data={data}><CartesianGrid vertical={false} strokeDasharray="3 3"/><XAxis dataKey="name"/><YAxis/><Tooltip/><Bar dataKey="wind" radius={[5,5,0,0]}/></BarChart></ResponsiveContainer></div></Panel></div>
 <Panel title="Environmental & geographic inputs" subtitle="Factors from the platform specification"><div className="factor-grid">{["Solar irradiance","Wind speed","Temperature","Rainfall","Cloud cover","Elevation","Land slope","Vegetation index","Road proximity","Transmission proximity"].map((x,i)=><div className="factor" key={x}><span>{x}</span><b>{sites.length?["5.6 kWh/m²/day","7.2 m/s","27 °C","800 mm","25%","500 m","4°","0.35","4 km","8 km"][i]:"—"}</b></div>)}</div></Panel></>
}

function Reports(){
 const download=async()=>{const token=localStorage.getItem("token");const r=await fetch(API+"/reports/sites.csv",{headers:{Authorization:`Bearer ${token}`}});const b=await r.blob();const u=URL.createObjectURL(b);const a=document.createElement("a");a.href=u;a.download="site-assessment-report.csv";a.click();URL.revokeObjectURL(u)};
 return <><PageTitle eyebrow="REPORTING" title="Reports & exports" sub="Generate assessment outputs for planners, project managers and decision-makers."/>
 <div className="report-grid">{[["Site assessment report","Candidate site scores, environmental inputs and suitability categories"],["Solar potential report","Solar resource and estimated energy output"],["Wind potential report","Wind resource, power density and annual production"],["Feasibility report","Environmental, infrastructure and economic assessment"],["Investment report","Suitability rankings and deployment priorities"]].map(([t,d])=><div className="report-card" key={t}><div className="report-icon"><FileBarChart size={20}/></div><h3>{t}</h3><p>{d}</p><button className="secondary" onClick={download}><Download size={15}/> Export CSV</button></div>)}</div>
 <Panel title="Deployment workflow" subtitle="End-to-end workflow represented in the project brief"><div className="workflow">{["Create project","Register site","Collect environmental data","Score suitability","Forecast energy","Optimise deployment","Export report"].map((x,i)=><div key={x}><span>{i+1}</span><b>{x}</b>{i<6&&<ArrowRight size={15}/>}</div>)}</div></Panel></>
}
function Profile(){const user=JSON.parse(localStorage.getItem("user")||"{}");return <><PageTitle eyebrow="ACCOUNT" title="Profile" sub="Your workspace identity and role-based access."/><Panel title="Account details"><div className="profile"><div className="profile-avatar">{(user.full_name||"U")[0]}</div><div><h2>{user.full_name}</h2><p>{user.email}</p><span className="badge good">{user.role}</span></div></div></Panel></>}
function Protected({children}){
  const token=localStorage.getItem("token");
  return token ? <AppShell>{children}</AppShell> : <Navigate to="/login" replace/>;
}

function HomeRedirect(){
  return localStorage.getItem("token") ? <Navigate to="/dashboard" replace/> : <Navigate to="/login" replace/>;
}

function App(){return <Routes>
  <Route path="/" element={<HomeRedirect/>}/>
  <Route path="/login" element={<Auth mode="login"/>}/>
  <Route path="/register" element={<Auth mode="register"/>}/>
  <Route path="/dashboard" element={<Protected><Dashboard/></Protected>}/>
  <Route path="/projects" element={<Protected><Projects/></Protected>}/>
  <Route path="/recommendations" element={<Protected><Recommendations/></Protected>}/>
  <Route path="/analytics" element={<Protected><Analytics/></Protected>}/>
  <Route path="/reports" element={<Protected><Reports/></Protected>}/>
  <Route path="/profile" element={<Protected><Profile/></Protected>}/>
  <Route path="*" element={<HomeRedirect/>}/>
</Routes>}
createRoot(document.getElementById("root")).render(<BrowserRouter><App/></BrowserRouter>);
