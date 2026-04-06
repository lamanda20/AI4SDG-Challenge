import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { getMyProfile, loginClient } from '../services/backendApi';

interface AuthContextType {
  isAuthenticated: boolean;
  isInitializing: boolean;
  userId: number | null;
  role: string | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [userId, setUserId]   = useState<number | null>(null);
  const [role, setRole]       = useState<string | null>(null);
  const [token, setToken]     = useState<string | null>(null);

  // Restaurer la session au reload
  useEffect(() => {
    const restoreSession = async () => {
      const savedToken = localStorage.getItem('token');
      if (!savedToken) {
        setIsInitializing(false);
        return;
      }

      setToken(savedToken);

      const savedRole = localStorage.getItem('role');
      if (savedRole) {
        setRole(savedRole);
      }

      const savedUserId = localStorage.getItem('userId');
      if (savedUserId) {
        setUserId(parseInt(savedUserId, 10));
      }

      if (savedUserId && savedRole) {
        setIsAuthenticated(true);
        setIsInitializing(false);
        return;
      }

      try {
        const profile = await getMyProfile();
        setIsAuthenticated(true);
        setUserId(profile.id);
        localStorage.setItem('userId', profile.id.toString());
      } catch {
        localStorage.removeItem('token');
        localStorage.removeItem('userId');
        localStorage.removeItem('role');
        setIsAuthenticated(false);
        setToken(null);
        setRole(null);
      } finally {
        setIsInitializing(false);
      }
    };

    void restoreSession();
  }, []);

  const login = async (email: string, password: string) => {
    const data = await loginClient(email, password);
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('role', data.role);

    let authenticatedUserId: number | null = null;
    if (data.role !== 'admin') {
      const profile = await getMyProfile();
      authenticatedUserId = profile.id;
      localStorage.setItem('userId', profile.id.toString());
    }

    setIsAuthenticated(true);
    setUserId(authenticatedUserId);
    setRole(data.role);
    setToken(data.access_token);
    if (authenticatedUserId === null) {
      localStorage.removeItem('userId');
    }
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUserId(null);
    setRole(null);
    setToken(null);
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    localStorage.removeItem('role');
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, isInitializing, userId, role, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
}
