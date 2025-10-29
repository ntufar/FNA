/**
 * Alerts Page Component
 * 
 * Manage alerts and notifications for significant changes.
 */

import React from 'react';

const AlertsPage: React.FC = () => {
  return (
    <div>
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Alerts & Notifications</h1>
            <p className="text-gray-600 mt-1">
              Manage alerts for significant narrative changes and threshold settings
            </p>
          </div>
          
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
            + Configure Alert
          </button>
        </div>
      </div>

      {/* Placeholder Content */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-8 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-3.5-3.5c-.3-.3-.5-.8-.5-1.3V9c0-2.2-1.8-4-4-4s-4 1.8-4 4v3.2c0 .5-.2 1-.5 1.3L4 17h5m6 0a3 3 0 01-6 0m6 0H9" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Alert Management</h3>
          <p className="text-gray-600 mb-4">
            This page will display active alerts and allow you to configure thresholds for notifications.
          </p>
          <p className="text-sm text-blue-600">
            Feature coming soon in User Story 3 implementation
          </p>
        </div>
      </div>
    </div>
  );
};

export default AlertsPage;
