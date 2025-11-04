import React, { useState } from 'react';
import ReportComparison from '../components/analysis/ReportComparison';
import DeltaVisualization from '../components/analysis/DeltaVisualization';
import apiClient, { ComparisonAnalysis } from '../services/api';

const ComparisonPage: React.FC = () => {
  const [comparison, setComparison] = useState<ComparisonAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCompare = async (baseReportId: string, comparisonReportId: string) => {
    setError(null);
    setComparison(null);
    try {
      const response = await apiClient.client.post<ComparisonAnalysis>('/analysis/compare', {
        base_report_id: baseReportId,
        comparison_report_id: comparisonReportId,
      });
      setComparison(response.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Comparison failed');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Report Comparison</h1>
        <p className="text-gray-600 mt-2">
          Compare narrative sentiment and tone between two financial reports to identify changes over time.
        </p>
      </div>

      <ReportComparison onCompare={handleCompare} />

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

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

