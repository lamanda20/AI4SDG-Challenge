import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';
import { getMyProfile, type UserProfileResponse } from '../services/backendApi';

export default function Profile() {
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
        setError('Unable to load profile.');
      }
    };

    void loadProfile();
  }, [isAdmin]);

  if (isAdmin) return <Navigate to="/admin" replace />;

  if (error) return <p className="text-red-600 text-center mt-20">{error}</p>;

  if (!client) return <p className="text-olive opacity-60 text-center mt-20">Loading...</p>;

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <h1 className="font-heading text-3xl font-bold text-olive">My Profile</h1>

      <div className="bg-white rounded-2xl p-6 shadow-md">
        <h2 className="font-heading text-xl font-semibold text-olive mb-4">Personal Info</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          {[
            ['Name', client.name],
            ['Email', client.email],
            ['Age', client.age],
            ['Gender', client.gender ?? '—'],
            ['Weight', `${client.weight_kg} kg`],
            ['Height', `${client.height_cm} cm`],
            ['Activity', client.activity_level],
          ].map(([label, value]) => (
            <div key={label} className="bg-cream rounded-xl p-3">
              <p className="text-xs text-olive opacity-60 mb-1">{label}</p>
              <p className="font-medium text-dark">{value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-md">
        <h2 className="font-heading text-xl font-semibold text-olive mb-4">Health Context</h2>
        <div className="grid grid-cols-1 gap-4 text-sm">
          <div className="bg-cream rounded-xl p-3">
            <p className="text-xs text-olive opacity-60 mb-1">Diseases</p>
            <p className="font-medium text-dark">{client.diseases.join(', ') || 'None reported'}</p>
          </div>
          <div className="bg-cream rounded-xl p-3">
            <p className="text-xs text-olive opacity-60 mb-1">Latest Plan Risk Level</p>
            <p className="font-medium text-dark">{client.latest_plan?.risk_level ?? 'No plan yet'}</p>
          </div>
          <div className="bg-cream rounded-xl p-3">
            <p className="text-xs text-olive opacity-60 mb-1">Latest Sentiment</p>
            <p className="font-medium text-dark">{client.latest_plan?.sentiment_label ?? 'No analysis yet'}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
