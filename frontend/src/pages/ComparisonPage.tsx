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

/**
 * Comparison Page Component
 * 
 * Compare narrative changes between reports.
 */

import React from 'react';

const ComparisonPage: React.FC = () => {
  return (
    <div>
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Report Comparisons</h1>
            <p className="text-gray-600 mt-1">
              Compare narrative changes and sentiment shifts over time
            </p>
          </div>
          
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
            + New Comparison
          </button>
        </div>
      </div>

      {/* Placeholder Content */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-8 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Narrative Delta Analysis</h3>
          <p className="text-gray-600 mb-4">
            This page will show theme evolution and sentiment changes between reporting periods.
          </p>
          <p className="text-sm text-blue-600">
            Feature coming soon in User Story 2 implementation
          </p>
        </div>
      </div>
    </div>
  );
};

export default ComparisonPage;
