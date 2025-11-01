import React, { useEffect, useMemo, useState } from 'react';
import apiClient, { Company, CreateCompanyRequest } from '../../services/api';

interface CompanySearchProps {
  onSelect?: (company: Company) => void;
}

const CompanySearch: React.FC<CompanySearchProps> = ({ onSelect }) => {
  const [query, setQuery] = useState<string>('');
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [creating, setCreating] = useState<boolean>(false);

  useEffect(() => {
    let ignore = false;
    const load = async () => {
      setLoading(true);
      try {
        const data = await apiClient.getCompanies();
        if (!ignore) setCompanies(data);
      } finally {
        setLoading(false);
      }
    };
    load();
    return () => { ignore = true; };
  }, []);

  const filtered = useMemo(() => {
    if (!query.trim()) return companies;
    const q = query.trim().toLowerCase();
    return companies.filter(c => (
      c.ticker_symbol.toLowerCase().includes(q) ||
      (c.company_name || '').toLowerCase().includes(q)
    ));
  }, [companies, query]);

  const handleCreate = async () => {
    const ticker = query.trim().toUpperCase();
    if (!ticker || ticker.length > 10) return;
    setCreating(true);
    try {
      const payload: CreateCompanyRequest = {
        ticker_symbol: ticker,
        company_name: ticker,
      };
      const created = await apiClient.createCompany(payload);
      setCompanies(prev => [created, ...prev]);
      onSelect?.(created);
      setQuery('');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="w-full">
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search companies by ticker or name"
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        />
        <button
          type="button"
          onClick={handleCreate}
          disabled={!query.trim() || creating}
          className="px-3 py-2 bg-blue-600 text-white rounded-md disabled:opacity-60"
        >
          {creating ? 'Adding…' : 'Add'}
        </button>
      </div>

      <div className="mt-3 bg-white border border-gray-200 rounded-md max-h-64 overflow-auto">
        {loading ? (
          <div className="p-3 text-sm text-gray-500">Loading…</div>
        ) : (
          filtered.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => onSelect?.(c)}
              className="w-full text-left px-3 py-2 hover:bg-gray-50 border-b last:border-b-0"
            >
              <div className="flex items-center justify-between">
                <span className="font-medium">{c.ticker_symbol}</span>
                <span className="text-sm text-gray-600">{c.company_name}</span>
              </div>
            </button>
          ))
        )}
        {!loading && filtered.length === 0 && (
          <div className="p-3 text-sm text-gray-500">No companies found.</div>
        )}
      </div>
    </div>
  );
};

export default CompanySearch;


