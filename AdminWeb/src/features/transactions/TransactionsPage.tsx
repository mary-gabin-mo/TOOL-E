import React, { useState, useRef, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ChevronDown, Trash2, ArrowUp, ArrowDown, ArrowUpDown, Loader2, ChevronLeft, ChevronRight } from 'lucide-react';
import clsx from 'clsx';
import { api } from '../../lib/axios';

interface Transaction {
  transaction_id: number;
  user_id: number | null;
  tool_id: number | null;
  checkout_timestamp: string;
  desired_return_date: string | null;
  return_timestamp: string | null;
  quantity: number;
  purpose: string | null;
  image_path: string | null;
  classification_correct: boolean | null;
  weight: number;
}

interface TransactionsResponse {
  items: Transaction[];
  total: number;
  page: number;
  size: number;
  pages: number;
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

export const TransactionsPage = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();

  const { data, isLoading, isError, error } = useQuery<TransactionsResponse>({
    queryKey: ['transactions', page],
    queryFn: async () => {
      const { data } = await api.get('/transactions', {
        params: { page, limit: 50 }
      });
      return data;
    },
  });

  const transactions = data?.items || [];
  const totalPages = data?.pages || 1;

  const deleteMutation = useMutation({
    mutationFn: async (transactionId: number) => {
      await api.delete(`/transactions/${transactionId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    },
  });
  
  // Sorting State
  const [sortConfig, setSortConfig] = useState<{ key: 'dateOut' | 'dateDue'; direction: 'asc' | 'desc' }>({
    key: 'dateOut',
    direction: 'desc',
  });

  // Filtering State
  const [isStatusDropdownOpen, setIsStatusDropdownOpen] = useState(false);
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([]);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const uniqueStatuses = Array.from(new Set(transactions.map((tx) => deriveStatus(tx))));

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
        String(tx.user_id ?? '').includes(searchLower) ||
        String(tx.tool_id ?? '').includes(searchLower) ||
        (tx.purpose ?? '').toLowerCase().includes(searchLower);
      
      const matchesStatus = selectedStatuses.length === 0 || selectedStatuses.includes(deriveStatus(tx));

      return matchesSearch && matchesStatus;
    });

    // Sort
    return data.sort((a, b) => {
      if (sortConfig.key === 'dateOut') {
        return sortConfig.direction === 'asc'
          ? a.checkout_timestamp.localeCompare(b.checkout_timestamp)
          : b.checkout_timestamp.localeCompare(a.checkout_timestamp);
      } else if (sortConfig.key === 'dateDue') {
        const valA = a.desired_return_date || 'N/A';
        const valB = b.desired_return_date || 'N/A';

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
          ? a.checkout_timestamp.localeCompare(b.checkout_timestamp)
          : b.checkout_timestamp.localeCompare(a.checkout_timestamp);
      }
      return 0;
    });
  }, [searchTerm, selectedStatuses, sortConfig, transactions]);

  function deriveStatus(tx: Transaction) {
    if (tx.return_timestamp) return 'Returned';
    if (tx.desired_return_date) {
      const due = new Date(tx.desired_return_date);
      if (!isNaN(due.getTime()) && Date.now() > due.getTime()) return 'Overdue';
    }
    return 'Borrowed';
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-black">Transaction Log</h2>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <input
          type="text"
          placeholder="Search by user ID, tool ID, or purpose"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-4 pr-4 py-3 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
        />
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
            {isLoading ? (
              <tr>
                <td colSpan={6} className="py-10 text-center text-sm text-gray-500">
                  Loading transactions...
                </td>
              </tr>
            ) : isError ? (
              <tr>
                <td colSpan={6} className="py-10 text-center text-sm text-red-500">
                  Failed to load transactions.
                  {error instanceof Error ? ` ${error.message}` : ''}
                </td>
              </tr>
            ) : filteredAndSortedTransactions.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-10 text-center text-sm text-gray-500">
                  No transactions found.
                </td>
              </tr>
            ) : (
              filteredAndSortedTransactions.map((tx) => (
              <tr key={tx.transaction_id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                <td className="py-4 px-6 text-sm font-medium text-gray-900">
                  {tx.user_id ?? 'N/A'}
                </td>
                <td className="py-4 px-6 text-sm text-gray-500">
                  {tx.tool_id ?? 'N/A'}
                </td>
                <td className="py-4 px-6 text-sm text-gray-500">
                  {tx.checkout_timestamp}
                </td>
                <td className="py-4 px-6 text-sm text-gray-500">
                  {tx.desired_return_date ?? 'N/A'}
                </td>
                <td className="py-4 px-6 text-sm">
                  <StatusBadge status={deriveStatus(tx)} />
                </td>
                <td className="py-4 px-6 text-sm text-right">
                  <button
                    className="text-gray-400 hover:text-red-500 transition-colors"
                    onClick={() => deleteMutation.mutate(tx.transaction_id)}
                    disabled={deleteMutation.isPending}
                  >
                    {deleteMutation.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                  </button>
                </td>
              </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6 rounded-lg shadow-sm">
        <div className="flex flex-1 justify-between sm:hidden">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            Previous
          </button>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            Next
          </button>
        </div>
        <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-gray-700">
              Showing page <span className="font-medium">{page}</span> of{' '}
              <span className="font-medium">{totalPages}</span> ({data?.total || 0} results)
            </p>
          </div>
          <div>
            <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
              >
                <span className="sr-only">Previous</span>
                <ChevronLeft className="h-5 w-5" aria-hidden="true" />
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1)
                .filter(p => p === 1 || p === totalPages || Math.abs(page - p) <= 1)
                .map((p, index, array) => {
                   // Add ellipsis logic if needed, simplify for now
                   const showEllipsis = index > 0 && p - array[index - 1] > 1;

                   return (
                    <React.Fragment key={p}>
                      {showEllipsis && <span className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-700 ring-1 ring-inset ring-gray-300 focus:outline-offset-0">...</span>}
                      <button
                        onClick={() => setPage(p)}
                        className={clsx(
                          p === page
                            ? 'relative z-10 inline-flex items-center bg-blue-600 px-4 py-2 text-sm font-semibold text-white focus:z-20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600'
                            : 'relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0'
                        )}
                      >
                        {p}
                      </button>
                    </React.Fragment>
                   );
                })}
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
              >
                <span className="sr-only">Next</span>
                <ChevronRight className="h-5 w-5" aria-hidden="true" />
              </button>
            </nav>
          </div>
        </div>
      </div>
    </div>
  );
};
