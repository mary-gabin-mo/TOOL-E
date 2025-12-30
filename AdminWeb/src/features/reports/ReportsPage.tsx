import React, { useState, useRef, useEffect, useMemo } from 'react';
import { ChevronDown } from 'lucide-react';
import clsx from 'clsx';

// Mock Data
const reportData = [
  { id: 1, user: 'Mary Mo', tool: 'Tape Measure', dateOut: '2025-10-28', dateDue: '2025-11-03', status: 'Borrowed' },
  { id: 2, user: 'Hajin Kim', tool: 'Box Cutter', dateOut: '2025-10-28', dateDue: '2025-10-31', status: 'Borrowed' },
  { id: 3, user: 'Jason Pang', tool: 'Super Glue', dateOut: '2025-10-20', dateDue: 'N/A', status: 'Consumed' },
  { id: 4, user: 'Hongwoo Yoon', tool: 'Side Cutting Pliers', dateOut: '2025-10-24', dateDue: '2025-10-27', status: 'Returned' },
  { id: 5, user: 'Howard Kim', tool: 'Tape Measure', dateOut: '2025-10-26', dateDue: '2025-10-27', status: 'Overdue' },
];

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
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Filtering State
  const [isStatusDropdownOpen, setIsStatusDropdownOpen] = useState(false);
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([]);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const uniqueStatuses = Array.from(new Set(reportData.map((row) => row.status)));

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsStatusDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const toggleStatusFilter = (status: string) => {
    setSelectedStatuses((prev) =>
      prev.includes(status)
        ? prev.filter((s) => s !== status)
        : [...prev, status]
    );
  };

  // Filter data based on status
  const filteredReportData = useMemo(() => {
    return reportData.filter((row) => {
      return selectedStatuses.length === 0 || selectedStatuses.includes(row.status);
    });
  }, [selectedStatuses]);

  const handleGenerate = () => {
    console.log('Generating report for:', startDate, 'to', endDate);
  };

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold text-black">Generate Reports</h2>

      {/* Filter Card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 max-w-3xl">
        <div className="flex items-end gap-6">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-500"
            />
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-500"
            />
          </div>
          <div>
            <button
              onClick={handleGenerate}
              className="px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors"
            >
              Generate Report
            </button>
          </div>
        </div>
      </div>

      {/* Results Section */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-bold text-black">
            Report Results (2025-10-01 to 2025-10-28)
          </h3>
          <button className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors">
            Download
          </button>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Tool
                </th>
                <th className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Date Out
                </th>
                <th className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Date Due
                </th>
                <th className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider relative">
                  <div ref={dropdownRef} className="relative inline-block">
                    <div 
                      className="flex items-center cursor-pointer hover:text-gray-700"
                      onClick={() => setIsStatusDropdownOpen(!isStatusDropdownOpen)}
                    >
                      Status
                      <ChevronDown className="w-3 h-3 ml-1" />
                    </div>

                    {/* Status Filter Dropdown */}
                    {isStatusDropdownOpen && (
                      <div className="absolute top-full right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-100 z-10 p-2">
                        {uniqueStatuses.map((status) => (
                          <label key={status} className="flex items-center px-2 py-2 hover:bg-gray-50 rounded cursor-pointer">
                            <input
                              type="checkbox"
                              checked={selectedStatuses.includes(status)}
                              onChange={() => toggleStatusFilter(status)}
                              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                            />
                            <span className="ml-2 text-sm text-gray-700">{status}</span>
                          </label>
                        ))}
                      </div>
                    )}
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="">
              {filteredReportData.map((row) => (
                <tr key={row.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                  <td className="py-4 px-6 text-sm font-medium text-gray-900">
                    {row.user}
                  </td>
                  <td className="py-4 px-6 text-sm text-gray-500">
                    {row.tool}
                  </td>
                  <td className="py-4 px-6 text-sm text-gray-500">
                    {row.dateOut}
                  </td>
                  <td className="py-4 px-6 text-sm text-gray-500">
                    {row.dateDue}
                  </td>
                  <td className="py-4 px-6 text-sm">
                    <StatusBadge status={row.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
