import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: '', email: '', password: '', confirmPassword: '',
  });
  const [error, setError]     = useState('');
  const [loading, setLoading] = useState(false);

  const update = (field: string, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setLoading(true);
    try {
      await api.post('/users/client', {
        name: form.name,
        email: form.email,
        password: form.password,
        role: 'client',
        age: 30,
        chronic_condition: 'Unknown',
        biometrics: { mood_score: 5, recent_feedback: 'New user' },
      });
      navigate('/login');
    } catch {
      setError('This email is already registered or an error occurred.');
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
            {[
              { label: 'Full Name', field: 'name', type: 'text', placeholder: 'Karim Benali' },
              { label: 'Email', field: 'email', type: 'email', placeholder: 'you@example.com' },
              { label: 'Password', field: 'password', type: 'password', placeholder: '••••••••' },
              { label: 'Confirm Password', field: 'confirmPassword', type: 'password', placeholder: '••••••••' },
            ].map(({ label, field, type, placeholder }) => (
              <div key={field}>
                <label className="block text-sm font-medium text-olive mb-1">{label}</label>
                <input
                  type={type}
                  value={form[field as keyof typeof form]}
                  onChange={(e) => update(field, e.target.value)}
                  required
                  placeholder={placeholder}
                  className="w-full px-4 py-3 rounded-2xl bg-cream border-2 border-transparent focus:border-olive focus:outline-none text-dark transition-all"
                />
              </div>
            ))}

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
