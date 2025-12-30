import React, { useState } from 'react';

export const ManualTransactionPage = () => {
  const [transactionType, setTransactionType] = useState<'checkout' | 'return'>('checkout');
  const [ucid, setUcid] = useState('');
  const [selectedTool, setSelectedTool] = useState('');
  const [returnDate, setReturnDate] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Transaction Submitted:', {
      transactionType,
      ucid,
      selectedTool,
      returnDate
    });
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-black">Manual Transaction (Staff Fallback)</h2>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 max-w-2xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          
          {/* Transaction Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Transaction Type
            </label>
            <div className="flex space-x-6">
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  name="type"
                  value="checkout"
                  checked={transactionType === 'checkout'}
                  onChange={() => setTransactionType('checkout')}
                  className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-900">Checkout</span>
              </label>
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  name="type"
                  value="return"
                  checked={transactionType === 'return'}
                  onChange={() => setTransactionType('return')}
                  className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-900">Return</span>
              </label>
            </div>
          </div>

          {/* Student UCID */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Student UCID
            </label>
            <input
              type="text"
              placeholder="e.g., 30012345"
              value={ucid}
              onChange={(e) => setUcid(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400"
            />
          </div>

          {/* Tool Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tool
            </label>
            <select
              value={selectedTool}
              onChange={(e) => setSelectedTool(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
            >
              <option value="" disabled>Select a tool...</option>
              <option value="hammer">Hammer</option>
              <option value="screwdriver">Screwdriver</option>
              <option value="pliers">Pliers</option>
              <option value="drill">Power Drill</option>
            </select>
          </div>

          {/* Return Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Return Date
            </label>
            <input
              type="date"
              value={returnDate}
              onChange={(e) => setReturnDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-500"
            />
          </div>

          {/* Submit Button */}
          <div className="pt-4 flex justify-end">
            <button
              type="submit"
              className="px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors"
            >
              Submit Transaction
            </button>
          </div>

        </form>
      </div>
    </div>
  );
};
