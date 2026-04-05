import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function Navbar() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-olive text-white px-6 py-4 flex justify-between items-center shadow-md">
      <Link to="/dashboard" className="font-heading text-xl font-bold tracking-wide">
        🌿 SportRX AI
      </Link>
      <div className="flex gap-6 text-sm font-medium">
        <Link to="/dashboard" className="hover:text-gold transition-colors">Dashboard</Link>
        <Link to="/profile"   className="hover:text-gold transition-colors">Profile</Link>
        <Link to="/exercise"  className="hover:text-gold transition-colors">Exercise Plan</Link>
        <button onClick={handleLogout} className="hover:text-apricot transition-colors">
          Logout
        </button>
      </div>
    </nav>
  );
}
