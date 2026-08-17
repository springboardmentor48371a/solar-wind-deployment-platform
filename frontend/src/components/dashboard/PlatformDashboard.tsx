import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { Sun, Wind, LogOut, CheckCircle2, ShieldCheck, User, Mail, Key } from 'lucide-react';

export const PlatformDashboard: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100 flex flex-col relative overflow-hidden">
      
      {/* Background Accent Gradients */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-amber-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* Top Header Navbar */}
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-30 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-amber-500">
              <Sun className="w-5 h-5 animate-spin-slow" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white leading-snug">
                Solar & Wind Deployment Intelligence Platform
              </h1>
              <p className="text-xs text-amber-400 font-semibold tracking-wide">
                AI-Powered Renewable Energy Intelligence
              </p>
            </div>
          </div>

          <button
            onClick={logout}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-rose-950/20 hover:bg-rose-900/30 border border-rose-800/40 text-rose-300 text-sm font-bold transition-all shadow-sm"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </button>

        </div>
      </header>

      {/* Main Authenticated Dashboard Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 z-10">
        
        {/* Welcome Card */}
        <div className="glass-card rounded-3xl p-6 sm:p-8 mb-8 border border-slate-800 shadow-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 p-8 opacity-5 pointer-events-none">
            <Wind className="w-48 h-48 text-emerald-500" />
          </div>

          <div className="relative z-10">
            <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/35 text-emerald-400 text-xs font-bold mb-4 shadow-sm">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Authentication Session Active</span>
            </div>

            <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-2">
              Welcome back, {user?.full_name || 'Valued User'}!
            </h2>
            <p className="text-slate-300 text-sm max-w-2xl font-medium leading-relaxed">
              You are securely logged into the Solar & Wind Deployment Intelligence Platform. Your real JWT authentication session has been verified against the backend database.
            </p>
          </div>
        </div>

        {/* User Authentication Status Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          
          {/* Card 1: User Full Name */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800 flex items-start space-x-4 shadow-sm">
            <div className="p-3 rounded-xl bg-slate-900 text-amber-500 border border-slate-800">
              <User className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs uppercase tracking-wider text-slate-400 font-bold">User Identity</span>
              <p className="text-lg font-bold text-white mt-1">{user?.full_name}</p>
              <p className="text-xs text-slate-400 font-medium mt-0.5">Account ID: {user?.id?.substring(0, 13)}...</p>
            </div>
          </div>

          {/* Card 2: User Email */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800 flex items-start space-x-4 shadow-sm">
            <div className="p-3 rounded-xl bg-slate-900 text-emerald-400 border border-slate-800">
              <Mail className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs uppercase tracking-wider text-slate-400 font-bold">Authenticated Email</span>
              <p className="text-lg font-bold text-white mt-1">{user?.email}</p>
              <p className="text-xs text-slate-400 font-medium mt-0.5">Verified Primary Account</p>
            </div>
          </div>

          {/* Card 3: JWT Token & Security Status */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800 flex items-start space-x-4 shadow-sm">
            <div className="p-3 rounded-xl bg-slate-900 text-emerald-400 border border-slate-800">
              <ShieldCheck className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <span className="text-xs uppercase tracking-wider text-slate-400 font-bold">Authentication Status</span>
              <p className="text-lg font-bold text-emerald-400 mt-1 flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping inline-block" />
                <span>✓ Authenticated</span>
              </p>
              <p className="text-xs text-slate-400 font-medium mt-0.5">Secure JWT Verified</p>
            </div>
          </div>

        </div>

        {/* Security & Architecture Audit Panel */}
        <div className="glass-card rounded-2xl p-6 sm:p-8 border border-slate-800 shadow-sm">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center space-x-2">
            <Key className="w-5 h-5 text-amber-500" />
            <span>Active Session Details</span>
          </h3>

          <div className="bg-slate-950/80 rounded-xl p-4 border border-slate-800 font-mono text-xs text-slate-300 space-y-2.5 overflow-x-auto shadow-inner">
            <div><span className="text-amber-500 font-bold">User ID:</span> {user?.id}</div>
            <div><span className="text-amber-500 font-bold">Full Name:</span> {user?.full_name}</div>
            <div><span className="text-amber-500 font-bold">Email:</span> {user?.email}</div>
            <div><span className="text-amber-500 font-bold">Account Created:</span> {user?.created_at ? new Date(user.created_at).toLocaleString() : 'N/A'}</div>
            <div><span className="text-amber-500 font-bold">JWT Token Status:</span> Verified & Securely Stored Client-Side</div>
          </div>
        </div>

      </main>

      {/* Dashboard Footer */}
      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500 font-medium z-10">
        Solar & Wind Deployment Intelligence Platform &copy; 2026. All rights reserved.
      </footer>
    </div>
  );
};
