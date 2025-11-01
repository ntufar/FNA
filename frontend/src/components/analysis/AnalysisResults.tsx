import React from 'react';
import { NarrativeAnalysis } from '../../services/api';

interface AnalysisResultsProps {
  analysis: NarrativeAnalysis | null;
}

const pct = (v: number | undefined) =>
  typeof v === 'number' && isFinite(v) ? `${Math.round(v * 100)}%` : '—';

const AnalysisResults: React.FC<AnalysisResultsProps> = ({ analysis }) => {
  if (!analysis) {
    return (
      <div className="text-center text-gray-600 py-8">No analysis selected.</div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Optimism</div>
          <div className="text-2xl font-semibold">{pct(analysis.optimism_score)}</div>
          <div className="text-xs text-gray-500">Confidence: {pct(analysis.optimism_confidence)}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Risk</div>
          <div className="text-2xl font-semibold">{pct(analysis.risk_score)}</div>
          <div className="text-xs text-gray-500">Confidence: {pct(analysis.risk_confidence)}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Uncertainty</div>
          <div className="text-2xl font-semibold">{pct(analysis.uncertainty_score)}</div>
          <div className="text-xs text-gray-500">Confidence: {pct(analysis.uncertainty_confidence)}</div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-4">
        <div className="text-sm font-medium text-gray-700 mb-2">Key Themes</div>
        {analysis.key_themes?.length ? (
          <div className="flex flex-wrap gap-2">
            {analysis.key_themes.map((t, idx) => {
              const isObj = t && typeof t === 'object';
              const term = isObj ? (t as any).term ?? JSON.stringify(t) : (t as string);
              const weight = isObj ? (t as any).weight : undefined;
              return (
                <span key={`${term}-${idx}`} className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded">
                  {term}{typeof weight === 'number' ? ` (${Math.round(weight * 100)}%)` : ''}
                </span>
              );
            })}
          </div>
        ) : (
          <div className="text-sm text-gray-500">No themes extracted.</div>
        )}
      </div>

      {analysis.risk_indicators?.length ? (
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm font-medium text-gray-700 mb-2">Risk Indicators</div>
          <ul className="list-disc list-inside text-sm text-gray-700">
            {analysis.risk_indicators.map((r, idx) => {
              if (r && typeof r === 'object') {
                const o: any = r;
                const label = o.detail || o.term || o.type || JSON.stringify(o);
                const meta = [o.severity, o.type].filter(Boolean).join(' • ');
                return (
                  <li key={`risk-${idx}`}>
                    {label}{meta ? ` (${meta})` : ''}
                  </li>
                );
              }
              return <li key={`risk-${idx}`}>{String(r)}</li>;
            })}
          </ul>
        </div>
      ) : null}

      <div className="text-xs text-gray-500">
        Model: {analysis.model_version} • Processing time: {Math.round(analysis.processing_time_seconds)}s
      </div>
    </div>
  );
};

export default AnalysisResults;


