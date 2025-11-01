import React from 'react';
import { apiClient, Company, CompanyTrendPoint } from '../services/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import SentimentTrends from '../components/dashboard/SentimentTrends';
import AlertsPanel from '../components/alerts/AlertsPanel';

const DashboardPage: React.FC = () => {
  const [isLoading, setIsLoading] = React.useState(true);
  const [companies, setCompanies] = React.useState<Company[]>([]);
  const [selectedCompanyId, setSelectedCompanyId] = React.useState<string | null>(null);
  const [trends, setTrends] = React.useState<CompanyTrendPoint[]>([]);

  const selectedCompany = React.useMemo(
    () => companies.find((c) => c.id === selectedCompanyId) || null,
    [companies, selectedCompanyId]
  );

  React.useEffect(() => {
    let isMounted = true;

    async function loadInitial() {
      try {
        const list = await apiClient.getCompanies();
        if (!isMounted) return;
        setCompanies(list);
        const firstId = list[0]?.id || null;
        setSelectedCompanyId(firstId);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadInitial();
    return () => {
      isMounted = false;
    };
  }, []);

  React.useEffect(() => {
    let isMounted = true;
    async function loadTrends(companyId: string) {
      try {
        const points = await apiClient.getCompanyTrends(companyId);
        if (!isMounted) return;
        setTrends(points);
      } catch (e) {
        // Fallback: keep empty
        if (isMounted) setTrends([]);
      }
    }
    if (selectedCompanyId) {
      loadTrends(selectedCompanyId);
    } else {
      setTrends([]);
    }
    return () => {
      isMounted = false;
    };
  }, [selectedCompanyId]);

  const timelineData = React.useMemo(
    () => (Array.isArray(trends) ? trends : []).map((p) => ({
        dateLabel: p.date_label,
        optimism: p.optimism,
        risk: p.risk,
        uncertainty: p.uncertainty,
      })),
    [trends]
  );

  const handleThresholdsChange = React.useCallback(
    async (t: { sentimentShift: number; riskIncrease: number; themeChange: number }) => {
      if (!selectedCompanyId) return;
      try {
        await Promise.all([
          apiClient.createAlertPreference(selectedCompanyId, 'SENTIMENT_SHIFT', t.sentimentShift),
          apiClient.createAlertPreference(selectedCompanyId, 'RISK_INCREASE', t.riskIncrease),
          apiClient.createAlertPreference(selectedCompanyId, 'THEME_CHANGE', t.themeChange),
        ]);
      } catch (e) {
        // Toasts handled by api client
      }
    },
    [selectedCompanyId]
  );

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">View trends and manage narrative change alerts.</p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-700">Company</label>
          <select
            className="border border-gray-300 rounded px-2 py-1 text-sm"
            value={selectedCompanyId || ''}
            onChange={(e) => setSelectedCompanyId(e.target.value || null)}
          >
            {companies.map((c) => (
              <option key={c.id} value={c.id}>
                {c.company_name} ({c.ticker_symbol})
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <SentimentTrends
            companyName={selectedCompany ? `${selectedCompany.company_name} (${selectedCompany.ticker_symbol})` : '—'}
            data={timelineData}
          />
        </div>
        <div className="lg:col-span-1">
          <AlertsPanel
            sector={selectedCompany?.sector}
            industry={selectedCompany?.industry}
            onChange={handleThresholdsChange}
          />
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
