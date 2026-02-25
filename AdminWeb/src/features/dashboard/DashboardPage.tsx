import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/axios';
import { Loader2, Calendar } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export const DashboardPage = () => {
  const [period, setPeriod] = useState('1_month');

  const { data, isLoading, isError } = useQuery({
    queryKey: ['dashboard', period],
    queryFn: async () => {
      const { data } = await api.get('/analytics/dashboard', {
        params: { period }
      });
      return data;
    }
  });

  const periods = [
    { value: '1_month', label: 'Recent 1 Month' },
    { value: 'winter_2026', label: 'Winter 2026' },
    { value: 'fall_2025', label: 'Fall 2025' },
    { value: 'summer_2025', label: 'Summer 2025' },
    { value: 'winter_2025', label: 'Winter 2025' },
  ];

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (isError) {
    return <div className="p-4 text-red-600">Failed to load dashboard data.</div>;
  }

  const { live_stats, period_stats } = data || {};

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-black">Dashboard</h2>
        
        {/* Period Selector */}
        <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-gray-500" />
            <select 
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                className="bg-white border border-gray-300 text-gray-700 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5 outline-none"
            >
                {periods.map(p => (
                    <option key={p.value} value={p.value}>{p.label}</option>
                ))}
            </select>
        </div>
      </div>

      {/* Live Stats Grid (Always Current) */}
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Current Status</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Total Inventory</p>
          <p className="text-3xl font-bold text-gray-900">{live_stats?.total_tools ?? '-'}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Currently Borrowed</p>
          <p className="text-3xl font-bold text-blue-600">{live_stats?.current_borrowed ?? '-'}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Currently Overdue</p>
          <p className="text-3xl font-bold text-red-600">{live_stats?.current_overdue ?? '-'}</p>
        </div>
      </div>

      {/* Period Stats */}
      <div className="pt-4">
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
            Analytics ({periods.find(p => p.value === period)?.label})
        </h3>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Activity Summary */}
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Total Checkouts in Period</p>
                <p className="text-3xl font-bold text-gray-900 mb-2">{period_stats?.checkouts ?? 0}</p>
                <p className="text-sm text-gray-500">
                    From {new Date(period_stats?.start_date).toLocaleDateString()} to {new Date(period_stats?.end_date).toLocaleDateString()}
                </p>
            </div>

            {/* Top 10 Borrowed Tools (Chart) */}
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 min-h-[400px]">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Top Used Tools</h3>
              {period_stats?.top_tools && period_stats.top_tools.length > 0 ? (
                <div className="h-[300px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={period_stats.top_tools}
                      layout="vertical"
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                      <XAxis type="number" hide />
                      <YAxis 
                        dataKey="name" 
                        type="category" 
                        width={150} 
                        tick={{ fontSize: 12 }} 
                      />
                      <Tooltip 
                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        cursor={{ fill: '#f3f4f6' }}
                      />
                      <Bar 
                        dataKey="uses" 
                        fill="#3b82f6" 
                        radius={[0, 4, 4, 0]} 
                        barSize={20}
                        name="Usage Count"
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-full flex items-center justify-center text-gray-500 text-sm">
                  No usage data for this period.
                </div>
              )}
            </div>
        </div>
      </div>
    </div>
  );
};
