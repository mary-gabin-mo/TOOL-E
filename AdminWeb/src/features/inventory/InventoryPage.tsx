import React, { useState, useMemo, useRef, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, ChevronDown, ArrowUp, ArrowDown, ArrowUpDown, Loader2, Search } from 'lucide-react';
import { AddToolModal } from './AddToolModal';
import { api } from '../../lib/axios';

// API Response type
interface Tool {
  id: number;
  name: string;
  size: string | null;
  type: string;
  status: string;
  total_quantity: number;
  available_quantity: number;
  consumed_quantity: number;
  trained: boolean;
}

type SortKey = 'id' | 'name' | 'available_quantity';
type SortDirection = 'asc' | 'desc';

export const InventoryPage = () => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Fetch Tools
  const { data: tools = [], isLoading, isError, error } = useQuery<Tool[]>({
    queryKey: ['tools'],
    queryFn: async () => {
      const { data } = await api.get('/tools');
      return data;
    },
  });

  // Sorting State
  const [sortConfig, setSortConfig] = useState<{ key: SortKey; direction: SortDirection }>({
    key: 'id',
    direction: 'asc',
  });

  // Filtering State (Removed Type)
  /* 
  const [isTypeDropdownOpen, setIsTypeDropdownOpen] = useState(false);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const uniqueTypes = useMemo(() => {
    return Array.from(new Set(tools.map((item) => item.type)));
  }, [tools]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsTypeDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);
  */

  // Derived Data
  const filteredAndSortedData = useMemo(() => {
    let data = [...tools];

    // 1. Filter by Search Query
    if (searchQuery) {
      const lowerQuery = searchQuery.toLowerCase();
      data = data.filter((item) => 
        item.name.toLowerCase().includes(lowerQuery)
      );
    }

    // 2. Sort
    data.sort((a, b) => {
      if (sortConfig.key === 'id') {
        return sortConfig.direction === 'asc'
          ? a.id - b.id
          : b.id - a.id;
      } else if (sortConfig.key === 'name') {
        return sortConfig.direction === 'asc'
          ? a.name.localeCompare(b.name)
          : b.name.localeCompare(a.name);
      } else if (sortConfig.key === 'available_quantity') {
        return sortConfig.direction === 'asc'
          ? a.available_quantity - b.available_quantity
          : b.available_quantity - a.available_quantity;
      }
      return 0;
    });

    return data;
  }, [tools, sortConfig, searchQuery]); // Added searchQuery to dependencies

  const handleSort = (key: SortKey) => {
    setSortConfig((current) => ({
      key,
      direction:
        current.key === key && current.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  /*
  const toggleTypeFilter = (type: string) => {
    setSelectedTypes((prev) =>
      prev.includes(type)
        ? prev.filter((t) => t !== type)
        : [...prev, type]
    );
  };
  */

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="text-red-600 p-4 bg-red-50 rounded-lg">
        Error loading tools. Please try again later.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header & Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h2 className="text-2xl font-bold text-black">Tool Inventory</h2>
        
        <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
          {/* Search Bar */}
          <div className="relative w-full sm:w-96">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition duration-150 ease-in-out"
              placeholder="Search by name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <button
            onClick={() => setIsAddModalOpen(true)}
            className="flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium whitespace-nowrap"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add New Tool
          </button>
        </div>
      </div>

      {/* Inventory Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-visible">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-gray-100">
              {/* ID Column - Sortable */}
              <th 
                className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => handleSort('id')}
              >
                <div className="flex items-center">
                  ID
                  {sortConfig.key === 'id' ? (
                    sortConfig.direction === 'asc' ? <ArrowUp className="w-3 h-3 ml-1" /> : <ArrowDown className="w-3 h-3 ml-1" />
                  ) : (
                    <ArrowUpDown className="w-3 h-3 ml-1 text-gray-300" />
                  )}
                </div>
              </th>

              {/* Name Column - Sortable */}
              <th 
                className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => handleSort('name')}
              >
                <div className="flex items-center">
                  Tool Name
                  {sortConfig.key === 'name' ? (
                    sortConfig.direction === 'asc' ? <ArrowUp className="w-3 h-3 ml-1" /> : <ArrowDown className="w-3 h-3 ml-1" />
                  ) : (
                    <ArrowUpDown className="w-3 h-3 ml-1 text-gray-300" />
                  )}
                </div>
              </th>

              {/* Size Column */}
              <th className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Size
              </th>

              {/* Total Column - Static */}
              <th className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Total
              </th>

              {/* Available Column - Sortable */}
              <th 
                className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => handleSort('available_quantity')}
              >
                <div className="flex items-center">
                  Available
                  {sortConfig.key === 'available_quantity' ? (
                    sortConfig.direction === 'asc' ? <ArrowUp className="w-3 h-3 ml-1" /> : <ArrowDown className="w-3 h-3 ml-1" />
                  ) : (
                    <ArrowUpDown className="w-3 h-3 ml-1 text-gray-300" />
                  )}
                </div>
              </th>

              {/* Status Column */}
              <th className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="">
            {filteredAndSortedData.map((item, index) => (
              <tr key={`${item.id}-${index}`} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                <td className="py-4 px-6 text-sm text-gray-500">
                  #{item.id}
                </td>
                <td className="py-4 px-6 text-sm font-medium text-gray-900">
                  <div className="flex flex-col items-start gap-1">
                    <span>{item.name}</span>
                    {item.trained && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
                        Training Required
                      </span>
                    )}
                  </div>
                </td>
                <td className="py-4 px-6 text-sm text-gray-500">
                  {item.size || '-'}
                </td>
                <td className="py-4 px-6 text-sm text-gray-500">
                  {item.total_quantity}
                </td>
                <td className="py-4 px-6 text-sm text-gray-500">
                  {item.available_quantity}
                </td>
                <td className="py-4 px-6 text-sm">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    item.status === 'Available' ? 'bg-green-100 text-green-700' :
                    item.status === 'Low Stock' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {item.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add Tool Modal */}
      <AddToolModal 
        isOpen={isAddModalOpen} 
        onClose={() => setIsAddModalOpen(false)} 
      />
    </div>
  );
};
