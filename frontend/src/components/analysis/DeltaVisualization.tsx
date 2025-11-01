import React from 'react';

interface DeltaVisualizationProps {
  optimismDelta: number;
  riskDelta: number;
  uncertaintyDelta: number;
  overallDelta: number;
}

const Bar: React.FC<{ label: string; value: number; positiveColor: string; negativeColor: string }> = ({ label, value, positiveColor, negativeColor }) => {
  const magnitude = Math.min(Math.abs(value), 1);
  const widthPercent = Math.round(magnitude * 100);
  const isPositive = value >= 0;
  const color = isPositive ? positiveColor : negativeColor;
  const directionClass = isPositive ? 'justify-start' : 'justify-end';

  return (
    <div className="mb-3">
      <div className="flex items-center justify-between text-sm text-gray-700 mb-1">
        <span>{label}</span>
        <span className="font-mono">{value.toFixed(3)}</span>
      </div>
      <div className={`w-full h-3 bg-gray-100 rounded overflow-hidden flex ${directionClass}`}>
        <div className={`h-3 ${color}`} style={{ width: `${widthPercent}%` }} />
      </div>
    </div>
  );
};

const DeltaVisualization: React.FC<DeltaVisualizationProps> = ({
  optimismDelta,
  riskDelta,
  uncertaintyDelta,
  overallDelta,
}) => {
  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">Delta Visualization</h3>
      <Bar label="Optimism" value={optimismDelta} positiveColor="bg-green-500" negativeColor="bg-red-500" />
      <Bar label="Risk" value={riskDelta} positiveColor="bg-red-500" negativeColor="bg-green-500" />
      <Bar label="Uncertainty" value={uncertaintyDelta} positiveColor="bg-yellow-500" negativeColor="bg-blue-500" />
      <Bar label="Overall Sentiment" value={overallDelta} positiveColor="bg-green-600" negativeColor="bg-red-600" />
    </div>
  );
};

export default DeltaVisualization;


