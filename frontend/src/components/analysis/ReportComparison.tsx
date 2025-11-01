import React, { useState } from 'react';
import apiClient, { ComparisonAnalysis } from '../../services/api';

interface ReportComparisonProps {
  defaultBaseReportId?: string;
  defaultComparisonReportId?: string;
}

const ReportComparison: React.FC<ReportComparisonProps> = ({
  defaultBaseReportId,
  defaultComparisonReportId,
}) => {
  const [baseReportId, setBaseReportId] = useState<string>(defaultBaseReportId || '');
  const [comparisonReportId, setComparisonReportId] = useState<string>(defaultComparisonReportId || '');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ComparisonAnalysis | null>(null);

  const handleCompare = async (e: React.FormEvent) => {
    e.preventDefault();
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
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Comparison failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Compare Reports</h2>

      <form onSubmit={handleCompare} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Base Report ID</label>
          <input
            type="text"
            value={baseReportId}
            onChange={(e) => setBaseReportId(e.target.value)}
            className="w-full border rounded px-3 py-2"
            placeholder="UUID of earlier report"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Comparison Report ID</label>
          <input
            type="text"
            value={comparisonReportId}
            onChange={(e) => setComparisonReportId(e.target.value)}
            className="w-full border rounded px-3 py-2"
            placeholder="UUID of later report"
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Comparing…' : 'Compare'}
        </button>
      </form>

      {error && (
        <div className="mt-4 text-red-600 text-sm" role="alert">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold mb-2">Results</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 border rounded">
              <div className="text-sm text-gray-600">Optimism Δ</div>
              <div className="text-2xl font-bold">{result.optimism_delta.toFixed(3)}</div>
            </div>
            <div className="p-4 border rounded">
              <div className="text-sm text-gray-600">Risk Δ</div>
              <div className="text-2xl font-bold">{result.risk_delta.toFixed(3)}</div>
            </div>
            <div className="p-4 border rounded">
              <div className="text-sm text-gray-600">Uncertainty Δ</div>
              <div className="text-2xl font-bold">{result.uncertainty_delta.toFixed(3)}</div>
            </div>
            <div className="p-4 border rounded">
              <div className="text-sm text-gray-600">Overall Sentiment Δ</div>
              <div className="text-2xl font-bold">{result.overall_sentiment_delta.toFixed(3)}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportComparison;


