import React, { useState } from 'react';
import { Sun, Moon } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import Dashboard from '../features/dashboard/Dashboard';
import History from '../features/history/History'
// Placeholder components for other sections

const TasksComponent = ({ isDark }) => (
  <div className="h-full p-6">
    <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Tasks</h1>
    <p className="text-gray-600 dark:text-gray-400">Manage your tasks here</p>
  </div>
);

const SettingsComponent = ({ isDark }) => (
  <div className="h-full p-6">
    <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Settings</h1>
    <p className="text-gray-600 dark:text-gray-400">Configure your preferences here</p>
  </div>
);

// Main App Component
function Main() {

  const [isDark, setIsDark] = useState(false);
  const [activeItem, setActiveItem] = useState('Dashboard');

  const toggleTheme = () => {
    setIsDark(!isDark);
  };

  // Function to render the active component
  const renderActiveComponent = () => {
    switch(activeItem) {
      case 'Dashboard':
        return <Dashboard isDark={isDark} />;
      case 'History':
        return <History isDark={isDark} />;
      case 'Tasks':
        return <TasksComponent isDark={isDark} />;
      case 'Settings':
        return <SettingsComponent isDark={isDark} />;
      default:
        return <Dashboard isDark={isDark} />;
    }
  };

  return (
    <div className={`min-h-screen ${isDark ? 'bg-gray-900' : 'bg-white'} transition-colors duration-200`}>
      {/* Theme Toggle Button */}
      <div className="absolute top-4 right-4 z-10">
        <button
          onClick={toggleTheme}
          className={`p-2 rounded-lg transition-colors duration-200 ${
            isDark 
              ? 'bg-gray-700 hover:bg-gray-600 text-yellow-400' 
              : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
          }`}
        >
          {isDark ? <Sun size={20} /> : <Moon size={20} />}
        </button>
      </div>

      {/* Main Layout */}
      <div className="flex h-screen">
        {/* Sidebar */}
        <Sidebar 
          isDark={isDark} 
          activeItem={activeItem} 
          setActiveItem={setActiveItem} 
        />
        
        {/* Main Content - Now occupies full remaining area */}
        <div className={`flex-1 ${isDark ? 'text-white mt-5' : 'text-gray-900'} overflow-auto`}>
          {renderActiveComponent()}
        </div>
      </div>
    </div>
  );
}

export default Main;