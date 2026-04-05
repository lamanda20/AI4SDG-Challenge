import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function Profile() {
  const { userId } = useAuth();
  const [client, setClient] = useState<any>(null);

  useEffect(() => {
    if (userId) api.get(`/users/${userId}`).then((r) => setClient(r.data));
  }, [userId]);

  if (!client) return <p className="text-olive opacity-60 text-center mt-20">Loading...</p>;

  const bio = client.biometrics;

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
            ['Condition', client.chronic_condition],
          ].map(([label, value]) => (
            <div key={label} className="bg-cream rounded-xl p-3">
              <p className="text-xs text-olive opacity-60 mb-1">{label}</p>
              <p className="font-medium text-dark">{value}</p>
            </div>
          ))}
        </div>
      </div>

      {bio && (
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <h2 className="font-heading text-xl font-semibold text-olive mb-4">Biometrics</h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            {[
              ['HRV', `${bio.hrv ?? '—'} ms`],
              ['Daily Steps', bio.daily_steps ?? '—'],
              ['BMI', bio.bmi ?? '—'],
              ['HbA1c', bio.hba1c ?? '—'],
              ['Blood Pressure', bio.blood_pressure ?? '—'],
              ['VO2 Max', bio.vo2_max ?? '—'],
              ['Mood Score', `${bio.mood_score} / 10`],
            ].map(([label, value]) => (
              <div key={label} className="bg-cream rounded-xl p-3">
                <p className="text-xs text-olive opacity-60 mb-1">{label}</p>
                <p className="font-medium text-dark">{value}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
