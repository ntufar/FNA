/**
 * Companies Page Component
 * 
 * Manage tracked companies and their information.
 */

import React from 'react';
import { toast } from 'react-toastify';
import CompanySearch from '../components/companies/CompanySearch';
import apiClient, { Company } from '../services/api';

const CompaniesPage: React.FC = () => {
  const [showAddModal, setShowAddModal] = React.useState(false);
  const [companies, setCompanies] = React.useState<Company[]>([]);
  const [loading, setLoading] = React.useState<boolean>(false);
  const [query, setQuery] = React.useState<string>('');

  const handleOpenAdd = () => setShowAddModal(true);
  const handleCloseAdd = () => setShowAddModal(false);

  const loadCompanies = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiClient.getCompanies();
      // Sort by ticker asc for stable display
      const sorted = [...data].sort((a, b) => a.ticker_symbol.localeCompare(b.ticker_symbol));
      setCompanies(sorted);
    } catch (e) {
      // errors are handled globally in api client; keep UX snappy
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadCompanies();
  }, [loadCompanies]);

  const filtered = React.useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return companies;
    return companies.filter(c =>
      c.ticker_symbol.toLowerCase().includes(q) || (c.company_name || '').toLowerCase().includes(q)
    );
  }, [companies, query]);

  const handleDelete = async (id: string) => {
    const company = companies.find(c => c.id === id);
    if (!company) return;
    const confirmed = window.confirm(`Delete ${company.ticker_symbol} (${company.company_name})?`);
    if (!confirmed) return;
    try {
      await apiClient.deleteCompany(id);
      setCompanies(prev => prev.filter(c => c.id !== id));
      toast.success('Company deleted');
    } catch (e) {
      // error toast handled by api client
    }
  };

  const handleAdded = (created: Company) => {
    // Insert new company and re-sort
    setCompanies(prev => {
      const next = [created, ...prev.filter(c => c.id !== created.id)];
      next.sort((a, b) => a.ticker_symbol.localeCompare(b.ticker_symbol));
      return next;
    });
    handleCloseAdd();
    toast.success('Company added');
  };

  return (
    <div>
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Companies</h1>
            <p className="text-gray-600 mt-1">
              Manage companies you're tracking for analysis
            </p>
          </div>
          
          <button onClick={handleOpenAdd} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
            + Add Company
          </button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="mb-4 flex items-center gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by ticker or name"
          className="w-full md:w-80 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        />
        <button
          type="button"
          onClick={loadCompanies}
          className="px-3 py-2 bg-gray-100 text-gray-800 rounded-md hover:bg-gray-200"
        >
          Refresh
        </button>
      </div>

      {/* Companies List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="px-6 py-8 text-center text-gray-600">Loading companies…</div>
        ) : filtered.length === 0 ? (
          <div className="px-6 py-8 text-center text-gray-600">No companies found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ticker</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sector</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Industry</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filtered.map((c) => (
                  <tr key={c.id}>
                    <td className="px-6 py-3 font-medium text-gray-900">{c.ticker_symbol}</td>
                    <td className="px-6 py-3 text-gray-700">{c.company_name}</td>
                    <td className="px-6 py-3 text-gray-700">{c.sector || '—'}</td>
                    <td className="px-6 py-3 text-gray-700">{c.industry || '—'}</td>
                    <td className="px-6 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => handleDelete(c.id)}
                        className="inline-flex items-center px-3 py-1.5 text-sm bg-red-50 text-red-700 rounded-md hover:bg-red-100"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Company Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={handleCloseAdd} />
          <div className="relative bg-white rounded-lg shadow-lg w-full max-w-xl mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Add Company</h2>
              <button onClick={handleCloseAdd} className="text-gray-500 hover:text-gray-700">✕</button>
            </div>
            <CompanySearch onSelect={handleAdded} />
          </div>
        </div>
      )}
    </div>
  );
};

export default CompaniesPage;
