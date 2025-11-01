/**
 * Analysis Page Component
 * 
 * View sentiment analysis results and insights.
 */

import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import AnalysisResults from '../components/analysis/AnalysisResults';
import apiClient, { FinancialReport, NarrativeAnalysis } from '../services/api';

const AnalysisPage: React.FC = () => {
  const [reports, setReports] = useState<FinancialReport[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string>('');
  const [analysis, setAnalysis] = useState<NarrativeAnalysis | null>(null);
  const [loadingReports, setLoadingReports] = useState<boolean>(false);
  const [running, setRunning] = useState<boolean>(false);
  const location = useLocation() as { state?: { reportId?: string } };

  useEffect(() => {
    let ignore = false;
    const load = async () => {
      setLoadingReports(true);
      try {
        const data = await apiClient.getReports();
        if (!ignore) setReports(data);
      } finally {
        setLoadingReports(false);
      }
    };
    load();
    return () => { ignore = true; };
  }, []);

  // Auto-select report if navigated with reportId state
  useEffect(() => {
    const passedReportId = location?.state?.reportId;
    if (passedReportId) {
      setSelectedReportId(passedReportId);
    }
  }, [location]);

  const handleAnalyze = async () => {
    if (!selectedReportId) return;
    setRunning(true);
    try {
      const result = await apiClient.waitForReportAnalysis(selectedReportId, { pollIntervalMs: 3000, timeoutMs: 120000 });
      setAnalysis(result);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div>
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Narrative Analysis</h1>
            <p className="text-gray-600 mt-1">
              View multi-dimensional sentiment analysis results
            </p>
          </div>
          
          <div className="flex gap-2">
            <select
              value={selectedReportId}
              onChange={(e) => setSelectedReportId(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="" disabled>
                {loadingReports ? 'Loading reports…' : 'Select a report'}
              </option>
              {reports.map((r) => {
                const companyLabel = r.company_name || r.ticker_symbol || r.company?.company_name || r.company?.ticker_symbol || r.company_id;
                const period = r.fiscal_period || '';
                const date = r.filing_date || '';
                const status = r.processing_status;
                const idSuffix = r.id ? r.id.slice(0, 8) : '';
                const label = `${companyLabel} • ${r.report_type}${period ? ' • ' + period : ''}${date ? ' • ' + date : ''} • ${status} • ${idSuffix}`;
                return (
                  <option key={r.id} value={r.id}>
                    {label}
                  </option>
                );
              })}
            </select>
            <button
              onClick={handleAnalyze}
              disabled={!selectedReportId || running}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-60"
            >
              {running ? 'Analyzing…' : 'Run Analysis'}
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow px-6 py-6">
        <AnalysisResults analysis={analysis} />
      </div>
    </div>
  );
};

export default AnalysisPage;
