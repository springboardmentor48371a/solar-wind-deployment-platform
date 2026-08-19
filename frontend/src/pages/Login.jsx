import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import Background from '../components/Background';

const API_URL = 'http://localhost:8000/api';

function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      console.log('Sending login request...');
      const response = await axios.post(`${API_URL}/auth/login`, { email, password });
      console.log('Login response:', response.data);

      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        console.log('Token stored, redirecting to dashboard...');
        // Use both methods for safety
        navigate('/dashboard');
        // Backup redirect
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 200);
      } else {
        setError('Login failed: No token received');
        setLoading(false);
      }
    } catch (err) {
      console.error('Login error:', err);
      if (err.response) {
        console.error('Response data:', err.response.data);
        setError(err.response.data?.error || 'Login failed');
      } else {
        setError('Cannot connect to server. Make sure backend is running.');
      }
      setLoading(false);
    }
  };

  return (
    <>
      <Background />
      <div style={styles.container}>
        <div style={styles.glassCard}>
          <div style={styles.logoSection}>
            <h1 style={styles.title}>⚡ Solar & Wind</h1>
            <p style={styles.subtitle}>Intelligence Platform</p>
          </div>

          <h2 style={styles.welcome}>Welcome Back</h2>
          {error && <div style={styles.error}>{error}</div>}

          <form onSubmit={handleSubmit}>
            <div style={styles.inputGroup}>
              <label style={styles.label}>Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                style={styles.input}
                placeholder="you@example.com"
              />
            </div>
            <div style={styles.inputGroup}>
              <label style={styles.label}>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                style={styles.input}
                placeholder="••••••••"
              />
            </div>
            <button type="submit" disabled={loading} style={styles.button}>
              {loading ? 'Logging in...' : 'Sign In'}
            </button>
          </form>

          <p style={styles.linkText}>
            Don't have an account? <Link to="/register" style={styles.link}>Create one</Link>
          </p>
        </div>
      </div>
    </>
  );
}

const styles = {
  container: {
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
  },
  glassCard: {
    width: '420px',
    padding: '40px',
    background: 'rgba(13, 27, 42, 0.65)',
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '20px',
    boxShadow: '0 25px 60px rgba(0, 0, 0, 0.6)',
    textAlign: 'center',
    maxWidth: '95%',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
  },
  logoSection: { marginBottom: '30px' },
  title: { fontSize: '28px', fontWeight: '700', color: '#ffffff', marginBottom: '4px' },
  subtitle: { fontSize: '14px', color: 'rgba(180, 210, 255, 0.6)' },
  welcome: { fontSize: '18px', fontWeight: '500', color: 'rgba(255,255,255,0.9)', marginBottom: '20px' },
  error: { backgroundColor: 'rgba(255,70,70,0.15)', color: '#ff6b6b', padding: '12px', borderRadius: '10px', marginBottom: '16px', fontSize: '14px', border: '1px solid rgba(255,70,70,0.1)' },
  inputGroup: { marginBottom: '18px', textAlign: 'left' },
  label: { display: 'block', color: 'rgba(200,220,255,0.7)', fontSize: '13px', fontWeight: '500', marginBottom: '6px' },
  input: { width: '100%', padding: '14px 16px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px', color: '#ffffff', fontSize: '15px', outline: 'none', boxSizing: 'border-box' },
  button: { width: '100%', padding: '14px', background: 'linear-gradient(135deg, #4a9eff 0%, #6c5ce7 100%)', color: 'white', border: 'none', borderRadius: '12px', fontSize: '16px', fontWeight: '600', cursor: 'pointer', marginTop: '8px' },
  linkText: { marginTop: '20px', color: 'rgba(180,210,255,0.5)', fontSize: '14px' },
  link: { color: '#4a9eff', textDecoration: 'none', fontWeight: '500' },
};

// Add hover styles
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  input:focus { border-color: rgba(74,158,255,0.4); background: rgba(255,255,255,0.08); }
  button:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(74,158,255,0.25); }
  button:disabled { opacity: 0.6; cursor: not-allowed; }
`;
document.head.appendChild(styleSheet);

export default Login;