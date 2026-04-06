import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function Navbar() {
  const { logout, role } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path: string) =>
    pathname === path ? 'nav-link nav-link-active' : 'nav-link';

  return (
    <nav className="sticky top-0 z-50 bg-olive/95 backdrop-blur-md text-white px-6 py-0 shadow-lg border-b border-white/10">
      <div className="max-w-6xl mx-auto flex justify-between items-center h-16">
        {/* Logo */}
        <Link
          to={role === 'admin' ? '/admin' : '/dashboard'}
          className="flex items-center gap-2 group"
        >
          <span className="text-2xl group-hover:animate-float">🌿</span>
          <span className="font-heading text-xl font-bold tracking-wide text-white">
            SportRX <span className="text-gold">AI</span>
          </span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-6">
          {role === 'admin' ? (
            <>
              <Link to="/admin" className={isActive('/admin')}>
                Dashboard
              </Link>
            </>
          ) : (
            <>
              <Link to="/dashboard" className={isActive('/dashboard')}>
                Dashboard
              </Link>
              <Link to="/exercise" className={isActive('/exercise')}>
                Exercise Plan
              </Link>
              <Link to="/profile" className={isActive('/profile')}>
                Profile
              </Link>
            </>
          )}

          {/* Role badge */}
          {role && (
            <span className="badge bg-white/15 text-white text-xs uppercase tracking-widest">
              {role === 'admin' ? '⚙ Admin' : '👤 Client'}
            </span>
          )}

          {/* Logout */}
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-sm font-medium text-white/70 hover:text-apricot transition-colors duration-200"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
