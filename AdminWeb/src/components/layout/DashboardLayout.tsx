import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { LayoutDashboard, Package, ArrowRightLeft, PenTool, FileBarChart } from 'lucide-react';
import clsx from 'clsx';

export const DashboardLayout = () => {
  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Inventory', path: '/inventory', icon: Package },
    { name: 'Transactions', path: '/transactions', icon: ArrowRightLeft },
    { name: 'Manual Transaction', path: '/manual-transaction', icon: PenTool },
    { name: 'Reports', path: '/reports', icon: FileBarChart },
  ];

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-[#0f172a] text-white flex flex-col flex-shrink-0">
        <div className="p-6">
          <h1 className="text-xl font-bold tracking-wide">TOOL-E Admin</h1>
        </div>

        <nav className="flex-1 px-4 space-y-2 mt-4">
          {navItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.path}
              className={({ isActive }) =>
                clsx(
                  'flex items-center px-4 py-3 text-sm font-medium rounded-md transition-colors',
                  isActive
                    ? 'bg-gray-800 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                )
              }
            >
              {/* Icon placeholder if needed, though screenshot doesn't explicitly show icons, standard admin panels usually have them. 
                  I'll hide them for now to match the screenshot exactly if it's text-only, 
                  but keeping the structure ready. The screenshot shows text only. */}
              {/* <item.icon className="w-5 h-5 mr-3" /> */}
              {item.name}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
