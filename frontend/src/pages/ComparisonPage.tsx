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
