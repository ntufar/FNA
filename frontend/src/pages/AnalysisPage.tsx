/**
 * Analysis Page Component
 * 
 * View sentiment analysis results and insights.
 */

import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import AnalysisResults from '../components/analysis/AnalysisResults';
import apiClient, { NarrativeAnalysis } from '../services/api';

const AnalysisPage: React.FC = () => {
	const [analyses, setAnalyses] = useState<NarrativeAnalysis[]>([]);
	const [selectedAnalysisId, setSelectedAnalysisId] = useState<string>('');
	const [analysis, setAnalysis] = useState<NarrativeAnalysis | null>(null);
	const [loadingAnalyses, setLoadingAnalyses] = useState<boolean>(false);
	const location = useLocation() as { state?: { analysisId?: string } };

	useEffect(() => {
		let ignore = false;
		const load = async () => {
			setLoadingAnalyses(true);
			try {
				const data = await apiClient.getAnalyses({ limit: 100 });
				if (!ignore) setAnalyses(Array.isArray(data) ? data : []);
			} finally {
				setLoadingAnalyses(false);
			}
		};
		load();
		return () => { ignore = true; };
	}, []);

	// Auto-select analysis if navigated with analysisId state
	useEffect(() => {
		const passedAnalysisId = location?.state?.analysisId;
		if (passedAnalysisId) {
			setSelectedAnalysisId(passedAnalysisId);
		}
	}, [location]);

	// Load analysis details when selection changes
	useEffect(() => {
		let cancelled = false;
		const loadAnalysis = async () => {
			if (!selectedAnalysisId) {
				setAnalysis(null);
				return;
			}
			try {
				const result = await apiClient.getAnalysis(selectedAnalysisId);
				if (!cancelled) setAnalysis(result);
			} catch (_err) {
				if (!cancelled) setAnalysis(null);
			}
		};
		loadAnalysis();
		return () => { cancelled = true; };
	}, [selectedAnalysisId]);

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
							value={selectedAnalysisId}
							onChange={(e) => setSelectedAnalysisId(e.target.value)}
							className="border border-gray-300 rounded-md px-3 py-2 text-sm"
						>
							<option value="" disabled>
								{loadingAnalyses ? 'Loading analyses…' : 'Select an analysis'}
							</option>
							{analyses.map((a) => {
								const companyLabel = a.report?.company_name || a.report?.ticker_symbol || '';
								const reportType = a.report?.report_type || '';
								const period = a.report?.fiscal_period || '';
								const date = a.report?.filing_date || '';
								const idSuffix = a.id ? a.id.slice(0, 8) : '';
								const labelParts = [companyLabel, reportType, period, date].filter(Boolean);
								const label = `${labelParts.join(' • ')}${labelParts.length ? ' • ' : ''}${idSuffix}` || idSuffix;
								return (
									<option key={a.id} value={a.id}>
										{label}
									</option>
								);
							})}
						</select>
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
