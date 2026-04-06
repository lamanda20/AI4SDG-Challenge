import { useEffect, useRef, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';
import {
  getMyPlans, submitCheckin,
  type CheckinPayload, type TrainingPlanResponse,
} from '../services/backendApi';

/* ── Types ────────────────────────────────────────────────── */
type WeeklyDayPlan = {
  activity?: string; duration_min?: number;
  intensity?: string; notes?: string;
};

const DAYS_ORDER = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday'] as const;
const DAY_LABELS: Record<(typeof DAYS_ORDER)[number], string> = {
  monday:'Mon', tuesday:'Tue', wednesday:'Wed', thursday:'Thu',
  friday:'Fri', saturday:'Sat', sunday:'Sun',
};
const DAY_ICONS: Record<(typeof DAYS_ORDER)[number], string> = {
  monday:'💪', tuesday:'🏊', wednesday:'🧘', thursday:'🚴',
  friday:'🚶', saturday:'🏋', sunday:'🌿',
};

/* ── Helpers ──────────────────────────────────────────────── */
function getRiskClasses(level: string) {
  const v = level.toLowerCase();
  if (v === 'low')     return { bg: 'bg-emerald-100', text: 'text-emerald-700', dot: 'bg-emerald-500' };
  if (v === 'moderate') return { bg: 'bg-amber-100',  text: 'text-amber-700',   dot: 'bg-amber-500' };
  return                       { bg: 'bg-red-100',    text: 'text-red-700',     dot: 'bg-red-500' };
}

function getIntensityClasses(level: string) {
  const v = level.toLowerCase();
  if (v === 'light')            return 'bg-sky-100 text-sky-700';
  if (v === 'moderate')         return 'bg-indigo-100 text-indigo-700';
  if (v === 'vigorous' || v === 'high') return 'bg-purple-100 text-purple-700';
  if (v === 'rest')             return 'bg-stone-100 text-stone-500';
  return 'bg-slate-100 text-slate-600';
}

function getDayCardColor(idx: number) {
  const colors = [
    'border-olive/30 bg-olive/5',
    'border-sky-200 bg-sky-50',
    'border-emerald-200 bg-emerald-50',
    'border-indigo-200 bg-indigo-50',
    'border-orange/30 bg-orange/5',
    'border-purple-200 bg-purple-50',
    'border-gold/40 bg-gold/10',
  ];
  return colors[idx % colors.length];
}

function parseWeeklyPlan(weeklyPlan: TrainingPlanResponse['weekly_plan']) {
  return DAYS_ORDER.map((day) => {
    const raw = weeklyPlan?.[day] as WeeklyDayPlan | undefined;
    return {
      day, label: DAY_LABELS[day], icon: DAY_ICONS[day],
      activity:    raw?.activity    ?? 'Rest day',
      durationMin: raw?.duration_min ?? null,
      intensity:   raw?.intensity   ?? 'rest',
      notes:       raw?.notes       ?? '',
    };
  });
}

/* ── Slider input ─────────────────────────────────────────── */
function SliderField({ label, value, min, max, onChange, color = 'text-orange' }: {
  label: string; value: number; min: number; max: number;
  onChange: (v: number) => void; color?: string;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between items-center">
        <label className="text-sm font-medium text-dark/70">{label}</label>
        <span className={`text-lg font-bold font-heading ${color}`}>{value}</span>
      </div>
      <input
        type="range" min={min} max={max} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full"
      />
      <div className="flex justify-between text-xs text-dark/30">
        <span>{min}</span><span>{max}</span>
      </div>
    </div>
  );
}

/* ── Toast ────────────────────────────────────────────────── */
function Toast({ msg, type, onClose }: { msg: string; type: 'success'|'error'; onClose: () => void }) {
  useEffect(() => { const t = setTimeout(onClose, 3500); return () => clearTimeout(t); }, [onClose]);
  return (
    <div className={`toast ${type === 'success' ? 'toast-success' : 'toast-error'}`}>
      {type === 'success' ? '✅' : '⚠'} {msg}
    </div>
  );
}

/* ── Main component ───────────────────────────────────────── */
export default function ExercisePlan() {
  const { role } = useAuth();
  const checkinRef = useRef<HTMLDivElement>(null);
  const [plans, setPlans]         = useState<TrainingPlanResponse[]>([]);
  const [loading, setLoading]     = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast]         = useState<{ msg: string; type: 'success'|'error' } | null>(null);
  const [checkin, setCheckin]     = useState<CheckinPayload>({
    sessions_completed: 0, avg_energy_level: 5, avg_pain_level: 0,
    feedback_text: '', mood_text: '',
  });

  if (role === 'admin') return <Navigate to="/admin" replace />;

  const loadPlans = async () => {
    try { setPlans(await getMyPlans()); }
    catch { setToast({ msg: 'Unable to load plans.', type: 'error' }); }
    finally { setLoading(false); }
  };

  useEffect(() => { void loadPlans(); }, []);

  // Scroll to checkin if hash present
  useEffect(() => {
    if (window.location.hash === '#checkin') {
      setTimeout(() => checkinRef.current?.scrollIntoView({ behavior: 'smooth' }), 500);
    }
  }, [loading]);

  const handleCheckinSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await submitCheckin(checkin);
      setToast({ msg: 'Check-in submitted! New plan generated 🎉', type: 'success' });
      await loadPlans();
      setCheckin({ sessions_completed: 0, avg_energy_level: 5, avg_pain_level: 0, feedback_text: '', mood_text: '' });
    } catch {
      setToast({ msg: 'Check-in failed. Verify values and try again.', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const latestPlan = plans.length > 0 ? plans[plans.length - 1] : null;
  const weeklyPlan = latestPlan ? parseWeeklyPlan(latestPlan.weekly_plan) : [];
  const riskClasses = latestPlan ? getRiskClasses(latestPlan.risk_level) : null;

  return (
    <div className="max-w-5xl mx-auto space-y-6 page-enter">
      {toast && <Toast msg={toast.msg} type={toast.type} onClose={() => setToast(null)} />}

      <div className="flex items-center justify-between">
        <h1 className="font-heading text-3xl font-bold text-dark">Exercise Plan</h1>
        {latestPlan && (
          <span className="text-sm text-dark/40">
            Week {latestPlan.week_number} · Updated {new Date(latestPlan.created_at).toLocaleDateString()}
          </span>
        )}
      </div>

      {/* Plan card */}
      <div className="bg-white rounded-2xl shadow-md border border-olive/10 overflow-hidden">
        <div className="bg-gradient-to-r from-olive to-olive/80 px-6 py-4 flex items-center justify-between">
          <h2 className="font-heading text-lg font-semibold text-white">Latest AI-Generated Plan</h2>
          <span className="text-white/60 text-sm">🤖 Llama 3.3 · Pinecone RAG</span>
        </div>

        <div className="p-6 space-y-6">
          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => <div key={i} className="skeleton h-8" />)}
            </div>
          ) : !latestPlan ? (
            <div className="text-center py-12">
              <p className="text-5xl mb-3">📋</p>
              <p className="text-dark/50">No plan generated yet. Complete registration or a check-in.</p>
            </div>
          ) : (
            <>
              {/* Meta row */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { label: 'Week', content: <span className="text-2xl font-bold font-heading text-olive">{latestPlan.week_number}</span> },
                  {
                    label: 'Risk Level',
                    content: (
                      <span className={`badge ${riskClasses!.bg} ${riskClasses!.text}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${riskClasses!.dot} mr-1.5 inline-block`} />
                        {latestPlan.risk_level}
                      </span>
                    ),
                  },
                  {
                    label: 'Sentiment',
                    content: <span className="font-semibold capitalize text-dark">{latestPlan.sentiment_label}</span>,
                  },
                  {
                    label: 'Intensity',
                    content: (
                      <span className={`badge ${getIntensityClasses(latestPlan.recommended_intensity)}`}>
                        {latestPlan.recommended_intensity}
                      </span>
                    ),
                  },
                ].map(({ label, content }) => (
                  <div key={label} className="bg-cream/60 rounded-xl p-3">
                    <p className="text-xs text-dark/50 mb-1.5">{label}</p>
                    {content}
                  </div>
                ))}
              </div>

              {/* Motivational message */}
              <div className="bg-gradient-to-r from-gold/10 to-orange/10 rounded-xl p-4 border border-gold/20">
                <p className="text-xs font-semibold text-olive/70 uppercase tracking-wider mb-2">AI Message</p>
                <p className="italic text-dark/80 leading-relaxed">"{latestPlan.motivational_message || 'Keep going!'}"</p>
              </div>

              {/* Warnings & guidelines */}
              <div className="grid md:grid-cols-2 gap-4">
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
                  <p className="font-semibold text-amber-800 mb-2 flex items-center gap-1.5">
                    <span>⚠️</span> Warnings
                  </p>
                  <ul className="space-y-1.5">
                    {(latestPlan.warnings.length ? latestPlan.warnings : ['No warnings']).map((w) => (
                      <li key={w} className="text-sm text-amber-900 flex items-start gap-2">
                        <span className="mt-0.5 shrink-0">•</span>{w}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="rounded-xl border border-sky-200 bg-sky-50 p-4">
                  <p className="font-semibold text-sky-800 mb-2 flex items-center gap-1.5">
                    <span>📚</span> Medical Guidelines (RAG)
                  </p>
                  <ul className="space-y-1.5">
                    {(latestPlan.medical_guidelines.length ? latestPlan.medical_guidelines : ['No guideline retrieved']).map((g) => (
                      <li key={g} className="text-sm text-sky-900 flex items-start gap-2">
                        <span className="mt-0.5 shrink-0">•</span>{g}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Weekly plan grid */}
              <div>
                <p className="font-semibold text-dark mb-3 flex items-center gap-2">
                  📅 7-Day Program
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-7 gap-3">
                  {weeklyPlan.map((dayPlan, idx) => (
                    <div
                      key={dayPlan.day}
                      className={`rounded-xl border-2 ${getDayCardColor(idx)} p-3 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 animate-slide-up`}
                      style={{ animationDelay: `${idx * 0.05}s` }}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-dark/60 uppercase">{dayPlan.label}</span>
                        <span className="text-lg">{dayPlan.icon}</span>
                      </div>
                      <p className="text-sm font-semibold text-dark leading-tight">{dayPlan.activity}</p>
                      {dayPlan.durationMin && (
                        <p className="text-xs text-dark/50 mt-1">{dayPlan.durationMin} min</p>
                      )}
                      <span className={`badge text-xs mt-2 ${getIntensityClasses(dayPlan.intensity)}`}>
                        {dayPlan.intensity}
                      </span>
                      {dayPlan.notes && (
                        <p className="text-xs text-dark/50 mt-2 leading-tight italic">{dayPlan.notes}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Check-in form */}
      <div ref={checkinRef} id="checkin" className="bg-white rounded-2xl shadow-md overflow-hidden">
        <div className="bg-gradient-to-r from-orange to-apricot px-6 py-4">
          <h2 className="font-heading text-lg font-semibold text-white">📝 Bi-Weekly Check-in</h2>
          <p className="text-white/70 text-sm mt-0.5">Submit your progress to generate an updated plan</p>
        </div>

        <form className="p-6 space-y-6" onSubmit={handleCheckinSubmit}>
          <div className="grid md:grid-cols-3 gap-6">
            <SliderField
              label="Sessions Completed (0-14)"
              value={checkin.sessions_completed}
              min={0} max={14}
              onChange={(v) => setCheckin((p) => ({ ...p, sessions_completed: v }))}
              color="text-olive"
            />
            <SliderField
              label="Average Energy Level (1-10)"
              value={checkin.avg_energy_level}
              min={1} max={10}
              onChange={(v) => setCheckin((p) => ({ ...p, avg_energy_level: v }))}
              color="text-orange"
            />
            <SliderField
              label="Average Pain Level (0-10)"
              value={checkin.avg_pain_level ?? 0}
              min={0} max={10}
              onChange={(v) => setCheckin((p) => ({ ...p, avg_pain_level: v }))}
              color="text-red-500"
            />
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-dark/60 uppercase tracking-wider mb-1.5">
                How are you feeling? (optional)
              </label>
              <input
                type="text"
                value={checkin.mood_text ?? ''}
                onChange={(e) => setCheckin((p) => ({ ...p, mood_text: e.target.value }))}
                placeholder="e.g. motivated, tired, energetic..."
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-dark/60 uppercase tracking-wider mb-1.5">
                Session feedback (optional)
              </label>
              <input
                type="text"
                value={checkin.feedback_text ?? ''}
                onChange={(e) => setCheckin((p) => ({ ...p, feedback_text: e.target.value }))}
                placeholder="e.g. completed most sessions, felt strong..."
                className="input-field"
              />
            </div>
          </div>

          {/* Progress summary */}
          <div className="bg-cream/50 rounded-xl p-4 text-sm text-dark/70">
            <p className="font-medium text-dark mb-2">Your check-in summary:</p>
            <div className="flex flex-wrap gap-3">
              <span>✅ <b>{checkin.sessions_completed}/14</b> sessions</span>
              <span>⚡ Energy: <b>{checkin.avg_energy_level}/10</b></span>
              <span>😣 Pain: <b>{checkin.avg_pain_level}/10</b></span>
              {checkin.mood_text && <span>😊 Mood: <b>{checkin.mood_text}</b></span>}
            </div>
          </div>

          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                </svg>
                Generating new plan...
              </span>
            ) : '🚀 Generate Updated Plan'}
          </button>
        </form>
      </div>
    </div>
  );
}
