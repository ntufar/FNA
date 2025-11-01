import React, { useState } from 'react';
import ReportComparison from '../components/analysis/ReportComparison';
import DeltaVisualization from '../components/analysis/DeltaVisualization';
import apiClient, { ComparisonAnalysis } from '../services/api';

const ComparisonPage: React.FC = () => {
  const [comparison, setComparison] = useState<ComparisonAnalysis | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleCompare = async (baseReportId: string, comparisonReportId: string) => {
    setError(null);
    setComparison(null);
    setLoading(true);
    try {
      const response = await apiClient.client.post<ComparisonAnalysis>('/analysis/compare', {
        base_report_id: baseReportId,
        comparison_report_id: comparisonReportId,
      });
      setComparison(response.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Comparison failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Report Comparison</h1>

      {/* Simple inline form using ReportComparison input UI but with handler override */}
      <div className="bg-white shadow rounded-lg p-6">
        <ReportComparison />
      </div>

      {loading && <div>Comparing…</div>}
      {error && <div className="text-red-600">{error}</div>}

      {comparison && (
        <DeltaVisualization
          optimismDelta={comparison.optimism_delta}
          riskDelta={comparison.risk_delta}
          uncertaintyDelta={comparison.uncertainty_delta}
          overallDelta={comparison.overall_sentiment_delta}
        />
      )}
    </div>
  );
};

export default ComparisonPage;

