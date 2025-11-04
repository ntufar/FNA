import React, { useState, useEffect } from 'react';
import apiClient, { Company, AvailableFiling, DownloadReportRequest } from '../../services/api';

interface AdvancedDownloadModalProps {
  isOpen: boolean;
  onClose: () => void;
  companies: Company[];
  onDownloadComplete?: () => void;
}

type Step = 'company' | 'filings' | 'confirm';

const AdvancedDownloadModal: React.FC<AdvancedDownloadModalProps> = ({
  isOpen,
  onClose,
  companies,
  onDownloadComplete,
}) => {
  const [step, setStep] = useState<Step>('company');
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>('');
  const [selectedTicker, setSelectedTicker] = useState<string>('');
  const [reportType, setReportType] = useState<'10-K' | '10-Q' | '8-K'>('10-K');
  const [fiscalYear, setFiscalYear] = useState<number | ''>('');
  const [availableFilings, setAvailableFilings] = useState<AvailableFiling[]>([]);
  const [selectedFiling, setSelectedFiling] = useState<AvailableFiling | null>(null);
  const [loadingFilings, setLoadingFilings] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string>('');

  // Reset state when modal opens/closes
  useEffect(() => {
    if (!isOpen) {
      setStep('company');
      setSelectedCompanyId('');
      setSelectedTicker('');
      setReportType('10-K');
      setFiscalYear('');
      setAvailableFilings([]);
      setSelectedFiling(null);
      setError('');
    }
  }, [isOpen]);

  // Get company ticker from selected company
  const getTicker = (): string => {
    if (selectedTicker) return selectedTicker;
    if (selectedCompanyId) {
      const company = companies.find(c => c.id === selectedCompanyId);
      return company?.ticker_symbol || '';
    }
    return '';
  };

  const handleSearchFilings = async () => {
    const ticker = getTicker();
    if (!ticker) {
      setError('Please select a company or enter a ticker symbol');
      return;
    }

    setLoadingFilings(true);
    setError('');
    try {
      const filings = await apiClient.getAvailableFilings(
        ticker,
        reportType,
        fiscalYear ? Number(fiscalYear) : undefined
      );
      setAvailableFilings(filings);
      setStep('filings');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch available filings');
    } finally {
      setLoadingFilings(false);
    }
  };

  const handleSelectFiling = (filing: AvailableFiling) => {
    setSelectedFiling(filing);
    setStep('confirm');
  };

  const handleConfirmDownload = async () => {
    if (!selectedFiling) return;

    const ticker = getTicker();
    setDownloading(true);
    setError('');
    
    try {
      const downloadRequest: DownloadReportRequest = {
        ticker_symbol: ticker,
        report_type: reportType,
        filing_date: selectedFiling.filing_date,
      };
      
      await apiClient.downloadReport(downloadRequest);
      onDownloadComplete?.();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to download report');
    } finally {
      setDownloading(false);
    }
  };

  const handleExistingReportClick = () => {
    if (selectedFiling?.existing_report_id) {
      window.open(`/reports/${selectedFiling.existing_report_id}`, '_blank');
    }
  };

  if (!isOpen) return null;

  // Generate fiscal year options (last 5 years)
  const currentYear = new Date().getFullYear();
  const yearOptions = Array.from({ length: 5 }, (_, i) => currentYear - i);

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" onClick={onClose}>
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold text-gray-900">Advanced Download</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500 focus:outline-none"
          >
            <span className="sr-only">Close</span>
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {/* Step 1: Company & Report Type Selection */}
        {step === 'company' && (
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-medium text-gray-800 mb-4">Step 1: Select Company and Report Type</h4>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Company
                  </label>
                  <select
                    value={selectedCompanyId}
                    onChange={(e) => setSelectedCompanyId(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Choose a company...</option>
                    {companies.map((company) => (
                      <option key={company.id} value={company.id}>
                        {company.company_name} ({company.ticker_symbol})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="text-center text-gray-500">OR</div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Enter Ticker Symbol
                  </label>
                  <input
                    type="text"
                    value={selectedTicker}
                    onChange={(e) => setSelectedTicker(e.target.value.toUpperCase())}
                    placeholder="e.g., AAPL"
                    maxLength={5}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Report Type
                    </label>
                    <select
                      value={reportType}
                      onChange={(e) => setReportType(e.target.value as '10-K' | '10-Q' | '8-K')}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="10-K">10-K</option>
                      <option value="10-Q">10-Q</option>
                      <option value="8-K">8-K</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Fiscal Year (Optional)
                    </label>
                    <select
                      value={fiscalYear}
                      onChange={(e) => setFiscalYear(e.target.value ? Number(e.target.value) : '')}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">All Years</option>
                      {yearOptions.map((year) => (
                        <option key={year} value={year}>
                          {year}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <button
                  onClick={handleSearchFilings}
                  disabled={loadingFilings}
                  className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loadingFilings ? 'Searching...' : 'Search Available Filings'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Available Filings List */}
        {step === 'filings' && (
          <div className="space-y-6">
            <div>
              <button
                onClick={() => setStep('company')}
                className="text-blue-600 hover:text-blue-800 mb-4 flex items-center"
              >
                <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Company Selection
              </button>
              <h4 className="text-lg font-medium text-gray-800 mb-4">
                Step 2: Select Filing to Download
              </h4>
            </div>

            {availableFilings.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No filings found for {getTicker()} ({reportType})
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Filing Date
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Fiscal Period
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Action
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {availableFilings.map((filing, idx) => (
                      <tr key={idx} className={filing.is_downloaded ? 'bg-gray-50' : 'hover:bg-gray-50'}>
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(filing.filing_date).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                          {filing.fiscal_period || '-'}
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap text-sm">
                          {filing.is_downloaded ? (
                            <button
                              onClick={handleExistingReportClick}
                              className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800 hover:bg-green-200"
                            >
                              Already Downloaded
                            </button>
                          ) : (
                            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                              Available
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap text-sm">
                          {filing.is_downloaded ? (
                            <button
                              onClick={handleExistingReportClick}
                              className="text-blue-600 hover:text-blue-800 font-medium"
                            >
                              View Report
                            </button>
                          ) : (
                            <button
                              onClick={() => handleSelectFiling(filing)}
                              className="text-blue-600 hover:text-blue-800 font-medium"
                            >
                              Select
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Step 3: Confirmation */}
        {step === 'confirm' && selectedFiling && (
          <div className="space-y-6">
            <div>
              <button
                onClick={() => setStep('filings')}
                className="text-blue-600 hover:text-blue-800 mb-4 flex items-center"
              >
                <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Filings List
              </button>
              <h4 className="text-lg font-medium text-gray-800 mb-4">Step 3: Confirm Download</h4>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 space-y-3">
              <div className="flex justify-between">
                <span className="font-medium text-gray-700">Company:</span>
                <span className="text-gray-900">{getTicker()}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium text-gray-700">Report Type:</span>
                <span className="text-gray-900">{selectedFiling.report_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium text-gray-700">Filing Date:</span>
                <span className="text-gray-900">{new Date(selectedFiling.filing_date).toLocaleDateString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium text-gray-700">Fiscal Period:</span>
                <span className="text-gray-900">{selectedFiling.fiscal_period || '-'}</span>
              </div>
            </div>

            {selectedFiling.is_downloaded && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <p className="text-yellow-800 text-sm">
                  ⚠️ This report has already been downloaded. You can view it or download it again.
                </p>
              </div>
            )}

            <div className="flex justify-end space-x-3">
              <button
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDownload}
                disabled={downloading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {downloading ? 'Downloading...' : 'Download Report'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdvancedDownloadModal;

