import React, { useState } from 'react';
import { Download, Loader2, Calendar } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import clsx from 'clsx';
import { api } from '../../lib/axios';

interface Transaction {
  transaction_id: number;
  user_name: string;
  tool_name: string;
  checkout_timestamp: string;
  desired_return_date: string | null;
  return_timestamp: string | null;
  status: string;
  quantity: number;
}

const StatusBadge = ({ status }: { status: string }) => {
  const styles = {
    Borrowed: 'bg-blue-100 text-blue-700',
    Consumed: 'bg-gray-100 text-gray-700',
    Returned: 'bg-green-100 text-green-700',
    Overdue: 'bg-red-100 text-red-700',
  };

  return (
    <span
      className={clsx(
        'px-3 py-1 rounded-full text-xs font-semibold',
        styles[status as keyof typeof styles] || 'bg-gray-100 text-gray-700'
      )}
    >
      {status}
    </span>
  );
};

export const ReportsPage = () => {
  // Date state
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  
  // Trigger for refetching
  const [enabled, setEnabled] = useState(false);

  // Fetch Data
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['reports', startDate, endDate],
    queryFn: async () => {
      const params: any = { limit: 1000 }; // Fetch up to 1000 records for the report
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      
      const response = await api.get<{ items: Transaction[] }>('/transactions', { params });
      return response.data.items;
    },
    enabled: enabled, // Only run when enabled (after clicking Generate)
  });

  const handleGenerate = () => {
    if (!startDate || !endDate) return;
    setEnabled(true);
    refetch();
  };

  const handleDownload = () => {
    if (!data || data.length === 0) return;

    const headers = ['Transaction ID', 'User', 'Tool', 'Date Out', 'Due Date', 'Returned Date', 'Status', 'Quantity'];
    const rows = data.map(item => [
      item.transaction_id,
      `"${item.user_name || 'Unknown'}"`,
      `"${item.tool_name || 'Unknown'}"`,
      new Date(item.checkout_timestamp).toLocaleString(),
      item.desired_return_date ? new Date(item.desired_return_date).toLocaleDateString() : 'N/A',
      item.return_timestamp ? new Date(item.return_timestamp).toLocaleString() : 'N/A',
      item.status,
      item.quantity
    ]);

    const csvContent = "data:text/csv;charset=utf-8," 
      + [headers.join(','), ...rows.map(e => e.join(','))].join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `report_${startDate || 'all'}_to_${endDate || 'all'}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-black">Generate Reports</h2>
      </div>

      {/* Filter Card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col sm:flex-row items-end gap-6">
          <div className="flex-1 w-full">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-600"
              />
            </div>
          </div>
          <div className="flex-1 w-full">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-600"
              />
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleGenerate}
              disabled={!startDate || !endDate}
              className={`px-6 py-2 rounded-md transition-colors font-medium ${
                !startDate || !endDate
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              Generate Report
            </button>
            {data && data.length > 0 && (
              <button
                onClick={handleDownload}
                className="px-6 py-2 border border-green-600 text-green-600 bg-green-50 rounded-md hover:bg-green-100 transition-colors font-medium flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Export CSV
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Results Table */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : isError ? (
        <div className="text-red-500 bg-red-50 p-4 rounded-md">
          Failed to load report data. Please try again.
        </div>
      ) : data ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          {data.length === 0 ? (
            <div className="p-12 text-center text-gray-500">
              No transactions found for the selected period.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-100">
                    <th className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">Transaction ID</th>
                    <th className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">User</th>
                    <th className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">Tool</th>
                    <th className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">Date Out</th>
                    <th className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">Due Date</th>
                    <th className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.map((item) => (
                    <tr key={item.transaction_id} className="hover:bg-gray-50 transition-colors">
                      <td className="py-4 px-6 text-sm text-gray-900 font-medium">#{item.transaction_id}</td>
                      <td className="py-4 px-6 text-sm text-gray-600">{item.user_name || 'Unknown'}</td>
                      <td className="py-4 px-6 text-sm text-gray-600">{item.tool_name || 'Unknown'}</td>
                      <td className="py-4 px-6 text-sm text-gray-600">
                        {new Date(item.checkout_timestamp).toLocaleDateString()}
                        <span className="text-gray-400 text-xs ml-1">
                            {new Date(item.checkout_timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </span>
                      </td>
                      <td className="py-4 px-6 text-sm text-gray-600">
                        {item.desired_return_date ? new Date(item.desired_return_date).toLocaleDateString() : '-'}
                      </td>
                      <td className="py-4 px-6 text-sm">
                        <StatusBadge status={item.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-dashed border-gray-300">
          <div className="text-gray-500">Select dates and click "Generate Report" to view transactions.</div>
        </div>
      )}
    </div>
  );
};
