import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { registerClient, type ActivityLevel, type Gender } from '../services/backendApi';

const COVERED_CONDITIONS = [
  { value: 'diabetes', label: 'Diabetes' },
  { value: 'hypertension', label: 'Hypertension' },
  { value: 'obesity', label: 'Obesity / weight management' },
  { value: 'depression', label: 'Depression / low mood' },
  { value: 'cardiac rehab', label: 'Cardiac rehabilitation' },
  { value: 'elderly', label: 'Older adults / elderly' },
  { value: 'general', label: 'General wellness' },
] as const;

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    age: '30',
    gender: '' as Gender | '',
    height_cm: '170',
    weight_kg: '70',
    selectedConditions: [] as string[],
    otherCondition: '',
    medications: '',
    injuries: '',
    activity_level: 'sedentary' as ActivityLevel,
    exercise_days_per_month: '0',
    goal_lose_weight: false,
    goal_build_muscle: false,
    goal_endurance: false,
    mood: '',
    motivation_text: '',
  });
  const [error, setError]     = useState('');
  const [loading, setLoading] = useState(false);

  const update = (field: string, value: string | boolean) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const toList = (value: string) =>
    value.split(',').map((item) => item.trim()).filter(Boolean);

  const toggleCondition = (condition: string) => {
    setForm((prev) => {
      const selected = prev.selectedConditions.includes(condition)
        ? prev.selectedConditions.filter((item) => item !== condition)
        : [...prev.selectedConditions, condition];

      return { ...prev, selectedConditions: selected };
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (form.selectedConditions.length === 0 && !form.otherCondition.trim()) {
      setError('Please select at least one medical condition covered by the ML.');
      return;
    }
    if (!form.gender) {
      setError('Please select a gender.');
      return;
    }
    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setLoading(true);
    try {
      await registerClient({
        name: form.name,
        email: form.email,
        password: form.password,
        age: Number(form.age),
        gender: form.gender,
        height_cm: Number(form.height_cm),
        weight_kg: Number(form.weight_kg),
        diseases: [
          ...form.selectedConditions,
          ...toList(form.otherCondition),
        ],
        medications: toList(form.medications),
        injuries: toList(form.injuries),
        activity_level: form.activity_level,
        exercise_days_per_month: Number(form.exercise_days_per_month),
        goal_lose_weight: form.goal_lose_weight,
        goal_build_muscle: form.goal_build_muscle,
        goal_endurance: form.goal_endurance,
        mood: form.mood || undefined,
        motivation_text: form.motivation_text || undefined,
      });
      navigate('/login');
    } catch {
      setError('Registration failed. Check your values and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-cream flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="font-heading text-4xl font-bold text-olive mb-2">🌿 SportRX AI</h1>
          <p className="text-dark opacity-70">Start your wellness journey</p>
        </div>

        <div className="bg-white rounded-3xl shadow-lg p-8">
          <h2 className="font-heading text-2xl font-semibold text-olive mb-6">Create account</h2>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 rounded-xl px-4 py-3 mb-4 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-olive mb-1">Full Name</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => update('name', e.target.value)}
                required
                placeholder="Enter your full name"
                className="w-full px-4 py-3 rounded-2xl bg-cream border-2 border-transparent focus:border-olive focus:outline-none text-dark transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-olive mb-1">Email</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => update('email', e.target.value)}
                required
                placeholder="name@example.com"
                className="w-full px-4 py-3 rounded-2xl bg-cream border-2 border-transparent focus:border-olive focus:outline-none text-dark transition-all"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-olive mb-1">Age</label>
                <input
                  type="number"
                  min={18}
                  max={120}
                  value={form.age}
                  onChange={(e) => update('age', e.target.value)}
                  required
                  placeholder="Enter your age"
                  className="w-full px-4 py-3 rounded-2xl bg-cream border-2 border-transparent focus:border-olive focus:outline-none text-dark transition-all"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-olive mb-1">Gender</label>
                <select
                  value={form.gender}
                  onChange={(e) => update('gender', e.target.value as Gender | '')}
                  className="w-full px-4 py-3 rounded-2xl bg-cream border-2 border-transparent focus:border-olive focus:outline-none text-dark transition-all"
                >
                  <option value="" disabled>Select gender</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-olive mb-1">Height (cm)</label>
                <input
                  type="number"
                  min={100}
                  max={250}
                  step="0.1"
                  value={form.height_cm}
                  onChange={(e) => update('height_cm', e.target.value)}
                  required
                  placeholder="Height in cm"
                  className="w-full px-4 py-3 rounded-2xl bg-cream border-2 border-transparent focus:border-olive focus:outline-none text-dark transition-all"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-olive mb-1">Weight (kg)</label>
                <input
                  type="number"
                  min={20}
                  max={300}
                  step="0.1"
                  value={form.weight_kg}
                  onChange={(e) => update('weight_kg', e.target.value)}
                  required
                  placeholder="Weight in kg"
                  className="w-full px-4 py-3 rounded-2xl bg-cream border-2 border-transparent focus:border-olive focus:outline-none text-dark transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-olive mb-1">Activity Level</label>
              <select
                value={form.activity_level}
                onChange={(e) => update('activity_level', e.target.value as ActivityLevel)}
                className="w-full px-4 py-3 rounded-2xl bg-cream border-2 border-transparent focus:border-olive focus:outline-none text-dark transition-all"
              >
                <option value="sedentary">Sedentary</option>
                <option value="light">Light</option>
                <option value="moderate">Moderate</option>
                <option value="active">Active</option>
                <option value="very_active">Very active</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-olive mb-1">Exercise Days / Month</label>
              <input
                type="number"
                min={0}
                max={31}
                value={form.exercise_days_per_month}
                onChange={(e) => update('exercise_days_per_month', e.target.value)}
                placeholder="Times per month"
                className="w-full px-4 py-3 rounded-2xl bg-cream border-2 border-transparent focus:border-olive focus:outline-none text-dark transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-olive mb-2">
                Conditions covered by the ML <span className="text-orange">*</span>
              </label>
              <div className="grid grid-cols-1 gap-2 rounded-2xl bg-cream p-4 border border-transparent">
                {COVERED_CONDITIONS.map((condition) => (
                  <label key={condition.value} className="flex items-center gap-3 text-sm text-dark">
                    <input
                      type="checkbox"
                      checked={form.selectedConditions.includes(condition.value)}
                      onChange={() => toggleCondition(condition.value)}
                    />
                    <span>{condition.label}</span>
                  </label>
                ))}
              </div>
              <p className="text-xs text-olive/70 mt-2">
                Required. Choose at least one condition or add an additional condition below.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-olive mb-1">Other condition</label>
              <input
                type="text"
                value={form.otherCondition}
                onChange={(e) => update('otherCondition', e.target.value)}
                placeholder="Add any additional condition"
                className="w-full px-4 py-3 rounded-2xl bg-cream border-2 border-transparent focus:border-olive focus:outline-none text-dark transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-olive mb-1">Medications (comma-separated)</label>
              <input
                type="text"
                value={form.medications}
                onChange={(e) => update('medications', e.target.value)}
                placeholder="List any medications"
                className="w-full px-4 py-3 rounded-2xl bg-cream border-2 border-transparent focus:border-olive focus:outline-none text-dark transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-olive mb-1">Injuries (comma-separated)</label>
              <input
                type="text"
                value={form.injuries}
                onChange={(e) => update('injuries', e.target.value)}
                placeholder="List any injuries or limitations"
                className="w-full px-4 py-3 rounded-2xl bg-cream border-2 border-transparent focus:border-olive focus:outline-none text-dark transition-all"
              />
            </div>

            <div className="grid grid-cols-3 gap-3 text-sm text-olive">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.goal_lose_weight}
                  onChange={(e) => update('goal_lose_weight', e.target.checked)}
                />
                Lose weight
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.goal_build_muscle}
                  onChange={(e) => update('goal_build_muscle', e.target.checked)}
                />
                Build muscle
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.goal_endurance}
                  onChange={(e) => update('goal_endurance', e.target.checked)}
                />
                Improve endurance
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-olive mb-1">Current Mood (optional)</label>
              <input
                type="text"
                value={form.mood}
                onChange={(e) => update('mood', e.target.value)}
                placeholder="Example: motivated, tired, stressed"
                className="w-full px-4 py-3 rounded-2xl bg-cream border-2 border-transparent focus:border-olive focus:outline-none text-dark transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-olive mb-1">Motivation Notes (optional)</label>
              <textarea
                value={form.motivation_text}
                onChange={(e) => update('motivation_text', e.target.value)}
                rows={3}
                placeholder="Add a short note about your goals or constraints"
                className="w-full px-4 py-3 rounded-2xl bg-cream border-2 border-transparent focus:border-olive focus:outline-none text-dark transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-olive mb-1">Password</label>
              <input
                type="password"
                value={form.password}
                onChange={(e) => update('password', e.target.value)}
                required
                placeholder="Create a password"
                className="w-full px-4 py-3 rounded-2xl bg-cream border-2 border-transparent focus:border-olive focus:outline-none text-dark transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-olive mb-1">Confirm Password</label>
              <input
                type="password"
                value={form.confirmPassword}
                onChange={(e) => update('confirmPassword', e.target.value)}
                required
                placeholder="Confirm your password"
                className="w-full px-4 py-3 rounded-2xl bg-cream border-2 border-transparent focus:border-olive focus:outline-none text-dark transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-4 rounded-full bg-orange text-white font-semibold text-base hover:opacity-90 hover:-translate-y-0.5 transition-all disabled:opacity-60"
            >
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <p className="text-center text-sm text-olive mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-orange hover:opacity-80 font-medium">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
