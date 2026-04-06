import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { registerClient, type ActivityLevel, type Gender } from '../services/backendApi';

/* ── Constants ────────────────────────────────────────────── */
const CONDITIONS = [
  { value: 'diabetes',     label: 'Diabetes',            icon: '🩺' },
  { value: 'hypertension', label: 'Hypertension',        icon: '❤️' },
  { value: 'obesity',      label: 'Obesity / Weight Mgmt', icon: '⚖️' },
  { value: 'depression',   label: 'Depression / Low Mood', icon: '🧠' },
  { value: 'cardiac rehab',label: 'Cardiac Rehab',       icon: '💓' },
  { value: 'elderly',      label: 'Older Adults',        icon: '🧓' },
  { value: 'general',      label: 'General Wellness',    icon: '🌿' },
] as const;

const GOALS = [
  { key: 'goal_lose_weight',  label: 'Lose Weight',       icon: '🔥' },
  { key: 'goal_build_muscle', label: 'Build Muscle',      icon: '💪' },
  { key: 'goal_endurance',    label: 'Improve Endurance', icon: '🏃' },
] as const;

const STEPS = ['Personal Info', 'Health Profile', 'Goals & Account'];

/* ── Step indicator ───────────────────────────────────────── */
function StepBar({ current }: { current: number }) {
  return (
    <div className="flex items-center justify-center gap-0 mb-8">
      {STEPS.map((label, idx) => (
        <div key={label} className="flex items-center">
          <div className="flex flex-col items-center gap-1">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300 ${
              idx < current  ? 'bg-olive text-white' :
              idx === current ? 'bg-orange text-white shadow-lg scale-110' :
              'bg-cream text-dark/40'
            }`}>
              {idx < current ? '✓' : idx + 1}
            </div>
            <span className={`text-xs whitespace-nowrap transition-colors ${idx === current ? 'text-orange font-semibold' : 'text-dark/40'}`}>
              {label}
            </span>
          </div>
          {idx < STEPS.length - 1 && (
            <div className={`h-0.5 w-12 sm:w-20 mx-1 mb-5 transition-all duration-300 ${idx < current ? 'bg-olive' : 'bg-cream'}`} />
          )}
        </div>
      ))}
    </div>
  );
}

/* ── Field wrapper ────────────────────────────────────────── */
function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="block text-xs font-semibold text-olive/80 uppercase tracking-wider">
        {label} {required && <span className="text-orange">*</span>}
      </label>
      {children}
    </div>
  );
}

/* ── Main ─────────────────────────────────────────────────── */
export default function Register() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({
    name: '', email: '', password: '', confirmPassword: '',
    age: '30', gender: '' as Gender | '',
    height_cm: '170', weight_kg: '70',
    selectedConditions: [] as string[], otherCondition: '',
    medications: '', injuries: '',
    activity_level: 'sedentary' as ActivityLevel,
    exercise_days_per_month: '4',
    goal_lose_weight: false, goal_build_muscle: false, goal_endurance: false,
    mood: '', motivation_text: '',
  });
  const [error, setError]     = useState('');
  const [loading, setLoading] = useState(false);

  const set = (field: string, value: string | boolean) =>
    setForm((p) => ({ ...p, [field]: value }));

  const toggleCondition = (v: string) =>
    setForm((p) => ({
      ...p,
      selectedConditions: p.selectedConditions.includes(v)
        ? p.selectedConditions.filter((x) => x !== v)
        : [...p.selectedConditions, v],
    }));

  const toList = (v: string) => v.split(',').map((x) => x.trim()).filter(Boolean);

  /* Validation per step */
  const validateStep = (): string => {
    if (step === 0) {
      if (!form.name.trim()) return 'Please enter your full name.';
      if (!form.email.trim()) return 'Please enter your email.';
      if (!form.gender) return 'Please select a gender.';
      if (Number(form.age) < 18) return 'You must be at least 18 years old.';
    }
    if (step === 1) {
      if (form.selectedConditions.length === 0 && !form.otherCondition.trim())
        return 'Please select at least one medical condition.';
    }
    if (step === 2) {
      if (form.password.length < 6) return 'Password must be at least 6 characters.';
      if (form.password !== form.confirmPassword) return 'Passwords do not match.';
    }
    return '';
  };

  const nextStep = () => {
    const err = validateStep();
    if (err) { setError(err); return; }
    setError('');
    setStep((s) => s + 1);
  };

  const prevStep = () => { setError(''); setStep((s) => s - 1); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const err = validateStep();
    if (err) { setError(err); return; }
    setError('');
    setLoading(true);
    try {
      await registerClient({
        name: form.name, email: form.email, password: form.password,
        age: Number(form.age), gender: form.gender as Gender,
        height_cm: Number(form.height_cm), weight_kg: Number(form.weight_kg),
        diseases: [...form.selectedConditions, ...toList(form.otherCondition)],
        medications: toList(form.medications),
        injuries:    toList(form.injuries),
        activity_level: form.activity_level,
        exercise_days_per_month: Number(form.exercise_days_per_month),
        goal_lose_weight: form.goal_lose_weight,
        goal_build_muscle: form.goal_build_muscle,
        goal_endurance: form.goal_endurance,
        mood:            form.mood || undefined,
        motivation_text: form.motivation_text || undefined,
      });
      navigate('/login');
    } catch {
      setError('Registration failed. Please check your information and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left hero */}
      <div className="hidden lg:flex lg:w-5/12 bg-gradient-to-br from-dark via-olive/80 to-olive flex-col justify-center p-12 relative overflow-hidden">
        <div className="absolute top-[-60px] right-[-60px] w-64 h-64 bg-gold/20 rounded-full blur-3xl" />
        <div className="absolute bottom-[-40px] left-[-40px] w-48 h-48 bg-orange/20 rounded-full blur-3xl" />
        <div className="relative z-10 space-y-6 animate-fade-in">
          <div>
            <span className="text-5xl animate-float inline-block">🌿</span>
            <h1 className="font-heading text-3xl font-bold text-white mt-3">
              SportRX <span className="text-gold">AI</span>
            </h1>
            <p className="text-white/50 text-sm mt-1">Your AI-powered medical fitness coach</p>
          </div>

          <div className="space-y-4">
            {[
              { icon: '🤖', title: 'AI Plan Generation', desc: 'Personalized 7-day plans via Llama 3.3' },
              { icon: '📚', title: 'Medical RAG', desc: 'ADA, ESC, WHO guidelines via Pinecone' },
              { icon: '📊', title: 'Risk Analysis', desc: 'ML-based health risk scoring' },
              { icon: '🔄', title: 'Adaptive Plans', desc: 'Evolves every 2 weeks with check-ins' },
            ].map((f) => (
              <div key={f.title} className="flex items-start gap-3">
                <span className="text-xl shrink-0">{f.icon}</span>
                <div>
                  <p className="text-white font-semibold text-sm">{f.title}</p>
                  <p className="text-white/50 text-xs">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right form */}
      <div className="flex-1 flex items-start justify-center px-6 py-10 bg-cream overflow-y-auto">
        <div className="w-full max-w-lg animate-slide-up">
          {/* Mobile logo */}
          <div className="text-center mb-6 lg:hidden">
            <h1 className="font-heading text-2xl font-bold text-olive">🌿 SportRX <span className="text-orange">AI</span></h1>
          </div>

          <div className="bg-white rounded-3xl shadow-xl p-8 border border-olive/10">
            <div className="mb-6">
              <h2 className="font-heading text-2xl font-bold text-dark">Create your account</h2>
              <p className="text-dark/40 text-sm mt-1">Step {step + 1} of {STEPS.length} — {STEPS[step]}</p>
            </div>

            <StepBar current={step} />

            {error && (
              <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-600 rounded-xl px-4 py-3 mb-5 text-sm animate-scale-in">
                <span>⚠</span> {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* ── STEP 0: Personal Info ── */}
              {step === 0 && (
                <div className="space-y-4 animate-slide-up">
                  <Field label="Full Name" required>
                    <input type="text" value={form.name} required placeholder="Ahmed Benali"
                      onChange={(e) => set('name', e.target.value)} className="input-field" />
                  </Field>

                  <Field label="Email" required>
                    <input type="email" value={form.email} required placeholder="name@example.com"
                      onChange={(e) => set('email', e.target.value)} className="input-field" />
                  </Field>

                  <div className="grid grid-cols-2 gap-3">
                    <Field label="Age" required>
                      <input type="number" min={18} max={120} value={form.age} required
                        onChange={(e) => set('age', e.target.value)} className="input-field" />
                    </Field>
                    <Field label="Gender" required>
                      <select value={form.gender} onChange={(e) => set('gender', e.target.value)} className="input-field">
                        <option value="" disabled>Select...</option>
                        <option value="male">Male</option>
                        <option value="female">Female</option>
                      </select>
                    </Field>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <Field label="Height (cm)" required>
                      <input type="number" min={100} max={250} step="0.1" value={form.height_cm}
                        onChange={(e) => set('height_cm', e.target.value)} className="input-field" />
                    </Field>
                    <Field label="Weight (kg)" required>
                      <input type="number" min={20} max={300} step="0.1" value={form.weight_kg}
                        onChange={(e) => set('weight_kg', e.target.value)} className="input-field" />
                    </Field>
                  </div>
                </div>
              )}

              {/* ── STEP 1: Health Profile ── */}
              {step === 1 && (
                <div className="space-y-4 animate-slide-up">
                  <Field label="Medical Conditions" required>
                    <div className="grid grid-cols-1 gap-2 bg-cream rounded-2xl p-4">
                      {CONDITIONS.map((c) => (
                        <label key={c.value} className={`flex items-center gap-3 p-2 rounded-xl cursor-pointer transition-all ${
                          form.selectedConditions.includes(c.value) ? 'bg-olive/10 border border-olive/30' : 'hover:bg-white/60'
                        }`}>
                          <input type="checkbox" checked={form.selectedConditions.includes(c.value)}
                            onChange={() => toggleCondition(c.value)} />
                          <span>{c.icon}</span>
                          <span className="text-sm text-dark">{c.label}</span>
                        </label>
                      ))}
                    </div>
                  </Field>

                  <Field label="Other Condition">
                    <input type="text" value={form.otherCondition} placeholder="E.g. arthritis, asthma..."
                      onChange={(e) => set('otherCondition', e.target.value)} className="input-field" />
                  </Field>

                  <Field label="Medications (comma-separated)">
                    <input type="text" value={form.medications} placeholder="E.g. metformin, lisinopril..."
                      onChange={(e) => set('medications', e.target.value)} className="input-field" />
                  </Field>

                  <Field label="Injuries or Limitations (comma-separated)">
                    <input type="text" value={form.injuries} placeholder="E.g. knee pain, lower back..."
                      onChange={(e) => set('injuries', e.target.value)} className="input-field" />
                  </Field>

                  <div className="grid grid-cols-2 gap-3">
                    <Field label="Activity Level">
                      <select value={form.activity_level} onChange={(e) => set('activity_level', e.target.value)} className="input-field">
                        <option value="sedentary">Sedentary</option>
                        <option value="light">Light</option>
                        <option value="moderate">Moderate</option>
                        <option value="active">Active</option>
                        <option value="very_active">Very Active</option>
                      </select>
                    </Field>
                    <Field label="Exercise Days / Month">
                      <input type="number" min={0} max={31} value={form.exercise_days_per_month}
                        onChange={(e) => set('exercise_days_per_month', e.target.value)} className="input-field" />
                    </Field>
                  </div>
                </div>
              )}

              {/* ── STEP 2: Goals & Account ── */}
              {step === 2 && (
                <div className="space-y-4 animate-slide-up">
                  <Field label="Your Goals">
                    <div className="grid grid-cols-3 gap-2">
                      {GOALS.map(({ key, label, icon }) => (
                        <button
                          key={key}
                          type="button"
                          onClick={() => set(key, !form[key as keyof typeof form])}
                          className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border-2 text-sm font-medium transition-all ${
                            form[key as keyof typeof form]
                              ? 'border-olive bg-olive/10 text-olive'
                              : 'border-cream text-dark/50 hover:border-olive/30'
                          }`}
                        >
                          <span className="text-2xl">{icon}</span>
                          {label}
                        </button>
                      ))}
                    </div>
                  </Field>

                  <Field label="Current Mood (optional)">
                    <input type="text" value={form.mood} placeholder="e.g. motivated, stressed, tired..."
                      onChange={(e) => set('mood', e.target.value)} className="input-field" />
                  </Field>

                  <Field label="Motivation Notes (optional)">
                    <textarea value={form.motivation_text} rows={2}
                      placeholder="Tell us about your goals or constraints..."
                      onChange={(e) => set('motivation_text', e.target.value)}
                      className="input-field resize-none" />
                  </Field>

                  <Field label="Password" required>
                    <input type="password" value={form.password} required placeholder="Min. 6 characters"
                      onChange={(e) => set('password', e.target.value)} className="input-field" />
                  </Field>

                  <Field label="Confirm Password" required>
                    <input type="password" value={form.confirmPassword} required placeholder="Repeat password"
                      onChange={(e) => set('confirmPassword', e.target.value)} className="input-field" />
                  </Field>
                </div>
              )}

              {/* Navigation buttons */}
              <div className="flex gap-3 pt-2">
                {step > 0 && (
                  <button type="button" onClick={prevStep} className="btn-secondary flex-1">
                    ← Back
                  </button>
                )}
                {step < STEPS.length - 1 ? (
                  <button type="button" onClick={nextStep} className="btn-primary flex-1">
                    Continue →
                  </button>
                ) : (
                  <button type="submit" disabled={loading} className="btn-primary flex-1">
                    {loading ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                        </svg>
                        Creating account...
                      </span>
                    ) : '🚀 Create Account'}
                  </button>
                )}
              </div>
            </form>

            <p className="text-center text-sm text-dark/40 mt-5">
              Already have an account?{' '}
              <Link to="/login" className="text-orange hover:text-orange/80 font-semibold">Sign in</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
