import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import RoleRoute from './components/ui/RoleRoute';
import HomeRedirect from './components/ui/HomeRedirect';
import Layout from './components/layout/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Profile from './pages/Profile';
import ExercisePlan from './pages/ExercisePlan';
import Onboarding from './pages/OnBoarding';
import AdminDashboard from './pages/AdminDashboard';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/login"    element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/onboarding" element={<Onboarding />} />

          {/* Protected routes */}
          <Route path="/" element={
            <RoleRoute allowRoles={['admin', 'client']}>
              <Layout />
            </RoleRoute>
          }>
            <Route index element={<HomeRedirect />} />
            <Route path="dashboard" element={<RoleRoute allowRoles={['client']} redirectTo="/admin"><Dashboard /></RoleRoute>} />
            <Route path="profile" element={<RoleRoute allowRoles={['client']} redirectTo="/admin"><Profile /></RoleRoute>} />
            <Route path="exercise" element={<RoleRoute allowRoles={['client']} redirectTo="/admin"><ExercisePlan /></RoleRoute>} />
            <Route path="admin" element={<RoleRoute allowRoles={['admin']} redirectTo="/dashboard"><AdminDashboard /></RoleRoute>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
