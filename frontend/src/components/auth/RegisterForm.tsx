import React, { useState } from 'react';
import { User as UserIcon, Mail, Lock, Eye, EyeOff, UserPlus, AlertCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface RegisterFormProps {
  onSwitchToLogin: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onSwitchToLogin }) => {
  const { register, isLoading, error, clearError } = useAuth();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [localValidationError, setLocalValidationError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setLocalValidationError(null);

    if (password !== confirmPassword) {
      setLocalValidationError('Passwords do not match. Please verify both password fields.');
      return;
    }

    if (password.length < 6) {
      setLocalValidationError('Password must be at least 6 characters long.');
      return;
    }

    try {
      await register({
        full_name: fullName,
        email,
        password,
        confirm_password: confirmPassword,
      });
    } catch (err) {
      // Error handled via AuthContext error state
    }
  };

  const displayError = localValidationError || error;

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Error Alert Message */}
      {displayError && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-start space-x-2.5 text-rose-200 text-xs font-semibold animate-fadeIn">
          <AlertCircle className="w-4 h-4 text-rose-400 mt-0.5 shrink-0" />
          <div className="flex-1">{displayError}</div>
        </div>
      )}

      {/* Full Name Input Field */}
      <div>
        <label htmlFor="reg-fullname" className="block text-xs font-bold text-slate-300 mb-1.5 uppercase tracking-wider">
          Full Name
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <UserIcon className="w-4 h-4" />
          </div>
          <input
            id="reg-fullname"
            type="text"
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Dr. Alex Rivera"
            className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm text-slate-100 placeholder-slate-500 font-medium"
          />
        </div>
      </div>

      {/* Email Address Input Field */}
      <div>
        <label htmlFor="reg-email" className="block text-xs font-bold text-slate-300 mb-1.5 uppercase tracking-wider">
          Work Email
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <Mail className="w-4 h-4" />
          </div>
          <input
            id="reg-email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="alex.rivera@solar-wind-ai.com"
            className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm text-slate-100 placeholder-slate-500 font-medium"
          />
        </div>
      </div>

      {/* Password Input Field */}
      <div>
        <label htmlFor="reg-password" className="block text-xs font-bold text-slate-300 mb-1.5 uppercase tracking-wider">
          Password
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <Lock className="w-4 h-4" />
          </div>
          <input
            id="reg-password"
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

      {/* Confirm Password Input Field */}
      <div>
        <label htmlFor="reg-confirm-password" className="block text-xs font-bold text-slate-300 mb-1.5 uppercase tracking-wider">
          Confirm Password
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <Lock className="w-4 h-4" />
          </div>
          <input
            id="reg-confirm-password"
            type={showPassword ? 'text' : 'password'}
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="••••••••••••"
            className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm text-slate-100 placeholder-slate-500 font-medium"
          />
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-slate-950 font-bold text-sm shadow-md shadow-amber-500/10 transition-all duration-200 flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed mt-4"
      >
        {isLoading ? (
          <div className="w-5 h-5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
        ) : (
          <>
            <span>Register New Account</span>
            <UserPlus className="w-4 h-4" />
          </>
        )}
      </button>

      {/* Link to Login */}
      <div className="text-center text-xs text-slate-400 font-medium pt-2">
        Already have an account?{' '}
        <button
          type="button"
          onClick={onSwitchToLogin}
          className="text-amber-400 font-bold hover:underline hover:text-amber-300"
        >
          Sign In instead
        </button>
      </div>
    </form>
  );
};
