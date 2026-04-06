import { type ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

type RoleRouteProps = {
  children: ReactNode;
  allowRoles: Array<'admin' | 'client'>;
  redirectTo?: string;
};

export default function RoleRoute({ children, allowRoles, redirectTo = '/login' }: RoleRouteProps) {
  const { isAuthenticated, isInitializing, role } = useAuth();

  if (isInitializing) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-olive opacity-70">Restoring session...</p>
      </div>
    );
  }

  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (!role || !allowRoles.includes(role as 'admin' | 'client')) return <Navigate to={redirectTo} replace />;

  return <>{children}</>;
}
