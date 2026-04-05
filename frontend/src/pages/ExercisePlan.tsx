import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';
import {
  getMyPlans,
  submitCheckin,
  type CheckinPayload,
  type TrainingPlanResponse,
} from '../services/backendApi';

type WeeklyDayPlan = {
  activity?: string;
  duration_min?: number;
  intensity?: string;
  notes?: string;
};

const DAYS_ORDER = [
  'monday',
  'tuesday',
  'wednesday',
  'thursday',
  'friday',
  'saturday',
  'sunday',
] as const;

const DAY_LABELS: Record<(typeof DAYS_ORDER)[number], string> = {
  monday: 'Monday',
  tuesday: 'Tuesday',
  wednesday: 'Wednesday',
  thursday: 'Thursday',
  friday: 'Friday',
  saturday: 'Saturday',
  sunday: 'Sunday',
};

function getRiskBadgeClasses(level: string) {
  const value = level.toLowerCase();
  if (value === 'low') return 'bg-emerald-100 text-emerald-700';
  if (value === 'moderate') return 'bg-amber-100 text-amber-700';
  if (value === 'high' || value === 'critical') return 'bg-red-100 text-red-700';
  return 'bg-stone-100 text-stone-700';
}

function getIntensityBadgeClasses(level: string) {
  const value = level.toLowerCase();
  if (value === 'light') return 'bg-sky-100 text-sky-700';
  if (value === 'moderate') return 'bg-indigo-100 text-indigo-700';
  if (value === 'vigorous' || value === 'high') return 'bg-fuchsia-100 text-fuchsia-700';
  if (value === 'rest') return 'bg-stone-100 text-stone-700';
  return 'bg-slate-100 text-slate-700';
}

function parseWeeklyPlan(weeklyPlan: TrainingPlanResponse['weekly_plan']) {
  return DAYS_ORDER.map((day) => {
    const raw = weeklyPlan?.[day] as WeeklyDayPlan | undefined;
    return {
      day,
      label: DAY_LABELS[day],
      activity: raw?.activity ?? 'Not specified',
      durationMin: raw?.duration_min ?? null,
      intensity: raw?.intensity ?? 'unknown',
      notes: raw?.notes ?? '',
    };
  });
}

export default function ExercisePlan() {
  const { role } = useAuth();
  const isAdmin = role === 'admin';
  const [plans, setPlans] = useState<TrainingPlanResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [checkin, setCheckin] = useState<CheckinPayload>({
    sessions_completed: 0,
    avg_energy_level: 5,
    avg_pain_level: 0,
    feedback_text: '',
    mood_text: '',
  });

  const loadPlans = async () => {
    if (isAdmin) {
      setLoading(false);
      return;
    }

    setError('');
    try {
      const data = await getMyPlans();
      setPlans(data);
    } catch {
      setError('Unable to load plans.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadPlans();
  }, [isAdmin]);

  if (isAdmin) return <Navigate to="/admin" replace />;

  const latestPlan = plans.length > 0 ? plans[plans.length - 1] : null;

  const handleCheckinSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await submitCheckin(checkin);
      await loadPlans();
    } catch {
      setError('Check-in failed. Verify values and try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const weeklyPlan = latestPlan ? parseWeeklyPlan(latestPlan.weekly_plan) : [];

  return (
    <div className="space-y-6">
      <h1 className="font-heading text-3xl font-bold text-olive">Exercise Plan</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 rounded-xl px-4 py-3 text-sm">
          {error}
        </div>
      )}

      <div className="bg-white rounded-2xl p-6 shadow-md border border-olive/10">
        <h2 className="font-heading text-xl font-semibold text-olive mb-3">Latest LLM Plan</h2>
        {loading ? (
          <p className="text-dark opacity-60">Loading latest plan...</p>
        ) : !latestPlan ? (
          <p className="text-dark opacity-60">No generated plan yet. Complete registration or a check-in.</p>
        ) : (
          <div className="space-y-6 text-sm text-dark">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-cream rounded-xl p-3">
                <span className="opacity-60">Week</span>
                <p className="font-semibold text-lg">{latestPlan.week_number}</p>
              </div>
              <div className="bg-cream rounded-xl p-3">
                <span className="opacity-60">Risk</span>
                <div className="mt-1">
                  <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-semibold ${getRiskBadgeClasses(latestPlan.risk_level)}`}>
                    {latestPlan.risk_level}
                  </span>
                </div>
              </div>
              <div className="bg-cream rounded-xl p-3">
                <span className="opacity-60">Sentiment</span>
                <p className="font-semibold mt-1 capitalize">{latestPlan.sentiment_label}</p>
              </div>
              <div className="bg-cream rounded-xl p-3">
                <span className="opacity-60">Intensity</span>
                <div className="mt-1">
                  <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-semibold ${getIntensityBadgeClasses(latestPlan.recommended_intensity)}`}>
                    {latestPlan.recommended_intensity}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-cream/70 rounded-xl p-4 border border-olive/10">
              <p className="font-medium text-olive mb-1">Motivational Message</p>
              <p className="italic leading-relaxed">{latestPlan.motivational_message || 'No message available.'}</p>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
                <p className="font-medium text-amber-800 mb-2">Warnings</p>
                <ul className="list-disc pl-5 space-y-1 text-amber-900">
                  {(latestPlan.warnings.length ? latestPlan.warnings : ['No warnings']).map((w) => (
                    <li key={w}>{w}</li>
                  ))}
                </ul>
              </div>

              <div className="rounded-xl border border-sky-200 bg-sky-50 p-4">
                <p className="font-medium text-sky-900 mb-2">Medical Guidelines (RAG)</p>
                <ul className="list-disc pl-5 space-y-1 text-sky-950">
                  {(latestPlan.medical_guidelines.length ? latestPlan.medical_guidelines : ['No guideline snippet']).map((g) => (
                    <li key={g}>{g}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div>
              <p className="font-medium text-olive mb-3">Weekly Plan</p>
              <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-3">
                {weeklyPlan.map((dayPlan) => (
                  <div key={dayPlan.day} className="rounded-xl border border-olive/10 bg-white p-4 shadow-sm">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="font-semibold text-olive">{dayPlan.label}</h3>
                      <span className={`inline-flex px-2 py-1 rounded-full text-xs font-semibold ${getIntensityBadgeClasses(dayPlan.intensity)}`}>
                        {dayPlan.intensity}
                      </span>
                    </div>
                    <p className="mt-2 font-medium text-dark">{dayPlan.activity}</p>
                    <p className="text-xs text-dark/70 mt-1">
                      {dayPlan.durationMin ? `${dayPlan.durationMin} minutes` : 'Duration not specified'}
                    </p>
                    {dayPlan.notes && <p className="text-xs mt-2 text-dark/80">{dayPlan.notes}</p>}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-md">
        <h2 className="font-heading text-xl font-semibold text-olive mb-3">Submit Bi-Weekly Check-in</h2>
        <form className="space-y-4" onSubmit={handleCheckinSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-sm text-olive mb-1">Sessions Completed (0-14)</label>
              <input
                type="number"
                min={0}
                max={14}
                required
                value={checkin.sessions_completed}
                onChange={(e) => setCheckin((prev) => ({ ...prev, sessions_completed: Number(e.target.value) }))}
                className="w-full px-3 py-2 rounded-xl bg-cream"
              />
            </div>
            <div>
              <label className="block text-sm text-olive mb-1">Average Energy (1-10)</label>
              <input
                type="number"
                min={1}
                max={10}
                required
                value={checkin.avg_energy_level}
                onChange={(e) => setCheckin((prev) => ({ ...prev, avg_energy_level: Number(e.target.value) }))}
                className="w-full px-3 py-2 rounded-xl bg-cream"
              />
            </div>
            <div>
              <label className="block text-sm text-olive mb-1">Average Pain (0-10)</label>
              <input
                type="number"
                min={0}
                max={10}
                required
                value={checkin.avg_pain_level}
                onChange={(e) => setCheckin((prev) => ({ ...prev, avg_pain_level: Number(e.target.value) }))}
                className="w-full px-3 py-2 rounded-xl bg-cream"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-sm text-olive mb-1">Mood Text (optional)</label>
              <input
                type="text"
                value={checkin.mood_text ?? ''}
                onChange={(e) => setCheckin((prev) => ({ ...prev, mood_text: e.target.value }))}
                className="w-full px-3 py-2 rounded-xl bg-cream"
              />
            </div>
            <div>
              <label className="block text-sm text-olive mb-1">Feedback (optional)</label>
              <input
                type="text"
                value={checkin.feedback_text ?? ''}
                onChange={(e) => setCheckin((prev) => ({ ...prev, feedback_text: e.target.value }))}
                className="w-full px-3 py-2 rounded-xl bg-cream"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="px-5 py-3 rounded-full bg-orange text-white font-semibold disabled:opacity-60"
          >
            {submitting ? 'Submitting...' : 'Generate Updated Plan'}
          </button>
        </form>
      </div>
    </div>
  );
}
