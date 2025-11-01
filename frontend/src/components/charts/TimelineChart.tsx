import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

export interface TimelinePoint {
  dateLabel: string; // e.g. "Q1 2024" or ISO date string
  optimism?: number; // 0..1
  risk?: number; // 0..1
  uncertainty?: number; // 0..1
}

interface TimelineChartProps {
  data: TimelinePoint[];
  height?: number;
  showOptimism?: boolean;
  showRisk?: boolean;
  showUncertainty?: boolean;
}

const TimelineChart: React.FC<TimelineChartProps> = ({
  data,
  height = 280,
  showOptimism = true,
  showRisk = true,
  showUncertainty = true,
}) => {
  const hasAnySeries = showOptimism || showRisk || showUncertainty;

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 16, right: 24, bottom: 8, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="dateLabel" tick={{ fill: '#6b7280' }} />
          <YAxis domain={[0, 1]} tick={{ fill: '#6b7280' }} />
          <Tooltip
            formatter={(value: any) =>
              typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : value
            }
          />
          {hasAnySeries && <Legend />}
          {showOptimism && (
            <Line
              type="monotone"
              dataKey="optimism"
              name="Optimism"
              stroke="#10b981"
              strokeWidth={2}
              dot={{ r: 2 }}
              isAnimationActive={false}
            />
          )}
          {showRisk && (
            <Line
              type="monotone"
              dataKey="risk"
              name="Risk"
              stroke="#ef4444"
              strokeWidth={2}
              dot={{ r: 2 }}
              isAnimationActive={false}
            />
          )}
          {showUncertainty && (
            <Line
              type="monotone"
              dataKey="uncertainty"
              name="Uncertainty"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={{ r: 2 }}
              isAnimationActive={false}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TimelineChart;


