import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopHeader } from './TopHeader';
import { AIChatDrawer } from '../ai/AIChatDrawer';

export const Layout: React.FC = () => {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', backgroundColor: 'var(--cg-bg-app)' }}>
      <Sidebar />
      <div style={{ flex: 1, marginLeft: '260px', display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <TopHeader />
        <main style={{ flex: 1, padding: '1.5rem 2rem', width: '100%', maxWidth: '1600px', boxSizing: 'border-box' }}>
          <Outlet />
        </main>
      </div>

      {/* Global AI Operations Analyst Floating Launcher */}
      <AIChatDrawer />
    </div>
  );
};
