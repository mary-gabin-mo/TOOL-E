import React, { useState, useMemo, useRef, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, ChevronDown, ArrowUp, ArrowDown, ArrowUpDown, Loader2 } from 'lucide-react';
import { AddToolModal } from './AddToolModal';
import { api } from '../../lib/axios';

// API Response type
interface Tool {
  id: number;
  name: string;
  type: string;
  total_quantity: number;
  available_quantity: number;
}

type SortKey = 'name' | 'available_quantity';
type SortDirection = 'asc' | 'desc';

export const InventoryPage = () => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  
  // Fetch Tools
  const { data: tools = [], isLoading, isError } = useQuery<Tool[]>({
    queryKey: ['tools'],
    queryFn: async () => {
      const { data } = await api.get('/tools');
      return data;
    },
  });

  // Sorting State
  const [sortConfig, setSortConfig] = useState<{ key: SortKey; direction: SortDirection }>({
    key: 'name',
    direction: 'asc',
  });

  // Filtering State
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

  // Derived Data
  const filteredAndSortedData = useMemo(() => {
    let data = [...tools];

    // 1. Filter by Type
    if (selectedTypes.length > 0) {
      data = data.filter((item) => selectedTypes.includes(item.type));
    }

    // 2. Sort
    data.sort((a, b) => {
      if (sortConfig.key === 'name') {
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
  }, [tools, sortConfig, selectedTypes]); // Depend on tools instead of inventoryData

  const handleSort = (key: SortKey) => {
    setSortConfig((current) => ({
      key,
      direction:
        current.key === key && current.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const toggleTypeFilter = (type: string) => {
    setSelectedTypes((prev) =>
      prev.includes(type)
        ? prev.filter((t) => t !== type)
        : [...prev, type]
    );
  };

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
      <div className="flex justify-between items-start">
        <h2 className="text-2xl font-bold text-black">Tool Inventory</h2>
        <button
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add New Tool
        </button>
      </div>

      {/* Inventory Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-visible">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-gray-100">
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

              {/* Type Column - Filterable */}
              <th className="py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider relative">
                <div ref={dropdownRef} className="relative inline-block">
                  <div 
                    className="flex items-center cursor-pointer hover:text-gray-700"
                    onClick={() => setIsTypeDropdownOpen(!isTypeDropdownOpen)}
                  >
                    Type
                    <ChevronDown className="w-3 h-3 ml-1" />
                  </div>
                  
                  {/* Type Filter Dropdown */}
                  {isTypeDropdownOpen && (
                    <div className="absolute top-full left-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-100 z-10 p-2">
                      {uniqueTypes.map((type) => (
                        <label key={type} className="flex items-center px-2 py-2 hover:bg-gray-50 rounded cursor-pointer">
                          <input
                            type="checkbox"
                            checked={selectedTypes.includes(type)}
                            onChange={() => toggleTypeFilter(type)}
                            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                          />
                          <span className="ml-2 text-sm text-gray-700">{type}</span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>
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
            </tr>
          </thead>
          <tbody className="">
            {filteredAndSortedData.map((item) => (
              <tr key={item.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                <td className="py-4 px-6 text-sm font-medium text-gray-900">
                  {item.name}
                </td>
                <td className="py-4 px-6 text-sm text-gray-500">
                  {item.type}
                </td>
                <td className="py-4 px-6 text-sm text-gray-500">
                  {item.total_quantity}
                </td>
                <td className="py-4 px-6 text-sm text-gray-500">
                  {item.available_quantity}
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
