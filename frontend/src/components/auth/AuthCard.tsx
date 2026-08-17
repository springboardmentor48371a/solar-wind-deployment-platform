import React from 'react';
import { Sun, Wind, Cpu } from 'lucide-react';

interface AuthCardProps {
  activeTab: 'login' | 'register';
  onTabChange: (tab: 'login' | 'register') => void;
  children: React.ReactNode;
}

export const AuthCard: React.FC<AuthCardProps> = ({ activeTab, onTabChange, children }) => {
  return (
    <div className="w-full max-w-md mx-auto z-20 px-4 py-6">
      <div className="glass-card rounded-2xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
        
        {/* Top Decorative Solar & Green Highlight Bar */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-amber-500 via-emerald-500 to-amber-600" />
        
        {/* Header Section */}
        <div className="text-center mb-8">
          {/* Platform Icon Badge */}
          <div className="inline-flex items-center justify-center space-x-2 px-3.5 py-1.5 rounded-full bg-slate-900/90 border border-slate-700/80 text-slate-100 mb-4 shadow-sm">
            <Sun className="w-4 h-4 text-amber-500 animate-spin-slow" />
            <Wind className="w-4 h-4 text-emerald-400" />
            <Cpu className="w-4 h-4 text-amber-400" />
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-200">CleanTech AI</span>
          </div>

          {/* Application Title */}
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-tight">
            Solar & Wind Deployment Intelligence Platform
          </h1>

          {/* Subtitle */}
          <p className="mt-2 text-sm text-amber-400 font-semibold tracking-wide">
            AI-powered renewable energy intelligence
          </p>
        </div>

        {/* Tab Navigation Controls */}
        <div className="flex bg-slate-950/70 p-1.5 rounded-xl border border-slate-800/80 mb-6">
          <button
            type="button"
            onClick={() => onTabChange('login')}
            className={`flex-1 py-2.5 text-sm font-bold rounded-lg transition-all duration-200 ${
              activeTab === 'login'
                ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 shadow-md'
                : 'text-slate-400 hover:text-white hover:bg-slate-900/40'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => onTabChange('register')}
            className={`flex-1 py-2.5 text-sm font-bold rounded-lg transition-all duration-200 ${
              activeTab === 'register'
                ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 shadow-md'
                : 'text-slate-400 hover:text-white hover:bg-slate-900/40'
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Form Container */}
        <div>{children}</div>

        {/* Security Footer Badge */}
        <div className="mt-6 pt-5 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400 font-medium">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>256-bit SSL Encrypted</span>
          </div>
          <span className="text-slate-500">v1.0 Enterprise</span>
        </div>

      </div>
    </div>
  );
};
