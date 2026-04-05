import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import api from '../services/api';

interface AuthContextType {
  isAuthenticated: boolean;
  userId: number | null;
  role: string | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userId, setUserId]   = useState<number | null>(null);
  const [role, setRole]       = useState<string | null>(null);
  const [token, setToken]     = useState<string | null>(null);

  // Restaurer la session au reload
  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    const savedUserId = localStorage.getItem('userId');
    const savedRole = localStorage.getItem('role');
    if (savedToken) {
      setToken(savedToken);
      setUserId(savedUserId ? parseInt(savedUserId) : null);
      setRole(savedRole);
      setIsAuthenticated(true);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await api.post('/auth/login', formData.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    const data = response.data;
    setIsAuthenticated(true);
    setUserId(data.user_id);
    setRole(data.role);
    setToken(data.access_token);
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('userId', data.user_id.toString());
    localStorage.setItem('role', data.role);
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
    <AuthContext.Provider value={{ isAuthenticated, userId, role, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
}
