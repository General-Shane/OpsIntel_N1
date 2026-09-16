import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { CapgeminiLogo } from '../common/CapgeminiLogo';
import {
  Home,
  Server,
  AlertTriangle,
  HelpCircle,
  GitCommit,
  BarChart2,
  Bot,
  FileText,
  Clock,
  Bell,
  UploadCloud,
  Settings,
  LogOut,
  ChevronLeft,
  Link2
} from 'lucide-react';

interface NavItem {
  label: string;
  path: string;
  icon: React.ComponentType<{ size?: number; color?: string }>;
  badge?: string;
}

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { role, logout } = useAuth();

  const operationsNav: NavItem[] = [
    { label: 'Overview', path: '/', icon: Home },
    { label: 'Service Health', path: '/service-health', icon: Server },
    { label: 'Incidents', path: '/incidents', icon: AlertTriangle },
    { label: 'Problems', path: '/problems', icon: HelpCircle },
    { label: 'Changes', path: '/changes', icon: GitCommit },
    { label: 'SLA / Performance', path: '/sla', icon: BarChart2 },
  ];

  const intelligenceNav: NavItem[] = [
    { label: 'AI Assistant', path: '/ai-assistant', icon: Bot, badge: 'AI' },
    { label: 'Reports', path: '/reports', icon: FileText },
    { label: 'Notifications', path: '/notifications', icon: Bell },
  ];

  const adminNav: NavItem[] = [
    { label: 'Integrations', path: '/integrations', icon: Link2 },
    { label: 'Scheduler', path: '/scheduler', icon: Clock },
    { label: 'Data Upload', path: '/data-upload', icon: UploadCloud },
    { label: 'Administration', path: '/admin', icon: Settings },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const renderNavGroup = (title: string, items: NavItem[]) => (
    <div style={{ marginBottom: '1.25rem' }}>
      <div style={{
        padding: '0 0.85rem 0.35rem',
        fontSize: '0.65rem',
        fontWeight: 700,
        color: '#607996',
        textTransform: 'uppercase',
        letterSpacing: '0.9px'
      }}>
        {title}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
        {items.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              to={item.path}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.55rem 0.85rem',
                borderRadius: '6px',
                textDecoration: 'none',
                fontSize: '0.825rem',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? '#FFFFFF' : '#B2C3D4',
                backgroundColor: isActive ? 'var(--cg-navy-sidebar-active)' : 'transparent',
                borderLeft: isActive ? '3px solid var(--cg-blue-primary)' : '3px solid transparent',
                transition: 'all 0.15s ease'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Icon size={16} color={isActive ? '#0070AD' : '#7C93AA'} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span style={{
                  fontSize: '0.6rem',
                  fontWeight: 700,
                  padding: '0.1rem 0.4rem',
                  borderRadius: '4px',
                  backgroundColor: 'var(--cg-blue-primary)',
                  color: '#FFFFFF',
                  letterSpacing: '0.3px'
                }}>
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </div>
    </div>
  );

  return (
    <aside style={{
      width: '260px',
      height: '100vh',
      backgroundColor: 'var(--cg-navy-sidebar)',
      borderRight: '1px solid rgba(255, 255, 255, 0.06)',
      display: 'flex',
      flexDirection: 'column',
      position: 'fixed',
      left: 0,
      top: 0,
      zIndex: 100,
      overflowY: 'auto'
    }}>
      {/* Capgemini Enterprise Brand Header */}
      <div style={{ padding: '1.25rem 1.15rem 1rem 1.15rem', borderBottom: '1px solid rgba(255, 255, 255, 0.06)' }}>
        <Link to="/" style={{ textDecoration: 'none', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <CapgeminiLogo variant="full" theme="dark" height={28} />
          </div>
          <div style={{ marginTop: '0.35rem' }}>
            <div style={{
              fontWeight: 800,
              fontSize: '1rem',
              letterSpacing: '0.8px',
              color: '#FFFFFF',
              lineHeight: 1.1
            }}>
              OPSINTEL
            </div>
            <div style={{
              fontSize: '0.575rem',
              color: '#7188A3',
              letterSpacing: '0.12em',
              fontWeight: 700,
              textTransform: 'uppercase',
              marginTop: '0.15rem'
            }}>
              IT OPERATIONS INTELLIGENCE
            </div>
          </div>
        </Link>

        {/* Live Status Pill Box */}
        <div style={{
          marginTop: '1rem',
          padding: '0.5rem 0.65rem',
          backgroundColor: 'rgba(0, 0, 0, 0.2)',
          borderRadius: '6px',
          border: '1px solid rgba(255, 255, 255, 0.05)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.2rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.6rem', fontWeight: 700, color: 'var(--cg-cyan-accent)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            <span>◆</span>
            <span>LIVE STATUS</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.675rem', color: '#CBD5E1' }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: 'var(--status-healthy)', display: 'inline-block' }} />
            <span>All systems operational</span>
          </div>
        </div>
      </div>

      {/* Navigation Groups */}
      <nav style={{ flex: 1, padding: '1rem 0.65rem' }}>
        {renderNavGroup('OPERATIONS', operationsNav)}
        {renderNavGroup('INTELLIGENCE & REPORTING', intelligenceNav)}
        {role === 'admin' && renderNavGroup('ADMINISTRATION', adminNav)}
      </nav>

      {/* Footer Profile & Logout Area */}
      <div style={{
        padding: '0.85rem 1rem',
        borderTop: '1px solid rgba(255, 255, 255, 0.06)',
        backgroundColor: 'rgba(0, 0, 0, 0.25)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.65rem'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{
              width: 28,
              height: 28,
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
            <div>
              <div style={{ fontSize: '0.8rem', color: '#FFFFFF', fontWeight: 600 }}>Administrator</div>
              <div style={{ fontSize: '0.65rem', color: '#7C93AA' }}>Super Admin</div>
            </div>
          </div>
          <span style={{
            fontSize: '0.6rem',
            padding: '0.1rem 0.4rem',
            borderRadius: '4px',
            backgroundColor: 'rgba(22, 138, 99, 0.25)',
            color: '#4ADE80',
            fontWeight: 700
          }}>
            LIVE
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '0.4rem', borderTop: '1px solid rgba(255, 255, 255, 0.04)' }}>
          <button
            onClick={handleLogout}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              color: '#94A3B8',
              backgroundColor: 'transparent',
              border: 'none',
              fontSize: '0.75rem',
              fontWeight: 500,
              cursor: 'pointer',
              padding: '0.2rem 0',
              transition: 'color 0.15s ease'
            }}
            onMouseEnter={(e) => { e.currentTarget.style.color = '#FCA5A5'; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = '#94A3B8'; }}
          >
            <LogOut size={13} />
            <span>Sign Out</span>
          </button>

          <button
            title="Collapse Sidebar"
            style={{
              width: 22,
              height: 22,
              borderRadius: '4px',
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#94A3B8',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer'
            }}
          >
            <ChevronLeft size={14} />
          </button>
        </div>

        <div style={{ fontSize: '0.625rem', color: '#5A728C', lineHeight: 1.3 }}>
          © 2026 Capgemini<br />All rights reserved.
        </div>
      </div>
    </aside>
  );
};
