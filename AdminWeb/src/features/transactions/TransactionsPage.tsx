import React, { useState, useRef, useEffect, useMemo } from 'react';
import { ChevronDown, Trash2, Search, ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react';
import clsx from 'clsx';

// Mock Data
const transactions = [
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

export const TransactionsPage = () => {
  const [searchTerm, setSearchTerm] = useState('');
  
  // Sorting State
  const [sortConfig, setSortConfig] = useState<{ key: 'dateOut' | 'dateDue'; direction: 'asc' | 'desc' }>({
    key: 'dateOut',
    direction: 'desc',
  });

  // Filtering State
  const [isStatusDropdownOpen, setIsStatusDropdownOpen] = useState(false);
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([]);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const uniqueStatuses = Array.from(new Set(transactions.map((tx) => tx.status)));

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

  const handleSort = (key: 'dateOut' | 'dateDue') => {
    setSortConfig((current) => ({
      key,
      direction:
        current.key === key && current.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  // Filter transactions based on search term and status
  const filteredAndSortedTransactions = useMemo(() => {
    const data = transactions.filter((tx) => {
      const searchLower = searchTerm.toLowerCase();
      const matchesSearch = 
        tx.user.toLowerCase().includes(searchLower) ||
        tx.tool.toLowerCase().includes(searchLower);
      
      const matchesStatus = selectedStatuses.length === 0 || selectedStatuses.includes(tx.status);

      return matchesSearch && matchesStatus;
    });

    // Sort
    return data.sort((a, b) => {
      if (sortConfig.key === 'dateOut') {
        return sortConfig.direction === 'asc'
          ? a.dateOut.localeCompare(b.dateOut)
          : b.dateOut.localeCompare(a.dateOut);
      } else if (sortConfig.key === 'dateDue') {
        const valA = a.dateDue;
        const valB = b.dateDue;

        // If values are different, sort by Date Due
        if (valA !== valB) {
          // Handle N/A: Always put N/A at the bottom regardless of sort direction
          if (valA === 'N/A') return 1;
          if (valB === 'N/A') return -1;
          
          return sortConfig.direction === 'asc'
            ? valA.localeCompare(valB)
            : valB.localeCompare(valA);
        }

        // If Date Due is the same (e.g. both 'N/A' or same date), sort by Date Out
        return sortConfig.direction === 'asc'
          ? a.dateOut.localeCompare(b.dateOut)
          : b.dateOut.localeCompare(a.dateOut);
      }
      return 0;
    });
  }, [searchTerm, selectedStatuses, sortConfig]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-black">Transaction Log</h2>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <input
          type="text"
          placeholder="Search by user or tool"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-4 pr-4 py-3 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
        />
        {/* <Search className="absolute right-4 top-3.5 text-gray-400 w-5 h-5" /> */}
      </div>

      {/* Transactions Table */}
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
              <th 
                className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => handleSort('dateOut')}
              >
                <div className="flex items-center">
                  Date Out
                  {sortConfig.key === 'dateOut' ? (
                    sortConfig.direction === 'asc' ? <ArrowUp className="w-3 h-3 ml-1" /> : <ArrowDown className="w-3 h-3 ml-1" />
                  ) : (
                    <ArrowUpDown className="w-3 h-3 ml-1 text-gray-300" />
                  )}
                </div>
              </th>
              <th 
                className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => handleSort('dateDue')}
              >
                <div className="flex items-center">
                  Date Due
                  {sortConfig.key === 'dateDue' ? (
                    sortConfig.direction === 'asc' ? <ArrowUp className="w-3 h-3 ml-1" /> : <ArrowDown className="w-3 h-3 ml-1" />
                  ) : (
                    <ArrowUpDown className="w-3 h-3 ml-1 text-gray-300" />
                  )}
                </div>
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
              <th className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                {/* Actions column */}
              </th>
            </tr>
          </thead>
          <tbody className="">
            {filteredAndSortedTransactions.map((tx) => (
              <tr key={tx.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                <td className="py-4 px-6 text-sm font-medium text-gray-900">
                  {tx.user}
                </td>
                <td className="py-4 px-6 text-sm text-gray-500">
                  {tx.tool}
                </td>
                <td className="py-4 px-6 text-sm text-gray-500">
                  {tx.dateOut}
                </td>
                <td className="py-4 px-6 text-sm text-gray-500">
                  {tx.dateDue}
                </td>
                <td className="py-4 px-6 text-sm">
                  <StatusBadge status={tx.status} />
                </td>
                <td className="py-4 px-6 text-sm text-right">
                  <button className="text-gray-400 hover:text-red-500 transition-colors">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
