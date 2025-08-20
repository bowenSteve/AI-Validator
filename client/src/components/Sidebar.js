import React from 'react';
import { LayoutDashboard, History, CheckSquare, Settings } from 'lucide-react';

const Sidebar = ({ isDark, activeItem, setActiveItem }) => {
  const menuItems = [
    { icon: LayoutDashboard, label: 'Dashboard' },
    { icon: History, label: 'History' },
    { icon: CheckSquare, label: 'Tasks' },
    { icon: Settings, label: 'Settings' }
  ];

  return (
    <div className={`w-64 h-screen ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-200'} border-r transition-colors duration-200`}>
      {/* Logo */}
      <div className="p-6">
        <div className="flex items-center space-x-2">
          <div className={`w-8 h-8 ${isDark ? 'bg-cyan-400' : 'bg-blue-500'} rounded flex items-center justify-center`}>
            <span className="text-white font-bold text-lg">MV</span>
          </div>
          <span className={`font-semibold text-lg ${isDark ? 'text-white' : 'text-gray-900'}`}>
            Middesk Validator
          </span>
        </div>
      </div>

      {/* Menu Items */}
      <nav className="px-4 space-y-1">
        {menuItems.map((item, index) => (
          <div
            key={index}
            onClick={() => setActiveItem(item.label)}
            className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg cursor-pointer transition-colors duration-150 ${
              activeItem === item.label
                ? isDark 
                  ? 'bg-cyan-600 text-white' 
                  : 'bg-blue-100 text-blue-700'
                : isDark 
                  ? 'text-gray-300 hover:bg-gray-700 hover:text-white' 
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
            }`}
          >
            <item.icon size={18} />
            <span className="text-sm font-medium">{item.label}</span>
          </div>
        ))}
      </nav>
    </div>
  );
};

export default Sidebar;