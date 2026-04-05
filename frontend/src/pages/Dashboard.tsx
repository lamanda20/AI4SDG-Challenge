import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function Dashboard() {
  const { userId } = useAuth();
  const [client, setClient] = useState<any>(null);

  useEffect(() => {
    if (userId) {
      api.get(`/users/${userId}`).then((res) => setClient(res.data));
    }
  }, [userId]);

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
          { label: 'Daily Steps',    value: client.biometrics?.daily_steps ?? '—',  unit: 'steps',  color: 'bg-olive' },
          { label: 'HRV',            value: client.biometrics?.hrv ?? '—',          unit: 'ms',     color: 'bg-orange' },
          { label: 'Mood Score',     value: client.biometrics?.mood_score ?? '—',   unit: '/ 10',   color: 'bg-apricot' },
          { label: 'BMI',            value: client.biometrics?.bmi ?? '—',          unit: '',       color: 'bg-gold' },
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
          <div><span className="opacity-60">Condition:</span> <span className="font-medium">{client.chronic_condition}</span></div>
          <div><span className="opacity-60">Age:</span> <span className="font-medium">{client.age}</span></div>
          <div><span className="opacity-60">Gender:</span> <span className="font-medium">{client.gender ?? '—'}</span></div>
          <div><span className="opacity-60">HbA1c:</span> <span className="font-medium">{client.biometrics?.hba1c ?? '—'}</span></div>
        </div>
      </div>

      {/* Feedback Card */}
      <div className="bg-white rounded-2xl p-6 shadow-md border-l-4 border-apricot">
        <h2 className="font-heading text-xl font-semibold text-olive mb-2">Latest Feedback</h2>
        <p className="text-dark italic opacity-80">
          "{client.biometrics?.recent_feedback ?? 'No feedback yet.'}"
        </p>
      </div>
    </div>
  );
}
