import React, { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../lib/axios';

const deriveStatus = (tx: any) => {
  if (tx.return_timestamp) return 'Returned';
  if (tx.desired_return_date) {
    const due = new Date(tx.desired_return_date);
    if (!isNaN(due.getTime()) && Date.now() > due.getTime()) return 'Overdue';
  }
  return 'Borrowed';
};

const StatusBadge = ({ status }: { status: string }) => {
  const styles: Record<string, string> = {
    Borrowed: 'bg-blue-100 text-blue-700',
    Consumed: 'bg-gray-100 text-gray-700',
    Returned: 'bg-green-100 text-green-700',
    Overdue: 'bg-red-100 text-red-700',
  };

  return (
    <span
      className={`px-3 py-1 rounded-full text-xs font-semibold ${
        styles[status] || 'bg-gray-100 text-gray-700'
      }`}
    >
      {status}
    </span>
  );
};

export const ManualTransactionPage = () => {
  const [activeTab, setActiveTab] = useState<'checkout' | 'return'>('checkout');
  const [userId, setUserId] = useState('');
  const [selectedToolId, setSelectedToolId] = useState('');
  const [purpose, setPurpose] = useState('');
  const [desiredReturnDate, setDesiredReturnDate] = useState('');

  const [returnUserId, setReturnUserId] = useState('');
  const [lookupUserId, setLookupUserId] = useState('');
  const [selectedTransactionId, setSelectedTransactionId] = useState<number | null>(null);
  const [returnPurpose, setReturnPurpose] = useState('');
  const [returnWeight, setReturnWeight] = useState(0);
  const [returnClassificationCorrect, setReturnClassificationCorrect] = useState<boolean | null>(null);

  const queryClient = useQueryClient();

  const { data: tools = [] } = useQuery<{ id: number; name: string }[]>({
    queryKey: ['tools'],
    queryFn: async () => {
      const { data } = await api.get('/tools');
      return data;
    },
  });

  const checkoutMutation = useMutation({
    mutationFn: async () => {
      await api.post('/transactions', {
        user_id: userId ? Number(userId) : null,
        tool_id: selectedToolId ? Number(selectedToolId) : null,
        desired_return_date: desiredReturnDate || null,
        purpose: purpose || null,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      setUserId('');
      setSelectedToolId('');
      setPurpose('');
      setDesiredReturnDate('');
    },
  });

  const { data: userTransactions = [], isFetching: isFetchingReturns, isError, error } = useQuery<any[]>({
    queryKey: ['transactions', lookupUserId],
    queryFn: async () => {
      const parsedId = parseInt(lookupUserId, 10);
      if (isNaN(parsedId)) throw new Error('Invalid User ID');
      
      const { data } = await api.get('/transactions', {
        params: { user_id: parsedId, limit: 50 },
      });
      return data.items || [];
    },
    enabled: Boolean(lookupUserId),
    retry: false
  });

  const selectedTransaction = useMemo(() => {
    return userTransactions.find((tx) => tx.transaction_id === selectedTransactionId) || null;
  }, [userTransactions, selectedTransactionId]);

  const returnMutation = useMutation({
    mutationFn: async () => {
      if (!selectedTransactionId) return;
      await api.put(`/transactions/${selectedTransactionId}`, {
        return_timestamp: new Date().toISOString(),
        purpose: returnPurpose || selectedTransaction?.purpose || null,
        weight: returnWeight,
        classification_correct: returnClassificationCorrect,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions', lookupUserId] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      setSelectedTransactionId(null);
      setReturnPurpose('');
      setReturnWeight(0);
      setReturnClassificationCorrect(null);
    },
  });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-black">Manual Transaction (Staff Fallback)</h2>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 max-w-6xl mx-auto">
        <div className="flex gap-4 mb-6">
          <button
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              activeTab === 'checkout' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
            }`}
            onClick={() => setActiveTab('checkout')}
          >
            Checkout
          </button>
          <button
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              activeTab === 'return' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
            }`}
            onClick={() => setActiveTab('return')}
          >
            Return
          </button>
        </div>

        {activeTab === 'checkout' ? (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              checkoutMutation.mutate();
            }}
            className="space-y-4"
          >
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">User ID</label>
              <input
                type="text"
                placeholder="e.g., 101"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tool</label>
              <select
                value={selectedToolId}
                onChange={(e) => setSelectedToolId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md bg-white"
              >
                <option value="">Select a tool...</option>
                {tools.map((tool) => (
                  <option key={tool.id} value={tool.id}>
                    {tool.name} (#{tool.id})
                  </option>
                ))}
              </select>
            </div>


            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Desired Return Date</label>
              <input
                type="date"
                value={desiredReturnDate}
                onChange={(e) => setDesiredReturnDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Purpose</label>
              <input
                type="text"
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="submit"
                disabled={checkoutMutation.isPending}
                className="px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:bg-gray-400"
              >
                {checkoutMutation.isPending ? 'Saving...' : 'Create Transaction'}
              </button>
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">User ID</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Search user ID"
                  value={returnUserId}
                  onChange={(e) => setReturnUserId(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      setLookupUserId(returnUserId);
                    }
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
                <button
                  type="button"
                  onClick={() => setLookupUserId(returnUserId)}
                  className="px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700"
                >
                  Lookup
                </button>
              </div>
            </div>

            <div className="border rounded-md overflow-hidden bg-white shadow-sm min-h-[400px]">
              <div className="px-4 py-3 text-sm font-medium bg-gray-50 border-b border-gray-200 flex justify-between items-center">
                <span>Select a Transaction to Return</span>
                {lookupUserId && <span className="text-xs text-gray-500 font-normal">Showing results for User ID: {lookupUserId}</span>}
              </div>
              
              {isFetchingReturns ? (
                <div className="p-10 text-center text-sm text-gray-500">Loading transactions...</div>
              ) : isError ? (
                 <div className="p-10 text-center text-sm text-red-500">
                  {error instanceof Error && error.message === 'Invalid User ID' 
                    ? 'Please enter a valid numeric User ID.' 
                    : 'Failed to load transactions. Check connection or User ID.'}
                 </div>
              ) : userTransactions.length === 0 ? (
                <div className="p-10 text-center text-sm text-gray-500">
                  {lookupUserId ? 'No transactions found for this user.' : 'Use the lookup box to search for a user.'}
                </div>
              ) : (
                <div className="overflow-x-auto max-h-[600px]">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-gray-50 text-gray-500 font-medium border-b border-gray-100 sticky top-0 z-10 shadow-sm">
                      <tr>
                        <th className="px-4 py-3 whitespace-nowrap">ID</th>
                        <th className="px-4 py-3 whitespace-nowrap">User</th>
                        <th className="px-4 py-3 whitespace-nowrap">Tool</th>
                        <th className="px-4 py-3 whitespace-nowrap">Date Out</th>
                        <th className="px-4 py-3 whitespace-nowrap">Purpose</th>
                        <th className="px-4 py-3 whitespace-nowrap">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {userTransactions.map((tx) => {
                        const toolName = tools.find((t) => t.id === tx.tool_id)?.name || 'Unknown';
                        const status = deriveStatus(tx);
                        const isSelected = selectedTransactionId === tx.transaction_id;
                        
                        return (
                          <tr 
                            key={tx.transaction_id}
                            onClick={() => {
                              setSelectedTransactionId(tx.transaction_id);
                              setReturnPurpose(tx.purpose || '');
                              setReturnWeight(tx.weight || 0);
                              setReturnClassificationCorrect(
                                tx.classification_correct === null ? null : Boolean(tx.classification_correct)
                              );
                            }}
                            className={`cursor-pointer transition-colors ${
                              isSelected 
                                ? 'bg-blue-50 hover:bg-blue-100 ring-1 ring-inset ring-blue-200' 
                                : 'hover:bg-gray-50'
                            }`}
                          >
                            <td className="px-4 py-3 font-medium text-gray-900">#{tx.transaction_id}</td>
                            <td className="px-4 py-3 text-gray-900">{tx.user_id}</td>
                            <td className="px-4 py-3 text-gray-600">
                                <div className="font-medium text-gray-900">{toolName}</div>
                                <div className="text-xs text-gray-400">ID: {tx.tool_id}</div>
                            </td>
                            <td className="px-4 py-3 text-gray-600">
                              {new Date(tx.checkout_timestamp).toLocaleDateString()}
                              <div className="text-xs text-gray-400">
                                {new Date(tx.checkout_timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                              </div>
                            </td>
                             <td className="px-4 py-3 text-gray-600 max-w-[150px] truncate" title={tx.purpose || ''}>
                              {tx.purpose || '-'}
                            </td>
                            <td className="px-4 py-3">
                              <StatusBadge status={status} />
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {selectedTransaction && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  returnMutation.mutate();
                }}
                className="space-y-4"
              >
                <div className="text-sm text-gray-600">
                  Updating Transaction #{selectedTransaction.transaction_id}
                </div>


                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Purpose</label>
                  <input
                    type="text"
                    value={returnPurpose}
                    onChange={(e) => setReturnPurpose(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Weight</label>
                  <input
                    type="number"
                    value={returnWeight}
                    onChange={(e) => setReturnWeight(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Classification Correct</label>
                  <select
                    value={returnClassificationCorrect === null ? '' : returnClassificationCorrect ? 'true' : 'false'}
                    onChange={(e) => {
                      const value = e.target.value;
                      setReturnClassificationCorrect(value === '' ? null : value === 'true');
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-white"
                  >
                    <option value="">Not set</option>
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                  </select>
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    type="submit"
                    disabled={returnMutation.isPending}
                    className="px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:bg-gray-400"
                  >
                    {returnMutation.isPending ? 'Updating...' : 'Update Transaction'}
                  </button>
                </div>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
