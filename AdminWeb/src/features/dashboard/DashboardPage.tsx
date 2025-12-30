import React from 'react';

// Mock Data for frontend display
const stats = [
  { label: 'Total Tools (Inventory)', value: '35 Items' },
  { label: 'Tools Borrowed', value: '7 Items' },
  { label: 'Tools Overdue', value: '1 Items' },
  { label: 'Return Rate (30 Days)', value: '91%' },
];

const topTools = [
  { name: 'Long Nose Pliers Small', uses: 42 },
  { name: 'Monkey Spanner 300', uses: 31 },
  { name: 'Tool 3', uses: 28 },
  { name: 'Tool 4', uses: 22 },
  { name: 'Tool 5', uses: 19 },
  { name: 'Tool 6', uses: 17 },
  { name: 'Tool 7', uses: 15 },
  { name: 'Tool 8', uses: 12 },
  { name: 'Tool 9', uses: 10 },
  { name: 'Tool 10', uses: 7 },
];

export const DashboardPage = () => {
  // Placeholder for data fetching
  // const { data: dashboardData, isLoading } = useQuery({ queryKey: ['dashboardStats'], queryFn: fetchDashboardStats });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-black">Staff Dashboard</h2>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">{stat.label}</p>
            <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top 10 Borrowed Tools */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Top 10 Borrowed Tools</h3>
          <div className="space-y-3">
            {topTools.map((tool, index) => (
              <div key={tool.name} className="flex justify-between items-center text-sm">
                <span className="text-gray-700">
                  {index + 1}. {tool.name}
                </span>
                <span className="font-semibold text-gray-900">{tool.uses} Uses</span>
              </div>
            ))}
          </div>
        </div>

        {/* Usage Over Time Chart Placeholder */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 flex flex-col">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Usage Over Time (Last 30 Days)</h3>
          <div className="flex-1 bg-gray-50 rounded-md flex items-center justify-center min-h-[300px]">
            <span className="text-gray-400 font-medium">[Usage Chart Placeholder]</span>
          </div>
        </div>
      </div>
    </div>
  );
};
