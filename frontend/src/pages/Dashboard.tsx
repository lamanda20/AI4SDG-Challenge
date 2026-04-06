import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Navigate, Link } from 'react-router-dom';
import { getMyProfile, type UserProfileResponse } from '../services/backendApi';

function SkeletonCard() {
  return <div className="skeleton h-28 w-full" />;
}

function StatCard({
  label, value, unit, color, icon, delay,
}: {
  label: string; value: string | number; unit: string;
  color: string; icon: string; delay: string;
}) {
  return (
    <div
      className={`${color} text-white rounded-2xl p-5 shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 animate-slide-up`}
      style={{ animationDelay: delay }}
    >
      <div className="flex justify-between items-start">
        <p className="text-sm font-medium opacity-80">{label}</p>
        <span className="text-2xl">{icon}</span>
      </div>
      <p className="text-3xl font-bold mt-2 font-heading">{value}</p>
      <p className="text-xs opacity-70 mt-0.5">{unit}</p>
    </div>
  );
}

function RiskBadge({ level }: { level?: string }) {
  if (!level) return null;
  const map: Record<string, string> = {
    low:      'bg-emerald-100 text-emerald-700',
    moderate: 'bg-amber-100 text-amber-700',
    high:     'bg-red-100 text-red-700',
    critical: 'bg-red-200 text-red-800',
  };
  return (
    <span className={`badge ${map[level.toLowerCase()] ?? 'bg-slate-100 text-slate-600'}`}>
      {level}
    </span>
  );
}

function IntensityBadge({ level }: { level?: string }) {
  if (!level) return null;
  const map: Record<string, string> = {
    light:    'bg-sky-100 text-sky-700',
    moderate: 'bg-indigo-100 text-indigo-700',
    vigorous: 'bg-purple-100 text-purple-700',
    high:     'bg-fuchsia-100 text-fuchsia-700',
  };
  return (
    <span className={`badge ${map[level.toLowerCase()] ?? 'bg-slate-100 text-slate-600'}`}>
      {level}
    </span>
  );
}

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 18) return 'Good afternoon';
  return 'Good evening';
}

export default function Dashboard() {
  const { role } = useAuth();
  const [client, setClient] = useState<UserProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  if (role === 'admin') return <Navigate to="/admin" replace />;

  useEffect(() => {
    getMyProfile()
      .then(setClient)
      .catch(() => setError('Unable to load dashboard data.'))
      .finally(() => setLoading(false));
  }, []);

  if (error) return (
    <div className="flex items-center justify-center h-64">
      <div className="bg-red-50 border border-red-200 text-red-600 rounded-2xl px-6 py-4 text-sm animate-scale-in">
        ⚠ {error}
      </div>
    </div>
  );

  return (
    <div className="max-w-5xl mx-auto space-y-6 page-enter">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          {loading ? (
            <div className="space-y-2">
              <div className="skeleton h-8 w-56" />
              <div className="skeleton h-4 w-40" />
            </div>
          ) : (
            <>
              <h1 className="font-heading text-3xl font-bold text-dark animate-fade-in">
                {getGreeting()}, <span className="text-olive">{client?.name.split(' ')[0]}</span> 🌿
              </h1>
              <p className="text-dark/50 mt-1 text-sm animate-fade-in" style={{ animationDelay: '0.1s' }}>
                Here's your wellness overview for today.
              </p>
            </>
          )}
        </div>

        <Link
          to="/exercise"
          className="btn-primary text-sm hidden sm:flex items-center gap-2"
        >
          View Plan →
        </Link>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
        ) : (
          <>
            <StatCard label="Weight"    value={client?.weight_kg ?? '—'} unit="kg"    color="bg-olive"   icon="⚖️" delay="0s"    />
            <StatCard label="Plans"     value={client?.total_plans ?? 0}  unit="total" color="bg-orange"  icon="📋" delay="0.1s"  />
            <StatCard label="Check-ins" value={client?.total_checkins ?? 0} unit="total" color="bg-apricot" icon="✅" delay="0.2s" />
            <StatCard
              label="Intensity"
              value={client?.latest_plan?.recommended_intensity ?? '—'}
              unit="current"
              color="bg-gold"
              icon="💪"
              delay="0.3s"
            />
          </>
        )}
      </div>

      {/* Two columns */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* Health Profile */}
        <div className="bg-white rounded-2xl p-6 shadow-md border-l-4 border-olive hover:shadow-lg transition-shadow animate-slide-up" style={{ animationDelay: '0.2s' }}>
          <h2 className="font-heading text-lg font-semibold text-olive mb-4 flex items-center gap-2">
            🏥 Health Profile
          </h2>
          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => <div key={i} className="skeleton h-5 w-full" />)}
            </div>
          ) : (
            <div className="space-y-3 text-sm">
              {[
                { label: 'Conditions', value: client?.diseases.join(', ') || 'None declared' },
                { label: 'Age',        value: client?.age ?? '—' },
                { label: 'Gender',     value: client?.gender ?? '—' },
                { label: 'Activity',   value: client?.activity_level ?? '—' },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between items-center py-1 border-b border-cream last:border-0">
                  <span className="text-dark/50 font-medium">{label}</span>
                  <span className="text-dark font-semibold capitalize">{String(value)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Latest Plan */}
        <div className="bg-white rounded-2xl p-6 shadow-md border-l-4 border-apricot hover:shadow-lg transition-shadow animate-slide-up" style={{ animationDelay: '0.3s' }}>
          <h2 className="font-heading text-lg font-semibold text-olive mb-4 flex items-center gap-2">
            🤖 AI Plan Overview
          </h2>
          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => <div key={i} className="skeleton h-5 w-full" />)}
            </div>
          ) : client?.latest_plan ? (
            <div className="space-y-4">
              <div className="flex gap-3 flex-wrap">
                <div className="text-xs text-dark/50">Risk</div>
                <RiskBadge level={client.latest_plan.risk_level} />
                <div className="text-xs text-dark/50 ml-2">Intensity</div>
                <IntensityBadge level={client.latest_plan.recommended_intensity} />
              </div>

              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${Math.min((client.latest_plan.week_number / 12) * 100, 100)}%` }}
                />
              </div>
              <p className="text-xs text-dark/40">Week {client.latest_plan.week_number} of your program</p>

              <p className="text-dark/70 italic text-sm leading-relaxed border-l-2 border-gold pl-3">
                "{client.latest_plan.motivational_message || 'No message yet.'}"
              </p>

              <Link to="/exercise" className="text-orange text-sm font-semibold hover:underline">
                See full plan →
              </Link>
            </div>
          ) : (
            <p className="text-dark/40 text-sm">No plan generated yet. Complete registration to get started.</p>
          )}
        </div>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 animate-slide-up" style={{ animationDelay: '0.4s' }}>
        {[
          { to: '/exercise', label: 'View Exercise Plan', icon: '🏃', color: 'border-orange text-orange' },
          { to: '/exercise#checkin', label: 'Submit Check-in', icon: '📝', color: 'border-olive text-olive' },
          { to: '/profile', label: 'My Profile', icon: '👤', color: 'border-gold text-gold' },
        ].map((action) => (
          <Link
            key={action.to}
            to={action.to}
            className={`flex items-center gap-3 p-4 bg-white rounded-2xl border-2 ${action.color}
              hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 font-medium text-sm`}
          >
            <span className="text-xl">{action.icon}</span>
            {action.label}
          </Link>
        ))}
      </div>
    </div>
  );
}
