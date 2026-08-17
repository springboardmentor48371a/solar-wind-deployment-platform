import React, {useEffect, useState} from "react";
import { createRoot } from "react-dom/client";
import axios from "axios";
import "leaflet/dist/leaflet.css";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import { Bar } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend } from "chart.js";
import "./styles.css";
ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const API="http://127.0.0.1:8000";
const emptySite={name:"",region:"",latitude:28.6139,longitude:77.2090,land_area:10,elevation:200,infrastructure:"Road and grid nearby"};

function App(){
 const [token,setToken]=useState(localStorage.getItem("token")||"");
 const [user,setUser]=useState(JSON.parse(localStorage.getItem("user")||"null"));
 const [mode,setMode]=useState("login");
 const [auth,setAuth]=useState({name:"",email:"",password:"",role:"Renewable Energy Planner"});
 const [sites,setSites]=useState([]);
 const [site,setSite]=useState(emptySite);
 const [selected,setSelected]=useState(null);
 const [result,setResult]=useState(null);
 const [tab,setTab]=useState("dashboard");
 const headers={Authorization:`Bearer ${token}`};

 useEffect(()=>{if(token) loadSites()},[token]);
 async function loadSites(){try{let r=await axios.get(API+"/sites",{headers});setSites(r.data)}catch(e){logout()}}
 function logout(){localStorage.clear();setToken("");setUser(null);setSites([]);setResult(null)}
 async function submitAuth(e){e.preventDefault();try{
   let endpoint=mode==="login"?"/auth/login":"/auth/register";
   let payload=mode==="login"?{email:auth.email,password:auth.password}:auth;
   let r=await axios.post(API+endpoint,payload); localStorage.setItem("token",r.data.access_token);localStorage.setItem("user",JSON.stringify(r.data.user));setToken(r.data.access_token);setUser(r.data.user);
 }catch(e){alert(e.response?.data?.detail||"Authentication failed")}}
 async function addSite(e){e.preventDefault();try{await axios.post(API+"/sites",site,{headers});setSite(emptySite);loadSites();alert("Site created")}catch(e){alert(e.response?.data?.detail||"Could not create site")}}
 async function analyze(s){
   setSelected(s);setTab("analysis");
   try{let r=await axios.post(API+"/assessment",{latitude:s.latitude,longitude:s.longitude,land_area:s.land_area,elevation:s.elevation},{headers});setResult(r.data)}
   catch(e){alert("Analysis failed")}
 }
 if(!token) return <div className="auth-wrap"><div className="auth-card"><h1>☀️ Solar & Wind</h1><p>Deployment Intelligence Platform</p><form onSubmit={submitAuth}>
 {mode==="register"&&<input placeholder="Name" value={auth.name} onChange={e=>setAuth({...auth,name:e.target.value})} required/>}
 <input type="email" placeholder="Email" value={auth.email} onChange={e=>setAuth({...auth,email:e.target.value})} required/>
 <input type="password" placeholder="Password" value={auth.password} onChange={e=>setAuth({...auth,password:e.target.value})} required/>
 {mode==="register"&&<select value={auth.role} onChange={e=>setAuth({...auth,role:e.target.value})}><option>Renewable Energy Planner</option><option>GIS Analyst</option><option>Project Manager</option><option>Administrator</option></select>}
 <button>{mode==="login"?"Login":"Create Account"}</button></form>
 <button className="link" onClick={()=>setMode(mode==="login"?"register":"login")}>{mode==="login"?"New user? Register":"Already registered? Login"}</button></div></div>;

 const nav=["dashboard","sites","analysis","map","report"];
 return <div className="app"><aside><h2>☀️ SWDI</h2><p>{user?.name}</p>{nav.map(x=><button key={x} className={tab===x?"active":""} onClick={()=>setTab(x)}>{x.toUpperCase()}</button>)}<button onClick={logout}>LOGOUT</button></aside>
 <main><header><h1>{tab==="dashboard"?"Renewable Energy Dashboard":tab.toUpperCase()}</h1><span>{user?.role}</span></header>
 {tab==="dashboard"&&<Dashboard sites={sites} result={result} onAnalyze={analyze}/>}
 {tab==="sites"&&<Sites site={site} setSite={setSite} sites={sites} addSite={addSite} onAnalyze={analyze} headers={headers} loadSites={loadSites}/>}
 {tab==="analysis"&&<Analysis selected={selected} result={result}/>}
 {tab==="map"&&<MapView sites={sites} selected={selected} onAnalyze={analyze}/>}
 {tab==="report"&&<Report selected={selected} result={result}/>}
 </main></div>
}

function Dashboard({sites,result,onAnalyze}){return <><div className="stats"><Card title="Registered Sites" value={sites.length}/><Card title="Overall Score" value={result?result.scores.overall_score+" / 100":"--"}/><Card title="Solar Energy" value={result?result.solar.expected_annual_energy_mwh+" MWh":"--"}/><Card title="Wind Energy" value={result?result.wind.expected_annual_energy_mwh+" MWh":"--"}/></div><section className="panel"><h2>Your Sites</h2>{sites.length===0?<p>No sites yet. Go to SITES and create your first site.</p>:<table><thead><tr><th>Site</th><th>Region</th><th>Coordinates</th><th>Action</th></tr></thead><tbody>{sites.map(s=><tr key={s.id}><td>{s.name}</td><td>{s.region}</td><td>{s.latitude}, {s.longitude}</td><td><button onClick={()=>onAnalyze(s)}>Analyze</button></td></tr>)}</tbody></table>}</section></>}

function Card({title,value}){return <div className="card"><p>{title}</p><h2>{value}</h2></div>}

function Sites({site,setSite,sites,addSite,onAnalyze,headers,loadSites}){let change=(k,v)=>setSite({...site,[k]:v});return <><section className="panel"><h2>Register New Deployment Site</h2><form className="grid-form" onSubmit={addSite}>{Object.entries(site).map(([k,v])=><label key={k}>{k.replaceAll("_"," ").toUpperCase()}<input type={["latitude","longitude","land_area","elevation"].includes(k)?"number":"text"} step="any" value={v} onChange={e=>change(k,["latitude","longitude","land_area","elevation"].includes(k)?Number(e.target.value):e.target.value)} required={k==="name"||k==="latitude"||k==="longitude"}/></label>)}<button>Add Site</button></form></section><section className="panel"><h2>Sites</h2>{sites.map(s=><div className="site-row" key={s.id}><div><b>{s.name}</b><br/>{s.region} · {s.land_area} hectares</div><div><button onClick={()=>onAnalyze(s)}>Run Analysis</button><button className="danger" onClick={async()=>{await axios.delete(API+"/sites/"+s.id,{headers});loadSites()}}>Delete</button></div></div>)}</section></>}

function Analysis({selected,result}){if(!selected)return <section className="panel"><p>Select and analyze a site first.</p></section>;if(!result)return <section className="panel"><p>Running analysis...</p></section>;let e=result.environment,s=result.solar,w=result.wind;let data={labels:["Solar Score","Wind Score","Terrain Score"],datasets:[{label:"Suitability",data:[result.scores.solar_score,result.scores.wind_score,result.scores.terrain_score]}]};return <><section className="panel"><h2>{selected.name} — Assessment</h2><div className="stats"><Card title="Overall Score" value={result.scores.overall_score}/><Card title="Category" value={result.scores.category}/><Card title="Wind Speed" value={e.wind_speed_m_s+" m/s"}/><Card title="Solar Irradiance" value={e.solar_irradiance_kwh_m2_day+" kWh/m²/day"}/></div></section><div className="two-col"><section className="panel"><h2>Environmental Intelligence</h2><Metric data={e}/></section><section className="panel"><h2>Suitability Scores</h2><Bar data={data}/></section></div><div className="two-col"><section className="panel"><h2>Solar Prediction</h2><Metric data={s}/></section><section className="panel"><h2>Wind Prediction</h2><Metric data={w}/></section></div></>}

function Metric({data}){return <div className="metrics">{Object.entries(data).map(([k,v])=><div key={k}><span>{k.replaceAll("_"," ")}</span><b>{v}</b></div>)}</div>}

function MapView({sites,selected,onAnalyze}){let center=selected?[selected.latitude,selected.longitude]:sites.length?[sites[0].latitude,sites[0].longitude]:[28.6139,77.2090];return <section className="panel map-panel"><MapContainer center={center} zoom={5} style={{height:"520px",width:"100%"}}><TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>{sites.map(s=><Marker position={[s.latitude,s.longitude]} key={s.id}><Popup><b>{s.name}</b><br/>{s.region}<br/><button onClick={()=>onAnalyze(s)}>Analyze</button></Popup></Marker>)}</MapContainer></section>}

function Report({selected,result}){if(!result)return <section className="panel"><p>Analyze a site to generate its resource assessment report.</p></section>;return <section className="report"><h1>RESOURCE ASSESSMENT REPORT</h1><h2>{selected.name}</h2><p>Coordinates: {selected.latitude}, {selected.longitude}</p><hr/><h2>Overall Deployment Suitability: {result.scores.overall_score}/100</h2><h3>{result.scores.category}</h3><h2>Solar Potential</h2><Metric data={result.solar}/><h2>Wind Potential</h2><Metric data={result.wind}/><h2>Environmental Conditions</h2><Metric data={result.environment}/><button onClick={()=>window.print()}>Print / Save as PDF</button></section>}

createRoot(document.getElementById("root")).render(<App/>);
