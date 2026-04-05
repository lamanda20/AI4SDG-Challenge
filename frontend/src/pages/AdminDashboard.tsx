import { useEffect, useMemo, useState } from 'react';
import {
  getAdminDiseaseActivity,
  getAdminDiseaseRegion,
  getAdminDiseaseRisk,
  getAdminOverview,
  type AdminOverviewResponse,
  type DiseaseMatrixPoint,
} from '../services/backendApi';

function metricBarWidth(count: number, maxCount: number) {
  if (maxCount <= 0) return '0%';
  return `${Math.max(8, Math.round((count / maxCount) * 100))}%`;
}

export default function AdminDashboard() {
  const [overview, setOverview] = useState<AdminOverviewResponse | null>(null);
  const [riskData, setRiskData] = useState<DiseaseMatrixPoint[]>([]);
  const [activityData, setActivityData] = useState<DiseaseMatrixPoint[]>([]);
  const [regionData, setRegionData] = useState<DiseaseMatrixPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const [overviewResponse, riskResponse, activityResponse, regionResponse] = await Promise.all([
          getAdminOverview(),
          getAdminDiseaseRisk(),
          getAdminDiseaseActivity(),
          getAdminDiseaseRegion(),
        ]);

        setOverview(overviewResponse);
        setRiskData(riskResponse);
        setActivityData(activityResponse);
        setRegionData(regionResponse);
      } catch {
        setError('Unable to load admin analytics.');
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const riskMax = useMemo(() => Math.max(0, ...riskData.map((item) => item.count)), [riskData]);
  const activityMax = useMemo(() => Math.max(0, ...activityData.map((item) => item.count)), [activityData]);
  const regionMax = useMemo(() => Math.max(0, ...regionData.map((item) => item.count)), [regionData]);

  if (loading) {
    return <p className="text-olive opacity-60 text-center mt-20">Loading admin analytics...</p>;
  }

  if (error) {
    return <p className="text-red-600 text-center mt-20">{error}</p>;
  }

  if (!overview) {
    return <p className="text-olive opacity-60 text-center mt-20">No analytics available.</p>;
  }

  return (
    <div className="space-y-6">
      <div className="rounded-3xl bg-white p-8 shadow-md border border-olive/10">
        <h1 className="font-heading text-3xl font-bold text-olive">Admin Analytics</h1>
        <p className="mt-3 text-dark/70">Global view of clients, plans, check-ins, and health distribution.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[
          { label: 'Users', value: overview.total_users, color: 'bg-olive' },
          { label: 'Clients', value: overview.total_clients, color: 'bg-orange' },
          { label: 'Admins', value: overview.total_admins, color: 'bg-apricot' },
          { label: 'Plans', value: overview.total_plans, color: 'bg-gold' },
          { label: 'Check-ins', value: overview.total_checkins, color: 'bg-slate-700' },
        ].map((metric) => (
          <div key={metric.label} className={`${metric.color} text-white rounded-2xl p-5 shadow-md`}>
            <p className="text-sm opacity-80">{metric.label}</p>
            <p className="text-3xl font-bold mt-1">{metric.value}</p>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl p-6 shadow-md border border-olive/10">
          <h2 className="font-heading text-xl font-semibold text-olive mb-4">Risk Distribution</h2>
          <div className="space-y-3">
            {overview.risk_levels.map((item) => (
              <div key={item.label}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="capitalize text-dark">{item.label}</span>
                  <span className="font-semibold">{item.count}</span>
                </div>
                <div className="h-3 rounded-full bg-cream overflow-hidden">
                  <div className="h-full rounded-full bg-olive" style={{ width: metricBarWidth(item.count, Math.max(...overview.risk_levels.map((r) => r.count), 1)) }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-md border border-olive/10">
          <h2 className="font-heading text-xl font-semibold text-olive mb-4">Activity Distribution</h2>
          <div className="space-y-3">
            {overview.activity_levels.map((item) => (
              <div key={item.label}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="capitalize text-dark">{item.label}</span>
                  <span className="font-semibold">{item.count}</span>
                </div>
                <div className="h-3 rounded-full bg-cream overflow-hidden">
                  <div className="h-full rounded-full bg-orange" style={{ width: metricBarWidth(item.count, Math.max(...overview.activity_levels.map((a) => a.count), 1)) }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {[
          { title: 'Disease x Risk', data: riskData, accent: 'bg-olive' },
          { title: 'Disease x Activity', data: activityData, accent: 'bg-orange' },
          { title: 'Disease x Region', data: regionData, accent: 'bg-apricot' },
        ].map((panel) => (
          <div key={panel.title} className="bg-white rounded-2xl p-6 shadow-md border border-olive/10">
            <h2 className="font-heading text-xl font-semibold text-olive mb-4">{panel.title}</h2>
            <div className="space-y-3 max-h-[420px] overflow-auto pr-1">
              {panel.data.map((item) => (
                <div key={`${item.disease}-${item.segment}`} className="rounded-xl bg-cream p-3">
                  <div className="flex items-center justify-between text-sm mb-1 gap-3">
                    <span className="font-semibold text-dark capitalize">{item.disease}</span>
                    <span className="text-dark/70 capitalize">{item.segment}</span>
                  </div>
                  <div className="h-2 rounded-full bg-white overflow-hidden">
                    <div className={`h-full rounded-full ${panel.accent}`} style={{ width: metricBarWidth(item.count, Math.max(panel.title === 'Disease x Risk' ? riskMax : panel.title === 'Disease x Activity' ? activityMax : regionMax, 1)) }} />
                  </div>
                  <div className="text-right text-xs text-dark/70 mt-1">{item.count}</div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
