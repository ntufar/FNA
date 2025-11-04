import React, { useState, useEffect } from 'react';
import apiClient, { ComparisonAnalysis, FinancialReport } from '../../services/api';
import LoadingSpinner from '../common/LoadingSpinner';

interface ReportComparisonProps {
  defaultBaseReportId?: string;
  defaultComparisonReportId?: string;
  onCompare?: (baseReportId: string, comparisonReportId: string) => void;
}

const ReportComparison: React.FC<ReportComparisonProps> = ({
  defaultBaseReportId,
  defaultComparisonReportId,
  onCompare,
}) => {
  const [baseReportId, setBaseReportId] = useState<string>(defaultBaseReportId || '');
  const [comparisonReportId, setComparisonReportId] = useState<string>(defaultComparisonReportId || '');
  const [reports, setReports] = useState<FinancialReport[]>([]);
  const [loadingReports, setLoadingReports] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ComparisonAnalysis | null>(null);

  // Fetch available reports on mount
  useEffect(() => {
    let mounted = true;
    async function loadReports() {
      try {
        setLoadingReports(true);
        const allReports = await apiClient.getReports();
        // Filter to only show COMPLETED reports (ready for comparison)
        const completedReports = allReports.filter(
          (r) => r.processing_status === 'COMPLETED'
        );
        // Sort by filing date (most recent first)
        completedReports.sort((a, b) => {
          const dateA = new Date(a.filing_date || a.created_at).getTime();
          const dateB = new Date(b.filing_date || b.created_at).getTime();
          return dateB - dateA;
        });
        if (mounted) {
          setReports(completedReports);
        }
      } catch (err: any) {
        console.error('Failed to load reports:', err);
        if (mounted) {
          setError(err?.response?.data?.detail || err?.message || 'Failed to load reports');
        }
      } finally {
        if (mounted) {
          setLoadingReports(false);
        }
      }
    }
    loadReports();
    return () => {
      mounted = false;
    };
  }, []);

  // Format report label for dropdown
  const formatReportLabel = (report: FinancialReport): string => {
    const company = report.company_name || report.ticker_symbol || 'Unknown Company';
    const type = report.report_type || 'Unknown Type';
    const period = report.fiscal_period || '';
    const filingDate = report.filing_date 
      ? new Date(report.filing_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
      : '';
    
    const parts = [company, type];
    if (period) parts.push(period);
    if (filingDate) parts.push(`(${filingDate})`);
    
    return parts.join(' - ');
  };

  const handleCompare = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!baseReportId || !comparisonReportId) {
      setError('Please select both reports to compare');
      return;
    }

    if (baseReportId === comparisonReportId) {
      setError('Please select two different reports');
      return;
    }

    setError(null);
    setResult(null);
    setLoading(true);
    
    try {
      // The backend expects report IDs; it derives analyses internally
      const response = await apiClient.client.post<ComparisonAnalysis>('/analysis/compare', {
        base_report_id: baseReportId,
        comparison_report_id: comparisonReportId,
      });
      setResult(response.data);
      
      // Call optional callback if provided
      if (onCompare) {
        onCompare(baseReportId, comparisonReportId);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Comparison failed');
    } finally {
      setLoading(false);
    }
  };

  if (loadingReports) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-2">Compare Reports</h2>
      <p className="text-sm text-gray-600 mb-6">
        Select two reports to compare their narrative sentiment and tone.
      </p>

      <form onSubmit={handleCompare} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Base Report (Earlier)
          </label>
          <select
            value={baseReportId}
            onChange={(e) => setBaseReportId(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            required
          >
            <option value="">-- Select a base report --</option>
            {reports.map((report) => (
              <option key={report.id} value={report.id}>
                {formatReportLabel(report)}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Comparison Report (Later)
          </label>
          <select
            value={comparisonReportId}
            onChange={(e) => setComparisonReportId(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            required
          >
            <option value="">-- Select a comparison report --</option>
            {reports.map((report) => (
              <option key={report.id} value={report.id}>
                {formatReportLabel(report)}
              </option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          disabled={loading || !baseReportId || !comparisonReportId || baseReportId === comparisonReportId}
          className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm hover:shadow-md"
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Comparing...
            </span>
          ) : (
            'Compare Reports'
          )}
        </button>
      </form>

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm" role="alert">
          <div className="flex items-start">
            <svg className="w-5 h-5 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span>{error}</span>
          </div>
        </div>
      )}

      {reports.length === 0 && !loadingReports && (
        <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800 text-sm">
          <p>No completed reports available for comparison. Please ensure reports are processed first.</p>
        </div>
      )}

      {result && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Comparison Results</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
              <div className="text-sm text-gray-600 mb-1">Optimism Δ</div>
              <div className="text-2xl font-bold text-gray-900">
                {result.optimism_delta >= 0 ? '+' : ''}{result.optimism_delta.toFixed(3)}
              </div>
            </div>
            <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
              <div className="text-sm text-gray-600 mb-1">Risk Δ</div>
              <div className="text-2xl font-bold text-gray-900">
                {result.risk_delta >= 0 ? '+' : ''}{result.risk_delta.toFixed(3)}
              </div>
            </div>
            <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
              <div className="text-sm text-gray-600 mb-1">Uncertainty Δ</div>
              <div className="text-2xl font-bold text-gray-900">
                {result.uncertainty_delta >= 0 ? '+' : ''}{result.uncertainty_delta.toFixed(3)}
              </div>
            </div>
            <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
              <div className="text-sm text-gray-600 mb-1">Overall Sentiment Δ</div>
              <div className="text-2xl font-bold text-gray-900">
                {result.overall_sentiment_delta >= 0 ? '+' : ''}{result.overall_sentiment_delta.toFixed(3)}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportComparison;


