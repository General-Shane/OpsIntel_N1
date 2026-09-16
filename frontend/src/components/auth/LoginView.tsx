import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { Lock, User, AlertCircle, Sun, Moon, Monitor } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { CapgeminiLogo } from '../common/CapgeminiLogo';

export const LoginView: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const { theme, resolvedTheme, setTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as any)?.from?.pathname || '/';

  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username, password }),
      });

      if (!response.ok) throw new Error('Invalid username or password');

      const data = await response.json();
      login(data.access_token, data.role, data.username, data.display_name, data.permissions);
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--cg-bg-app)',
        fontFamily: "'Inter', system-ui, sans-serif",
        position: 'relative',
        overflow: 'hidden',
        transition: 'background-color 0.2s ease'
      }}
    >
      {/* Top-Right Theme Toggle on Login Screen */}
      <div style={{
        position: 'absolute',
        top: '1.5rem',
        right: '1.5rem',
        display: 'flex',
        alignItems: 'center',
        backgroundColor: 'var(--cg-surface-secondary)',
        border: '1px solid var(--cg-border)',
        borderRadius: '7px',
        padding: '2px',
        gap: '2px',
        zIndex: 20
      }}>
        <button
          onClick={() => setTheme('light')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '28px',
            height: '26px',
            borderRadius: '5px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: theme === 'light' ? 'var(--cg-surface-card)' : 'transparent',
            color: theme === 'light' ? 'var(--cg-blue-primary)' : 'var(--text-muted)',
            transition: 'all 0.15s ease'
          }}
          title="Light Theme"
        >
          <Sun size={14} />
        </button>
        <button
          onClick={() => setTheme('dark')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '28px',
            height: '26px',
            borderRadius: '5px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: theme === 'dark' ? 'var(--cg-surface-card)' : 'transparent',
            color: theme === 'dark' ? 'var(--cg-blue-secondary)' : 'var(--text-muted)',
            transition: 'all 0.15s ease'
          }}
          title="Dark Theme"
        >
          <Moon size={14} />
        </button>
        <button
          onClick={() => setTheme('system')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '28px',
            height: '26px',
            borderRadius: '5px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: theme === 'system' ? 'var(--cg-surface-card)' : 'transparent',
            color: theme === 'system' ? 'var(--cg-blue-primary)' : 'var(--text-muted)',
            transition: 'all 0.15s ease'
          }}
          title="System Theme"
        >
          <Monitor size={14} />
        </button>
      </div>

      {/* Background ambient accents */}
      <div style={{
        position: 'absolute', top: '-15%', left: '-10%',
        width: '45%', height: '45%', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(0, 112, 173, 0.08) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute', bottom: '-15%', right: '-10%',
        width: '45%', height: '45%', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(18, 171, 219, 0.06) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      {/* Main Login Card */}
      <div style={{ width: '100%', maxWidth: 420, padding: '0 1.5rem', position: 'relative', zIndex: 10 }}>
        <div
          style={{
            backgroundColor: 'var(--cg-surface-card)',
            border: '1px solid var(--cg-border)',
            borderRadius: 12,
            padding: '2.5rem 2rem',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.08), 0 1px 3px rgba(0, 0, 0, 0.04)',
            position: 'relative',
          }}
        >
          {/* Capgemini Enterprise Brand Slot */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '2rem' }}>
            <div style={{ marginBottom: '1.25rem' }}>
              <CapgeminiLogo variant="full" theme={resolvedTheme === 'dark' ? 'dark' : 'light'} height={42} />
            </div>

            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.3px', margin: '0 0 0.35rem 0' }}>
              OPSINTEL
            </h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--cg-blue-primary)', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
              IT Operations Intelligence Platform
            </p>
          </div>

          {/* Error Alert */}
          {error && (
            <div style={{
              marginBottom: '1.25rem',
              backgroundColor: 'var(--status-critical-bg)',
              border: '1px solid var(--status-critical-border)',
              borderRadius: 7,
              padding: '0.75rem 1rem',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.6rem',
            }}>
              <AlertCircle style={{ width: 17, height: 17, color: 'var(--status-critical)', flexShrink: 0, marginTop: 1 }} />
              <p style={{ fontSize: '0.825rem', color: 'var(--status-critical)', margin: 0 }}>{error}</p>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* Username */}
            <div style={{ position: 'relative' }}>
              <div style={{
                position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)',
                pointerEvents: 'none', display: 'flex', alignItems: 'center',
              }}>
                <User style={{ width: 17, height: 17, color: 'var(--text-muted)' }} strokeWidth={1.75} />
              </div>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username (e.g. admin or analyst)"
                required
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  backgroundColor: 'var(--cg-surface-input)',
                  border: '1px solid var(--cg-border)',
                  borderRadius: 7,
                  paddingLeft: '2.85rem',
                  paddingRight: '1rem',
                  paddingTop: '0.75rem',
                  paddingBottom: '0.75rem',
                  color: 'var(--text-primary)',
                  fontSize: '0.875rem',
                  outline: 'none',
                  transition: 'border-color 0.2s, box-shadow 0.2s',
                }}
                onFocus={e => {
                  e.target.style.borderColor = 'var(--cg-blue-primary)';
                  e.target.style.boxShadow = '0 0 0 3px rgba(0, 112, 173, 0.18)';
                }}
                onBlur={e => {
                  e.target.style.borderColor = 'var(--cg-border)';
                  e.target.style.boxShadow = 'none';
                }}
              />
            </div>

            {/* Password */}
            <div style={{ position: 'relative' }}>
              <div style={{
                position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)',
                pointerEvents: 'none', display: 'flex', alignItems: 'center',
              }}>
                <Lock style={{ width: 17, height: 17, color: 'var(--text-muted)' }} strokeWidth={1.75} />
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                required
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  backgroundColor: 'var(--cg-surface-input)',
                  border: '1px solid var(--cg-border)',
                  borderRadius: 7,
                  paddingLeft: '2.85rem',
                  paddingRight: '1rem',
                  paddingTop: '0.75rem',
                  paddingBottom: '0.75rem',
                  color: 'var(--text-primary)',
                  fontSize: '0.875rem',
                  outline: 'none',
                  transition: 'border-color 0.2s, box-shadow 0.2s',
                }}
                onFocus={e => {
                  e.target.style.borderColor = 'var(--cg-blue-primary)';
                  e.target.style.boxShadow = '0 0 0 3px rgba(0, 112, 173, 0.18)';
                }}
                onBlur={e => {
                  e.target.style.borderColor = 'var(--cg-border)';
                  e.target.style.boxShadow = 'none';
                }}
              />
            </div>

            {/* Login Button */}
            <button
              type="submit"
              disabled={loading}
              className="btn-cg-primary"
              style={{
                marginTop: '0.5rem',
                width: '100%',
                padding: '0.75rem',
                fontSize: '0.9rem',
                borderRadius: 7,
                cursor: loading ? 'wait' : 'pointer',
              }}
            >
              {loading ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <svg style={{ width: 18, height: 18, animation: 'spin 1s linear infinite' }} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle style={{ opacity: 0.25 }} cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path style={{ opacity: 0.75 }} fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Authenticating...</span>
                </div>
              ) : 'Sign In'}
            </button>
          </form>
        </div>

        <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.725rem', color: 'var(--text-muted)', letterSpacing: '0.03em' }}>
          Authorized Enterprise Access • Demo credentials: <code style={{ color: 'var(--cg-blue-primary)', fontWeight: 600 }}>admin / admin</code>
        </p>
      </div>
    </div>
  );
};
