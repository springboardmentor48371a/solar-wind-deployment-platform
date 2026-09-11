import React, { useState } from 'react';
import { Mail, Lock, Eye, EyeOff, LogIn, AlertCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface LoginFormProps {
  onSwitchToRegister: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSwitchToRegister }) => {
  const { login, isLoading, error, clearError } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    if (!email || !password) return;

    try {
      await login({ email, password });
    } catch (err) {
      // Error handled via AuthContext error state
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Error Alert Message */}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-start space-x-2.5 text-rose-200 text-xs font-semibold animate-fadeIn">
          <AlertCircle className="w-4 h-4 text-rose-400 mt-0.5 shrink-0" />
          <div className="flex-1">{error}</div>
        </div>
      )}

      {/* Email Input Field */}
      <div>
        <label htmlFor="login-email" className="block text-xs font-bold text-slate-300 mb-1.5 uppercase tracking-wider">
          Email Address
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <Mail className="w-4 h-4" />
          </div>
          <input
            id="login-email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="engineer@renewable-ai.com"
            className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm text-slate-100 placeholder-slate-500 font-medium"
          />
        </div>
      </div>

      {/* Password Input Field */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <label htmlFor="login-password" className="block text-xs font-bold text-slate-300 uppercase tracking-wider">
            Password
          </label>
        </div>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <Lock className="w-4 h-4" />
          </div>
          <input
            id="login-password"
            type={showPassword ? 'text' : 'password'}
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••••••"
            className="w-full pl-10 pr-11 py-2.5 rounded-xl glass-input text-sm text-slate-100 placeholder-slate-500 font-medium"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200 transition-colors"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-slate-950 font-bold text-sm shadow-md shadow-amber-500/10 transition-all duration-200 flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed mt-6"
      >
        {isLoading ? (
          <div className="w-5 h-5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
        ) : (
          <>
            <span>Sign In to Platform</span>
            <LogIn className="w-4 h-4" />
          </>
        )}
      </button>

      {/* Quick Role Demo Accounts (For Springboard Presentation) */}
      <div className="pt-2 border-t border-slate-800/80 mt-4">
        <span className="text-[11px] font-semibold text-slate-400 block mb-2 text-center">
          1-Click Mentor Demo Logins (4 Platform Roles):
        </span>
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => {
              setEmail('admin@solarwind.ai');
              setPassword('Madurga@26');
              login({ email: 'admin@solarwind.ai', password: 'Madurga@26' });
            }}
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-rose-500/40 hover:bg-rose-500/20 text-[11px] font-bold text-rose-300 transition-all text-left truncate flex items-center justify-between"
          >
            <span>👑 Admin</span>
            <span className="text-[9px] font-normal opacity-75">Full Access</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setEmail('planner@solarwind.ai');
              setPassword('Madurga@26');
              login({ email: 'planner@solarwind.ai', password: 'Madurga@26' });
            }}
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-amber-500/40 hover:bg-amber-500/20 text-[11px] font-bold text-amber-300 transition-all text-left truncate flex items-center justify-between"
          >
            <span>⚡ Energy Planner</span>
            <span className="text-[9px] font-normal opacity-75">All Access</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setEmail('gis.specialist@solarwind.ai');
              setPassword('Madurga@26');
              login({ email: 'gis.specialist@solarwind.ai', password: 'Madurga@26' });
            }}
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-cyan-500/40 hover:bg-cyan-500/20 text-[11px] font-bold text-cyan-300 transition-all text-left truncate flex items-center justify-between"
          >
            <span>🗺️ GIS Specialist</span>
            <span className="text-[9px] font-normal opacity-75">Spatial</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setEmail('financial.analyst@solarwind.ai');
              setPassword('Madurga@26');
              login({ email: 'financial.analyst@solarwind.ai', password: 'Madurga@26' });
            }}
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-emerald-500/40 hover:bg-emerald-500/20 text-[11px] font-bold text-emerald-300 transition-all text-left truncate flex items-center justify-between"
          >
            <span>📊 Financial Analyst</span>
            <span className="text-[9px] font-normal opacity-75">Read-Only</span>
          </button>
        </div>
      </div>

      {/* Link to Register */}
      <div className="text-center text-xs text-slate-400 font-medium pt-2">
        Don't have an account?{' '}
        <button
          type="button"
          onClick={onSwitchToRegister}
          className="text-amber-400 font-bold hover:underline hover:text-amber-300"
        >
          Create an account
        </button>
      </div>
    </form>
  );
};
