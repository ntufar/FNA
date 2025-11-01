import React from 'react';

type Thresholds = {
  sentimentShift: number; // percent 5..50
  riskIncrease: number; // percent 5..50
  themeChange: number; // percent 5..50
};

interface AlertsPanelProps {
  sector?: string;
  industry?: string;
  initialThresholds?: Partial<Thresholds>;
  onChange?: (thresholds: Thresholds) => void;
}

// Simple industry defaults. Can be extended or fetched from backend later.
const INDUSTRY_DEFAULTS: Record<string, Thresholds> = {
  'Technology': { sentimentShift: 12, riskIncrease: 10, themeChange: 15 },
  'Financials': { sentimentShift: 8, riskIncrease: 7, themeChange: 12 },
  'Healthcare': { sentimentShift: 10, riskIncrease: 9, themeChange: 14 },
  'Energy': { sentimentShift: 15, riskIncrease: 12, themeChange: 18 },
  'Default': { sentimentShift: 10, riskIncrease: 10, themeChange: 15 },
};

function clampPercent(value: number): number {
  return Math.min(50, Math.max(5, Math.round(value)));
}

const AlertsPanel: React.FC<AlertsPanelProps> = ({ sector, industry, initialThresholds, onChange }) => {
  const defaults = React.useMemo<Thresholds>(() => {
    if (industry && INDUSTRY_DEFAULTS[industry]) return INDUSTRY_DEFAULTS[industry];
    if (sector && INDUSTRY_DEFAULTS[sector]) return INDUSTRY_DEFAULTS[sector];
    return INDUSTRY_DEFAULTS['Default'];
  }, [sector, industry]);

  const [thresholds, setThresholds] = React.useState<Thresholds>({
    sentimentShift: clampPercent(initialThresholds?.sentimentShift ?? defaults.sentimentShift),
    riskIncrease: clampPercent(initialThresholds?.riskIncrease ?? defaults.riskIncrease),
    themeChange: clampPercent(initialThresholds?.themeChange ?? defaults.themeChange),
  });

  React.useEffect(() => {
    onChange?.(thresholds);
  }, [thresholds, onChange]);

  function handleChange(key: keyof Thresholds, value: number) {
    setThresholds((prev) => ({ ...prev, [key]: clampPercent(value) }));
  }

  return (
    <div className="bg-white rounded-lg shadow p-4 md:p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Alerts & Thresholds</h3>
        <p className="text-sm text-gray-500">
          Configure alert thresholds (allowed range 5% - 50%). Defaults are based on {industry || sector || 'industry'} norms.
        </p>
      </div>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Sentiment Shift Threshold: <span className="text-gray-900">{thresholds.sentimentShift}%</span>
          </label>
          <input
            type="range"
            min={5}
            max={50}
            value={thresholds.sentimentShift}
            onChange={(e) => handleChange('sentimentShift', Number(e.target.value))}
            className="w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Risk Increase Threshold: <span className="text-gray-900">{thresholds.riskIncrease}%</span>
          </label>
          <input
            type="range"
            min={5}
            max={50}
            value={thresholds.riskIncrease}
            onChange={(e) => handleChange('riskIncrease', Number(e.target.value))}
            className="w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Theme Change Threshold: <span className="text-gray-900">{thresholds.themeChange}%</span>
          </label>
          <input
            type="range"
            min={5}
            max={50}
            value={thresholds.themeChange}
            onChange={(e) => handleChange('themeChange', Number(e.target.value))}
            className="w-full"
          />
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded"
            onClick={() => setThresholds(defaults)}
          >
            Reset to Industry Defaults
          </button>
          <button
            type="button"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
            onClick={() => onChange?.(thresholds)}
          >
            Save Preferences
          </button>
        </div>
      </div>
    </div>
  );
};

export default AlertsPanel;


