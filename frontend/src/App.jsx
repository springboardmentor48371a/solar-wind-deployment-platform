import React, { useState } from 'react';
import { 
  Sun, 
  Wind, 
  ShieldCheck, 
  Mail, 
  Lock, 
  UserCheck, 
  User, 
  Eye, 
  EyeOff, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';

export default function App() {
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('Renewable Energy Planner');
  
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [loggedInUser, setLoggedInUser] = useState(null);

  const roles = [
    'Renewable Energy Planner',
    'GIS Analyst',
    'Project Manager',
    'Administrator'
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage(null);

    if (isRegister) {
      if (password !== confirmPassword) {
        setMessage({ type: 'error', text: 'Passwords do not match.' });
        return;
      }
      if (password.length < 6) {
        setMessage({ type: 'error', text: 'Password must be at least 6 characters long.' });
        return;
      }
    }

    setLoading(true);
    const endpoint = isRegister 
      ? 'http://127.0.0.1:8000/api/auth/register' 
      : 'http://127.0.0.1:8000/api/auth/login';
    
    const payload = isRegister 
      ? { name, email, password, confirm_password: confirmPassword, role }
      : { email, password, role };

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('token', data.access_token);
        setLoggedInUser({ name: data.name, role: data.role, email: data.email });
        setMessage({ 
          type: 'success', 
          text: isRegister ? 'Registration successful! Logged in.' : `Welcome back, ${data.name}!` 
        });
      } else {
        setMessage({ type: 'error', text: data.detail || 'Authentication failed' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Unable to connect to backend server (http://127.0.0.1:8000)' });
    } finally {
      setLoading(false);
    }
  };

  if (loggedInUser) {
    return (
      <div className="min-h-screen bg-slate-50 text-slate-800 font-sans">
        <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1 bg-emerald-50 text-emerald-600 p-2 rounded-xl border border-emerald-100">
              <Sun className="w-5 h-5 text-amber-500" />
              <Wind className="w-5 h-5 text-sky-500" />
            </div>
            <div>
              <h1 className="text-base font-semibold text-slate-900 leading-none">Solar & Wind Intelligence</h1>
              <p className="text-xs text-slate-500 mt-0.5">Deployment Platform</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="text-sm font-semibold text-slate-800">{loggedInUser.name}</p>
              <span className="inline-block text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                {loggedInUser.role}
              </span>
            </div>
            <button 
              onClick={() => { setLoggedInUser(null); setMessage(null); }}
              className="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium px-3 py-1.5 rounded-lg border border-slate-200 transition"
            >
              Sign Out
            </button>
          </div>
        </header>

        <main className="max-w-6xl mx-auto p-8">
          <div className="bg-white rounded-2xl p-8 border border-slate-200 shadow-sm text-center">
            <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4 border border-emerald-100">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900">Welcome, {loggedInUser.name}!</h2>
            <p className="text-sm text-slate-600 mt-2 max-w-md mx-auto">
              Signed in as <span className="font-semibold text-slate-800">{loggedInUser.role}</span>.
            </p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 text-slate-800 font-sans">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
        <div className="flex flex-col items-center text-center mb-6">
          <div className="flex items-center justify-center space-x-2 bg-emerald-50 text-emerald-600 p-3 rounded-2xl border border-emerald-100 mb-3">
            <Sun className="w-6 h-6 text-amber-500" />
            <Wind className="w-6 h-6 text-sky-500" />
          </div>
          <h1 className="text-xl font-semibold text-slate-900 tracking-tight">
            Solar & Wind Intelligence Platform
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Renewable Energy Deployment & Feasibility Analysis
          </p>
        </div>

        <div className="flex bg-slate-100 p-1 rounded-xl mb-6 border border-slate-200">
          <button
            type="button"
            onClick={() => { setIsRegister(false); setMessage(null); }}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition ${
              !isRegister ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setIsRegister(true); setMessage(null); }}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition ${
              isRegister ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Register Account
          </button>
        </div>

        {message && (
          <div className={`p-3 rounded-lg text-xs font-medium mb-5 flex items-start space-x-2 border ${
            message.type === 'success' 
              ? 'bg-emerald-50 border-emerald-200 text-emerald-700' 
              : 'bg-rose-50 border-rose-200 text-rose-700'
          }`}>
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span>{message.text}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">
                Display Name
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="text"
                  required
                  placeholder="Sakshi Sharma"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">
              Platform Role
            </label>
            <div className="relative">
              <UserCheck className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition"
              >
                {roles.map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="email"
                required
                placeholder="planner@energy.org"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">
              {isRegister ? 'Create Password' : 'Password'}
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-10 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 focus:outline-none"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {isRegister && (
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  required
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-10 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 focus:outline-none"
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-slate-900 hover:bg-slate-800 text-white font-medium py-2.5 rounded-lg text-sm shadow-sm transition duration-150 ease-in-out mt-2 disabled:opacity-50"
          >
            {loading 
              ? (isRegister ? 'Creating Account...' : 'Authenticating...') 
              : (isRegister ? 'Register & Sign In' : 'Sign In to Portal')
            }
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-center space-x-1.5 text-xs text-slate-400">
          <ShieldCheck className="w-4 h-4 text-slate-400" />
          <span>Role-Based Access Control (RBAC)</span>
        </div>
      </div>
    </div>
  );
}