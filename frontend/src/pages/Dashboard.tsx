import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';
import { getMyProfile, type UserProfileResponse } from '../services/backendApi';

export default function Dashboard() {
  const { role } = useAuth();
  const [client, setClient] = useState<UserProfileResponse | null>(null);
  const [error, setError] = useState('');

  const isAdmin = role === 'admin';

  useEffect(() => {
    if (isAdmin) return;

    const loadProfile = async () => {
      try {
        const profile = await getMyProfile();
        setClient(profile);
      } catch {
        setError('Unable to load dashboard data.');
      }
    };

    void loadProfile();
  }, [isAdmin]);

  if (isAdmin) return <Navigate to="/admin" replace />;

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-600 rounded-xl px-4 py-3">
        {error}
      </div>
    );
  }

  if (!client) return (
    <div className="flex items-center justify-center h-64">
      <p className="text-olive opacity-60 text-lg">Loading your dashboard...</p>
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-bold text-olive">
          Good morning, {client.name.split(' ')[0]} 🌿
        </h1>
        <p className="text-dark opacity-60 mt-1">Here's your wellness overview for today.</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Weight', value: client.weight_kg, unit: 'kg', color: 'bg-olive' },
          { label: 'Plans', value: client.total_plans, unit: 'total', color: 'bg-orange' },
          { label: 'Check-ins', value: client.total_checkins, unit: 'total', color: 'bg-apricot' },
          { label: 'Intensity', value: client.latest_plan?.recommended_intensity ?? '—', unit: '', color: 'bg-gold' },
        ].map((stat) => (
          <div key={stat.label} className={`${stat.color} text-white rounded-2xl p-5 shadow-md`}>
            <p className="text-sm opacity-80">{stat.label}</p>
            <p className="text-3xl font-bold mt-1">{stat.value}</p>
            <p className="text-xs opacity-70">{stat.unit}</p>
          </div>
        ))}
      </div>

      {/* Condition Card */}
      <div className="bg-white rounded-2xl p-6 shadow-md border-l-4 border-olive">
        <h2 className="font-heading text-xl font-semibold text-olive mb-2">Health Profile</h2>
        <div className="grid grid-cols-2 gap-4 text-sm text-dark">
          <div><span className="opacity-60">Diseases:</span> <span className="font-medium">{client.diseases.join(', ') || 'None'}</span></div>
          <div><span className="opacity-60">Age:</span> <span className="font-medium">{client.age}</span></div>
          <div><span className="opacity-60">Gender:</span> <span className="font-medium">{client.gender ?? '—'}</span></div>
          <div><span className="opacity-60">Activity:</span> <span className="font-medium">{client.activity_level}</span></div>
        </div>
      </div>

      {/* Feedback Card */}
      <div className="bg-white rounded-2xl p-6 shadow-md border-l-4 border-apricot">
        <h2 className="font-heading text-xl font-semibold text-olive mb-2">Latest Plan Summary</h2>
        <p className="text-dark italic opacity-80">
          "{client.latest_plan?.motivational_message ?? 'No generated plan yet.'}"
        </p>
      </div>
    </div>
  );
}
