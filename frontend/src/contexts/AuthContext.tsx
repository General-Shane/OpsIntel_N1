import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import axios from 'axios';

interface AuthContextType {
  token: string | null;
  role: string | null;
  username: string | null;
  displayName: string | null;
  permissions: string[];
  login: (token: string, role: string, username?: string, displayName?: string, permissions?: string[]) => void;
  logout: () => void;
  isAuthenticated: boolean;
  hasPermission: (perm: string) => boolean;
  hasRole: (r: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [role, setRole] = useState<string | null>(localStorage.getItem('role'));
  const [username, setUsername] = useState<string | null>(localStorage.getItem('username'));
  const [displayName, setDisplayName] = useState<string | null>(localStorage.getItem('displayName'));
  const [permissions, setPermissions] = useState<string[]>(() => {
    try {
      return JSON.parse(localStorage.getItem('permissions') || '[]');
    } catch {
      return [];
    }
  });

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      localStorage.setItem('token', token);
      if (role) localStorage.setItem('role', role);
      if (username) localStorage.setItem('username', username);
      if (displayName) localStorage.setItem('displayName', displayName);
      localStorage.setItem('permissions', JSON.stringify(permissions));
    } else {
      delete axios.defaults.headers.common['Authorization'];
      localStorage.removeItem('token');
      localStorage.removeItem('role');
      localStorage.removeItem('username');
      localStorage.removeItem('displayName');
      localStorage.removeItem('permissions');
    }
  }, [token, role, username, displayName, permissions]);

  const login = (newToken: string, newRole: string, newUsername?: string, newDisplayName?: string, newPermissions?: string[]) => {
    setToken(newToken);
    setRole(newRole);
    if (newUsername) setUsername(newUsername);
    if (newDisplayName) setDisplayName(newDisplayName);
    if (newPermissions) setPermissions(newPermissions);
  };

  const logout = () => {
    setToken(null);
    setRole(null);
    setUsername(null);
    setDisplayName(null);
    setPermissions([]);
  };

  const hasPermission = (perm: string) => {
    if (role?.toUpperCase() === 'ADMIN') return true;
    return permissions.includes(perm);
  };

  const hasRole = (r: string) => {
    if (!role) return false;
    return role.toUpperCase() === r.toUpperCase();
  };

  return (
    <AuthContext.Provider value={{
      token,
      role,
      username,
      displayName,
      permissions,
      login,
      logout,
      isAuthenticated: !!token,
      hasPermission,
      hasRole
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
