import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword]     = useState('');
  const [showPass, setShowPass]     = useState(false);
  const [error, setError]           = useState('');
  const [loading, setLoading]       = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(identifier, password);
      const savedRole = localStorage.getItem('role');
      navigate(savedRole === 'admin' ? '/admin' : '/dashboard');
    } catch {
      setError('Incorrect email or password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left hero panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-olive via-olive/90 to-dark flex-col justify-between p-12 relative overflow-hidden">
        {/* Background circles */}
        <div className="absolute top-[-80px] right-[-80px] w-72 h-72 bg-gold/20 rounded-full blur-3xl" />
        <div className="absolute bottom-[-60px] left-[-60px] w-64 h-64 bg-orange/20 rounded-full blur-3xl" />

        {/* Logo */}
        <div className="relative z-10">
          <span className="text-4xl">🌿</span>
          <h1 className="font-heading text-3xl font-bold text-white mt-2">
            SportRX <span className="text-gold">AI</span>
          </h1>
          <p className="text-white/60 text-sm mt-1">Medical Fitness Coach</p>
        </div>

        {/* Center quote */}
        <div className="relative z-10 space-y-6 animate-fade-in">
          <blockquote className="text-white/90 text-2xl font-heading leading-relaxed">
            "Your personalized exercise prescription, <span className="text-gold">powered by AI</span> and grounded in medical science."
          </blockquote>

          {/* Feature pills */}
          <div className="flex flex-wrap gap-2">
            {['ML Risk Analysis', 'RAG Medical Guidelines', 'LLM Plan Generation', 'Bi-weekly Adaptation'].map((feat) => (
              <span key={feat} className="px-3 py-1.5 bg-white/10 rounded-full text-xs text-white/80 border border-white/20">
                {feat}
              </span>
            ))}
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 pt-4 border-t border-white/20">
            {[
              { label: 'Response time', value: '~5s' },
              { label: 'Medical sources', value: 'ADA·ESC·WHO' },
              { label: 'AI model', value: 'Llama 3.3' },
            ].map((s) => (
              <div key={s.label}>
                <p className="text-white font-bold text-lg">{s.value}</p>
                <p className="text-white/50 text-xs">{s.label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom */}
        <p className="relative z-10 text-white/40 text-xs">
          ENSA · AI4SDG Challenge · 2026
        </p>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex items-center justify-center px-6 py-12 bg-cream">
        <div className="w-full max-w-sm animate-slide-up">
          {/* Mobile logo */}
          <div className="text-center mb-8 lg:hidden">
            <span className="text-4xl">🌿</span>
            <h1 className="font-heading text-3xl font-bold text-olive mt-1">
              SportRX <span className="text-orange">AI</span>
            </h1>
          </div>

          <div className="bg-white rounded-3xl shadow-xl p-8 border border-olive/10">
            <div className="mb-8">
              <h2 className="font-heading text-2xl font-bold text-dark">Welcome back</h2>
              <p className="text-dark/50 text-sm mt-1">Sign in to your account</p>
            </div>

            {error && (
              <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-600 rounded-xl px-4 py-3 mb-5 text-sm animate-scale-in">
                <span>⚠</span> {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-olive/80 uppercase tracking-wider mb-1.5">
                  Email or admin alias
                </label>
                <input
                  type="text"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  required
                  placeholder="name@example.com"
                  className="input-field"
                  autoComplete="email"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-olive/80 uppercase tracking-wider mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <input
                    type={showPass ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    placeholder="••••••••"
                    className="input-field pr-12"
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPass(!showPass)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-dark/40 hover:text-olive transition-colors"
                    tabIndex={-1}
                  >
                    {showPass ? '🙈' : '👁'}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full py-4 text-base mt-2"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                    </svg>
                    Signing in...
                  </span>
                ) : 'Continue →'}
              </button>
            </form>

            <p className="text-center text-sm text-dark/50 mt-6">
              New to SportRX?{' '}
              <Link to="/register" className="text-orange hover:text-orange/80 font-semibold transition-colors">
                Create account
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
