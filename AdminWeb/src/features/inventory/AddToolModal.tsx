import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { X, Loader2 } from 'lucide-react';
import { api } from '../../lib/axios';

interface AddToolModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AddToolModal = ({ isOpen, onClose }: AddToolModalProps) => {
  const [name, setName] = useState('');
  const [size, setSize] = useState('');
  const [isConsumable, setIsConsumable] = useState(false);
  const [total, setTotal] = useState('');
  const [available, setAvailable] = useState('');
  const [consumed, setConsumed] = useState('');
  const [trained, setTrained] = useState(false);
  const [error, setError] = useState('');

  const queryClient = useQueryClient();

  const addToolMutation = useMutation({
    mutationFn: async (newTool: { 
      tool_name: string; 
      tool_size: string | null;
      tool_type: string; 
      total_quantity: number; 
      available_quantity: number;
      trained: boolean;
      current_status: string;
      consumed_quantity: number;
    }) => {
      await api.post('/tools', newTool);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tools'] });
      resetForm();
      onClose();
    },
    onError: () => {
      setError('Failed to add tool. Please try again.');
    }
  });

  const resetForm = () => {
    setName('');
    setSize('');
    setIsConsumable(false);
    setTotal('');
    setAvailable('');
    setConsumed('');
    setTrained(true);
    setError('');
  };

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    const totalQty = parseInt(total);
    const availableQty = parseInt(available);
    const consumedQty = parseInt(consumed);

    if (isNaN(totalQty) || totalQty < 0) {
      setError('Please enter a valid total quantity');
      return;
    }
    if (isNaN(availableQty) || availableQty < 0) {
      setError('Please enter a valid available quantity');
      return;
    }
    if (isNaN(consumedQty) || consumedQty < 0) {
      setError('Please enter a valid consumed quantity');
      return;
    }


    if (availableQty + consumedQty > totalQty) {
      setError('Available + Consumed cannot be higher than Total quantity');
      return;
    }

    // Optional: Add consistency check? 
    // For now, trusting user input as requested.

    addToolMutation.mutate({
      tool_name: name,
      tool_size: size || null,
      tool_type: isConsumable ? 'Consumable' : 'Borrowable',
      total_quantity: totalQty,
      available_quantity: availableQty,
      trained: !trained,
      current_status: 'Available',
      consumed_quantity: consumedQty
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900">Add New Tool</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="text-sm text-red-600 bg-red-50 p-3 rounded-md">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tool Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., Hammer"
              autoFocus
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Size (Optional)
              </label>
              <input
                type="text"
                value={size}
                onChange={(e) => setSize(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., 16 oz"
              />
            </div>

            <div className="flex items-end pb-3">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="isConsumable"
                  checked={isConsumable}
                  onChange={(e) => setIsConsumable(e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="isConsumable" className="text-sm font-medium text-gray-700 cursor-pointer select-none">
                  Consumable (Check if not Borrowable)
                </label>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Total Qty
              </label>
              <input
                type="number"
                value={total}
                onChange={(e) => setTotal(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="0"
                required
                min="0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Available
              </label>
              <input
                type="number"
                value={available}
                onChange={(e) => setAvailable(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="0"
                required
                min="0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Consumed
              </label>
              <input
                type="number"
                value={consumed}
                onChange={(e) => setConsumed(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="0"
                required
                min="0"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="trained"
                checked={trained}
                onChange={(e) => setTrained(e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="trained" className="text-sm font-medium text-gray-700 cursor-pointer select-none">
                Requires Training?
              </label>
            </div>
          </div>

          <div className="pt-4 flex justify-end space-x-3">

            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              disabled={addToolMutation.isPending}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-blue-400"
              disabled={addToolMutation.isPending}
            >
              {addToolMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Adding...
                </>
              ) : (
                'Add Tool'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
