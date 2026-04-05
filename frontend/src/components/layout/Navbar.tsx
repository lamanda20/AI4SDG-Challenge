import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function Navbar() {
  const { logout, role } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-olive text-white px-6 py-4 flex justify-between items-center shadow-md">
      <Link to={role === 'admin' ? '/admin' : '/dashboard'} className="font-heading text-xl font-bold tracking-wide">
        🌿 SportRX AI
      </Link>
      <div className="flex items-center gap-4 text-sm font-medium">
        {role && (
          <span className="rounded-full bg-white/15 px-3 py-1 text-xs font-semibold uppercase tracking-wide">
            {role === 'admin' ? 'Admin' : 'Client'}
          </span>
        )}
        <div className="flex gap-6">
          {role === 'admin' ? (
            <>
              <Link to="/admin" className="hover:text-gold transition-colors">Admin Dashboard</Link>
              <button onClick={handleLogout} className="hover:text-apricot transition-colors">Logout</button>
            </>
          ) : (
            <>
              <Link to="/dashboard" className="hover:text-gold transition-colors">Dashboard</Link>
              <Link to="/profile" className="hover:text-gold transition-colors">Profile</Link>
              <Link to="/exercise" className="hover:text-gold transition-colors">Exercise Plan</Link>
              <button onClick={handleLogout} className="hover:text-apricot transition-colors">Logout</button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
