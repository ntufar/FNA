import React from 'react';
import TimelineChart, { TimelinePoint } from '../charts/TimelineChart';

interface SentimentTrendsProps {
  companyName: string;
  data: TimelinePoint[];
}

const SentimentTrends: React.FC<SentimentTrendsProps> = ({ companyName, data }) => {
  const [showOptimism, setShowOptimism] = React.useState(true);
  const [showRisk, setShowRisk] = React.useState(true);
  const [showUncertainty, setShowUncertainty] = React.useState(true);

  return (
    <div className="bg-white rounded-lg shadow p-4 md:p-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Sentiment Trends</h3>
          <p className="text-sm text-gray-500">{companyName} • Quarterly trend (0% - 100%)</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="inline-flex items-center gap-2 text-sm text-gray-700">
            <input type="checkbox" checked={showOptimism} onChange={(e) => setShowOptimism(e.target.checked)} />
            <span className="inline-flex items-center gap-1">
              <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: '#10b981' }} /> Optimism
            </span>
          </label>
          <label className="inline-flex items-center gap-2 text-sm text-gray-700">
            <input type="checkbox" checked={showRisk} onChange={(e) => setShowRisk(e.target.checked)} />
            <span className="inline-flex items-center gap-1">
              <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: '#ef4444' }} /> Risk
            </span>
          </label>
          <label className="inline-flex items-center gap-2 text-sm text-gray-700">
            <input type="checkbox" checked={showUncertainty} onChange={(e) => setShowUncertainty(e.target.checked)} />
            <span className="inline-flex items-center gap-1">
              <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: '#f59e0b' }} /> Uncertainty
            </span>
          </label>
        </div>
      </div>

      <TimelineChart
        data={data}
        showOptimism={showOptimism}
        showRisk={showRisk}
        showUncertainty={showUncertainty}
      />
    </div>
  );
};

export default SentimentTrends;


