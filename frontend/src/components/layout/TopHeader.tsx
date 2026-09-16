import React from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import {
  Menu,
  Search,
  Bell,
  HelpCircle,
  Sun,
  Moon,
  Monitor
} from 'lucide-react';

export const TopHeader: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { role } = useAuth();
  const { theme, setTheme } = useTheme();

  const getPageInfo = () => {
    switch (location.pathname) {
      case '/service-health':
        return {
          title: 'Service Health & Infrastructure Catalog',
          subtitle: 'Fleet availability • Service criticality tiers • Error budget monitoring • MTTR telemetry'
        };
      case '/incidents':
        return {
          title: 'Incident Management & NOC Triage',
          subtitle: 'Real-time telemetry • Root-cause correlation • SLA breach tracking • Automated triage'
        };
      case '/problems':
        return {
          title: 'Problem Management & Root Cause Intelligence',
          subtitle: 'Known-error tracking • Investigation backlog • Recurring cluster detection • Corrective actions'
        };
      case '/changes':
        return {
          title: 'Change Management & Release Governance',
          subtitle: 'Deployment tracking • Risk evaluation • Release success rate • Change failure telemetry'
        };
      case '/sla':
        return {
          title: 'SLA Compliance & Service Level Objectives',
          subtitle: 'Contractual SLA compliance • Breach distribution • Error budget consumption • Target threshold monitoring'
        };
      case '/reports':
        return {
          title: 'Executive Operational Reports Engine',
          subtitle: 'Generate and customize executive operational reports • Multi-channel Webhook routing'
        };
      case '/scheduler':
        return {
          title: 'Automated Report Scheduler & Delivery Governance',
          subtitle: 'Autonomous background synthesis • Multi-channel Webhook routing • Scheduled dispatch lifecycle'
        };
      case '/notifications':
        return {
          title: 'Operational Alerts & Delivery Channels',
          subtitle: 'Real-time threshold alerts • Multi-channel Webhook routing • Delivery audit stream'
        };
      case '/data-upload':
        return {
          title: 'Data Upload & Ingestion Center',
          subtitle: 'Upload CSV datasets (Incidents, Problems, Changes, SLAs, Services) to ingest into SQLite'
        };
      case '/admin':
        return {
          title: 'System Administration & Control Center',
          subtitle: 'Execute administrative operations, database maintenance, data purges, and environment re-seeding'
        };
      case '/ai-assistant':
        return {
          title: 'AI Operations Analyst',
          subtitle: 'Ask questions and get AI-powered insights grounded in live telemetry'
        };
      case '/profile':
        return {
          title: 'User Profile & Environment Preferences',
          subtitle: 'Session configuration • Role credentials • System telemetry preferences'
        };
      case '/':
      default:
        return {
          title: 'Global Operations Command Center',
          subtitle: 'Executive Overview • Incident Governance • SLA Performance • Predictive Risk'
        };
    }
  };

  const { title, subtitle } = getPageInfo();

  return (
    <header style={{
      width: '100%',
      backgroundColor: 'var(--cg-surface-card)',
      borderBottom: '1px solid var(--cg-border)',
      padding: '0.75rem 2rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '1.5rem',
      boxSizing: 'border-box',
      transition: 'background-color 0.2s ease, border-color 0.2s ease'
    }}>
      {/* Left Title & Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button
          style={{
            background: 'none',
            border: '1px solid var(--cg-border)',
            borderRadius: '6px',
            padding: '0.4rem',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          title="Toggle Navigation"
        >
          <Menu size={18} />
        </button>

        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <h1 style={{
              fontSize: '1.15rem',
              fontWeight: 800,
              color: 'var(--text-primary)',
              margin: 0,
              letterSpacing: '-0.3px',
              lineHeight: 1.2
            }}>
              {title}
            </h1>
            <span style={{
              fontSize: '0.625rem',
              fontWeight: 700,
              padding: '0.125rem 0.45rem',
              borderRadius: '12px',
              backgroundColor: 'var(--status-healthy-bg)',
              color: 'var(--status-healthy)',
              border: '1px solid var(--status-healthy-border)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.25rem',
              letterSpacing: '0.4px'
            }}>
              <span style={{ width: 5, height: 5, borderRadius: '50%', backgroundColor: 'var(--status-healthy)', display: 'inline-block' }} />
              LIVE
            </span>
          </div>
          <p style={{
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
            margin: '0.1rem 0 0 0',
            lineHeight: 1.2
          }}>
            {subtitle}
          </p>
        </div>
      </div>

      {/* Right Controls: Search, Theme Switcher, Notifications, Help, Profile */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
        {/* Global Search Box */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.4rem 0.85rem',
          borderRadius: '7px',
          border: '1px solid var(--cg-border)',
          backgroundColor: 'var(--cg-surface-input)',
          minWidth: '260px'
        }}>
          <input
            type="text"
            placeholder="Search for incidents, services, KB..."
            style={{
              border: 'none',
              background: 'transparent',
              fontSize: '0.8rem',
              color: 'var(--text-primary)',
              outline: 'none',
              width: '100%'
            }}
          />
          <Search size={14} color="var(--text-muted)" />
        </div>

        {/* Theme Switcher Segmented Control */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          backgroundColor: 'var(--cg-surface-secondary)',
          border: '1px solid var(--cg-border)',
          borderRadius: '7px',
          padding: '2px',
          gap: '2px'
        }} title={`Current theme: ${theme}`}>
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
              boxShadow: theme === 'light' ? '0 1px 2px rgba(0, 0, 0, 0.1)' : 'none',
              transition: 'all 0.15s ease'
            }}
            title="Light Theme (Executive Review)"
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
              boxShadow: theme === 'dark' ? '0 1px 2px rgba(0, 0, 0, 0.2)' : 'none',
              transition: 'all 0.15s ease'
            }}
            title="Dark Theme (NOC Command Center)"
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
              boxShadow: theme === 'system' ? '0 1px 2px rgba(0, 0, 0, 0.1)' : 'none',
              transition: 'all 0.15s ease'
            }}
            title="System Preference"
          >
            <Monitor size={14} />
          </button>
        </div>

        {/* Notifications Icon with Badge */}
        <Link
          to="/notifications"
          style={{
            position: 'relative',
            padding: '0.4rem',
            borderRadius: '6px',
            color: 'var(--text-secondary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            textDecoration: 'none'
          }}
          title="Notifications"
        >
          <Bell size={17} />
          <span style={{
            position: 'absolute',
            top: 2,
            right: 2,
            width: 14,
            height: 14,
            borderRadius: '50%',
            backgroundColor: 'var(--status-critical)',
            color: '#FFFFFF',
            fontSize: '0.6rem',
            fontWeight: 800,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '2px solid var(--cg-surface-card)'
          }}>
            3
          </span>
        </Link>

        {/* Help Icon */}
        <button
          onClick={() => navigate('/ai-assistant')}
          style={{
            background: 'none',
            border: 'none',
            padding: '0.4rem',
            borderRadius: '6px',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          title="AI Operations Assistant"
        >
          <HelpCircle size={17} />
        </button>

        {/* User Profile Mini Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', paddingLeft: '0.6rem', borderLeft: '1px solid var(--cg-border)' }}>
          <div style={{
            width: 30,
            height: 30,
            borderRadius: '50%',
            backgroundColor: 'var(--cg-blue-primary)',
            color: '#FFFFFF',
            fontSize: '0.75rem',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            AD
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '0.775rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.1 }}>
              {role === 'admin' ? 'Administrator' : 'Ops Analyst'}
            </span>
            <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', lineHeight: 1.1 }}>
              Super Admin
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
