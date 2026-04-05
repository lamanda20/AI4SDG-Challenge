import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function HomeRedirect() {
  const { role, isInitializing, isAuthenticated } = useAuth();

  if (isInitializing) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-olive opacity-70">Restoring session...</p>
      </div>
    );
  }

  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Navigate to={role === 'admin' ? '/admin' : '/dashboard'} replace />;
}
