import React from 'react';
import { User, Sun, Moon, Monitor, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';

export const ProfileView: React.FC = () => {
  const { role } = useAuth();
  const { theme, setTheme } = useTheme();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '800px' }}>
      <div>
        <h1 className="page-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <User color="var(--cg-blue-primary)" size={24} />
          User Profile & Environment Preferences
        </h1>
        <p className="page-subtitle">
          Manage your credentials, operational role, and display preferences
        </p>
      </div>

      {/* Account Info Card */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <h3 className="card-title" style={{ margin: 0 }}>Active Identity</h3>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', paddingBottom: '1rem', borderBottom: '1px solid var(--cg-border)' }}>
          <div style={{
            width: 48,
            height: 48,
            borderRadius: '50%',
            backgroundColor: 'var(--cg-blue-primary)',
            color: '#FFFFFF',
            fontSize: '1.2rem',
            fontWeight: 800,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            AD
          </div>
          <div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {role === 'admin' ? 'Administrator' : 'Operations Analyst'}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Role: <code style={{ color: 'var(--cg-blue-primary)', fontWeight: 600 }}>{role}</code> • Access Tier: Level 3 Executive NOC
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Authentication Provider</span>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>JWT Bearer / Internal SQLite RBAC</span>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Session Security</span>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--status-healthy)', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
              <ShieldCheck size={14} /> Active & Encrypted
            </span>
          </div>
        </div>
      </div>

      {/* Theme & Display Preferences Card */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <h3 className="card-title" style={{ margin: 0 }}>Theme & Visual Experience</h3>
        <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', margin: 0 }}>
          Choose your interface preference. Light theme is tailored for executive reporting; Dark theme is engineered for 24/7 NOC command operations.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.85rem', marginTop: '0.5rem' }}>
          {/* Light Mode Option */}
          <div
            onClick={() => setTheme('light')}
            style={{
              padding: '1rem',
              borderRadius: '8px',
              border: `2px solid ${theme === 'light' ? 'var(--cg-blue-primary)' : 'var(--cg-border)'}`,
              backgroundColor: theme === 'light' ? 'var(--cg-blue-soft)' : 'var(--cg-surface-secondary)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
              transition: 'all 0.15s ease'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Sun size={20} color={theme === 'light' ? 'var(--cg-blue-primary)' : 'var(--text-secondary)'} />
              {theme === 'light' && <CheckCircle2 size={16} color="var(--cg-blue-primary)" />}
            </div>
            <div>
              <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary)', display: 'block' }}>Light Theme</strong>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Executive & Review</span>
            </div>
          </div>

          {/* Dark Mode Option */}
          <div
            onClick={() => setTheme('dark')}
            style={{
              padding: '1rem',
              borderRadius: '8px',
              border: `2px solid ${theme === 'dark' ? 'var(--cg-blue-primary)' : 'var(--cg-border)'}`,
              backgroundColor: theme === 'dark' ? 'var(--cg-blue-soft)' : 'var(--cg-surface-secondary)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
              transition: 'all 0.15s ease'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Moon size={20} color={theme === 'dark' ? 'var(--cg-blue-secondary)' : 'var(--text-secondary)'} />
              {theme === 'dark' && <CheckCircle2 size={16} color="var(--cg-blue-primary)" />}
            </div>
            <div>
              <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary)', display: 'block' }}>Dark Theme</strong>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>NOC Command Center</span>
            </div>
          </div>

          {/* System Option */}
          <div
            onClick={() => setTheme('system')}
            style={{
              padding: '1rem',
              borderRadius: '8px',
              border: `2px solid ${theme === 'system' ? 'var(--cg-blue-primary)' : 'var(--cg-border)'}`,
              backgroundColor: theme === 'system' ? 'var(--cg-blue-soft)' : 'var(--cg-surface-secondary)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
              transition: 'all 0.15s ease'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Monitor size={20} color={theme === 'system' ? 'var(--cg-blue-primary)' : 'var(--text-secondary)'} />
              {theme === 'system' && <CheckCircle2 size={16} color="var(--cg-blue-primary)" />}
            </div>
            <div>
              <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary)', display: 'block' }}>System Theme</strong>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Match OS Setting</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
