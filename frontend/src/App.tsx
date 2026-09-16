import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { LoginView } from './components/auth/LoginView';
import { Layout } from './components/layout/Layout';
import { HealthCheck } from './components/common/HealthCheck';
import { DashboardView } from './components/dashboard/DashboardView';
import { ServiceHealthView } from './components/service/ServiceHealthView';
import { IncidentsView } from './components/incidents/IncidentsView';
import { ProblemsView } from './components/problems/ProblemsView';
import { ChangesView } from './components/changes/ChangesView';
import { SLAView } from './components/sla/SLAView';
import { AIAssistantView } from './components/ai/AIAssistantView';
import { ReportsView } from './components/reports/ReportsView';
import { SchedulerView } from './components/scheduler/SchedulerView';
import { NotificationsView } from './components/notifications/NotificationsView';
import { DataUploadView } from './components/ingestion/DataUploadView';
import { AdminView } from './components/admin/AdminView';
import { IntegrationsView } from './components/admin/IntegrationsView';
import { ProfileView } from './components/profile/ProfileView';

const ProtectedRoute = ({ children, requiredRole }: { children: React.ReactNode, requiredRole?: string }) => {
  const { isAuthenticated, role } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && role !== requiredRole) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <WebSocketProvider>
            <Routes>
              <Route path="/login" element={<LoginView />} />
              <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
                <Route index element={<DashboardView />} />
                <Route path="service-health" element={<ServiceHealthView />} />
                <Route path="incidents" element={<IncidentsView />} />
                <Route path="problems" element={<ProblemsView />} />
                <Route path="changes" element={<ChangesView />} />
                <Route path="sla" element={<SLAView />} />
                <Route path="ai-assistant" element={<AIAssistantView />} />
                <Route path="reports" element={<ReportsView />} />
                <Route path="scheduler" element={<SchedulerView />} />
                <Route path="notifications" element={<NotificationsView />} />
                <Route path="data-upload" element={<DataUploadView />} />
                <Route path="integrations" element={<ProtectedRoute><IntegrationsView /></ProtectedRoute>} />
                <Route path="admin" element={<ProtectedRoute requiredRole="admin"><AdminView /></ProtectedRoute>} />
                <Route path="profile" element={<ProfileView />} />
                <Route path="status" element={<HealthCheck />} />
              </Route>
            </Routes>
          </WebSocketProvider>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
