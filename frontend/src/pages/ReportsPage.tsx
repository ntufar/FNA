/**
 * Reports Page Component
 * 
 * View and manage financial reports.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient, Company, FinancialReport } from '../services/api';
import LoadingSpinner from '../components/common/LoadingSpinner';

const ReportsPage: React.FC = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = React.useState(true);
  const [companies, setCompanies] = React.useState<Company[]>([]);
  const [selectedCompanyId, setSelectedCompanyId] = React.useState<string | ''>('');
  const [reports, setReports] = React.useState<FinancialReport[]>([]);
  const [isDownloading, setIsDownloading] = React.useState(false);
  const [downloadTicker, setDownloadTicker] = React.useState('');
  const [downloadType, setDownloadType] = React.useState<'10-K' | '10-Q' | '8-K' | 'Annual' | 'Other'>('10-K');

  const companyById = React.useMemo(() => {
    const map: Record<string, Company> = {};
    for (const c of companies) map[c.id] = c;
    return map;
  }, [companies]);

  React.useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const [companyList, reportList] = await Promise.all([
          apiClient.getCompanies(),
          apiClient.getReports(),
        ]);
        if (!mounted) return;
        setCompanies(companyList);
        setReports(Array.isArray(reportList) ? reportList : []);
        if (companyList[0]) setSelectedCompanyId(companyList[0].id);
      } finally {
        if (mounted) setIsLoading(false);
      }
    }
    load();
    return () => { mounted = false; };
  }, []);

  async function handleDownloadFromSEC() {
    if (!downloadTicker) return;
    setIsDownloading(true);
    try {
      const fr = await apiClient.downloadReport({ ticker_symbol: downloadTicker.toUpperCase(), report_type: downloadType });
      // Prepend new report if returned
      if (fr) setReports((prev) => [fr, ...prev]);
      setDownloadTicker('');
    } finally {
      setIsDownloading(false);
    }
  }

  async function handleReanalyze(reportId: string) {
    // Optimistically set status to PENDING
    setReports((prev) => prev.map((r) => (r.id === reportId ? { ...r, processing_status: 'PENDING' } : r)));
    try {
      await apiClient.triggerAnalysis(reportId);
      // Optionally reflect immediate PENDING state; background task will update to COMPLETED/FAILED later
    } catch (e) {
      // On error, revert status
      setReports((prev) => prev.map((r) => (r.id === reportId ? { ...r, processing_status: 'FAILED' } : r)));
    }
  }

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div>
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Financial Reports</h1>
            <p className="text-gray-600 mt-1">
              Upload, download, and manage financial reports for analysis
            </p>
          </div>
          
          <div className="flex flex-wrap gap-3 items-center">
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Ticker (e.g., AAPL)"
                value={downloadTicker}
                onChange={(e) => setDownloadTicker(e.target.value)}
                className="border border-gray-300 rounded px-2 py-1 text-sm w-32"
              />
              <select
                className="border border-gray-300 rounded px-2 py-1 text-sm"
                value={downloadType}
                onChange={(e) => setDownloadType(e.target.value as any)}
              >
                <option value="10-K">10-K</option>
                <option value="10-Q">10-Q</option>
                <option value="8-K">8-K</option>
                <option value="Annual">Annual</option>
                <option value="Other">Other</option>
              </select>
              <button
                onClick={handleDownloadFromSEC}
                disabled={!downloadTicker || isDownloading}
                className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors disabled:opacity-50"
              >
                {isDownloading ? 'Downloading…' : 'Download from SEC.gov'}
              </button>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-700">Company</label>
              <select
                className="border border-gray-300 rounded px-2 py-1 text-sm"
                value={selectedCompanyId}
                onChange={(e) => setSelectedCompanyId(e.target.value)}
              >
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>{c.company_name} ({c.ticker_symbol})</option>
                ))}
              </select>
            </div>

            <button className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
              + Upload Report
            </button>
          </div>
        </div>
      </div>

      {/* Reports Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Reports</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Company</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Filing Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {reports.map((r) => (
                <tr key={r.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {r.company_name || r.ticker_symbol || r.company?.company_name || companyById[r.company_id]?.company_name || r.company_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{r.report_type}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{r.filing_date || '—'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                      {r.processing_status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                    <div className="flex gap-3 justify-end">
                      <button
                        onClick={() => navigate('/analysis', { state: { reportId: r.id } })}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        Analyze
                      </button>
                      {r.processing_status === 'FAILED' && (
                        <button
                          onClick={() => handleReanalyze(r.id)}
                          className="text-red-600 hover:text-red-800"
                          title="Re-run analysis"
                        >
                          Re-run Analysis
                        </button>
                      )}
                      {r.processing_status === 'PENDING' && (
                        <button
                          onClick={() => handleReanalyze(r.id)}
                          className="text-amber-600 hover:text-amber-800"
                          title="Re-process (restart analysis)"
                        >
                          Re-process
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {reports.length === 0 && (
                <tr>
                  <td className="px-6 py-8 text-center text-sm text-gray-500" colSpan={5}>
                    No reports yet. Try downloading a report from SEC.gov above.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
