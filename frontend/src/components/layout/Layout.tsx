import { Outlet, useLocation } from 'react-router-dom';
import Navbar from './Navbar';

export default function Layout() {
  const { pathname } = useLocation();

  return (
    <div className="min-h-screen bg-cream">
      <Navbar />
      <main key={pathname} className="max-w-5xl mx-auto px-4 sm:px-6 py-8 page-enter">
        <Outlet />
      </main>
    </div>
  );
}
