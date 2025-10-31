import React, { useRef, useState } from 'react';
import apiClient, { FinancialReport, UploadReportRequest } from '../../services/api';

interface ReportUploadProps {
  companyId: string;
  onUploaded?: (report: FinancialReport) => void;
}

const ACCEPTED_TYPES = [
  'application/pdf',
  'text/html',
  'text/plain',
  'application/xhtml+xml',
];

const ReportUpload: React.FC<ReportUploadProps> = ({ companyId, onUploaded }) => {
  const [reportType, setReportType] = useState<string>('10-K');
  const [fiscalPeriod, setFiscalPeriod] = useState<string>('');
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] || null;
    if (selected && !ACCEPTED_TYPES.includes(selected.type)) {
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }
    setFile(selected || null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setSubmitting(true);
    try {
      const payload: UploadReportRequest = {
        company_id: companyId,
        report_type: reportType,
        fiscal_period: fiscalPeriod || undefined,
        file,
      };
      const report = await apiClient.uploadReport(payload);
      onUploaded?.(report);
      setFile(null);
      setFiscalPeriod('');
      if (fileInputRef.current) fileInputRef.current.value = '';
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <label className="block text-sm font-medium text-gray-700">Report Type</label>
          <select
            className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
            value={reportType}
            onChange={(e) => setReportType(e.target.value)}
          >
            <option value="10-K">10-K</option>
            <option value="10-Q">10-Q</option>
            <option value="8-K">8-K</option>
            <option value="Annual">Annual</option>
            <option value="Other">Other</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Fiscal Period (optional)</label>
          <input
            type="text"
            value={fiscalPeriod}
            onChange={(e) => setFiscalPeriod(e.target.value)}
            placeholder="e.g., FY2024"
            className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Report File</label>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.html,.htm,.txt"
            onChange={handleFileChange}
            className="mt-1 block w-full"
          />
        </div>
      </div>
      <div>
        <button
          type="submit"
          disabled={!file || submitting}
          className="px-4 py-2 bg-blue-600 text-white rounded-md disabled:opacity-60"
        >
          {submitting ? 'Uploading…' : 'Upload Report'}
        </button>
      </div>
    </form>
  );
};

export default ReportUpload;


