import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Sidebar = ({ collapsed, setCollapsed }) => {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const isUserAdmin = isAdmin();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const userMenuItems = [
    { path: '/chat', icon: '💬', label: 'Sohbet', show: true },
    { path: '/history', icon: '📜', label: 'Geçmiş', show: true },
    { path: '/dashboard', icon: '📊', label: 'Dashboard', show: true },
    { path: '/credits', icon: '💳', label: 'Kredi', show: !isUserAdmin },
    { path: '/profile', icon: '👤', label: 'Profil', show: true },
  ];

  const adminMenuItems = [
    { path: '/admin/dashboard', icon: '🏠', label: 'Ana Sayfa', show: true },
    { path: '/chat', icon: '💬', label: 'Sohbet', show: true },
    { path: '/history', icon: '📜', label: 'Geçmiş', show: true },
    { path: '/admin/users', icon: '👥', label: 'Kullanıcılar', show: true },
    { path: '/admin/analytics', icon: '📈', label: 'Analitik', show: true },
    { path: '/admin/qdrant', icon: '🗄️', label: 'Qdrant', show: true },
    { path: '/upload', icon: '📤', label: 'PDF Yükle', show: true },
    { path: '/dashboard', icon: '📊', label: 'Popüler', show: true },
    { path: '/profile', icon: '👤', label: 'Profil', show: true },
  ];

  const menuItems = isUserAdmin ? adminMenuItems : userMenuItems;

  return (
    <div
      className={`bg-gray-800 border-r border-gray-700 flex flex-col transition-all duration-300 ${
        collapsed ? 'w-16' : 'w-64'
      }`}
      style={{ height: '100vh' }}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-700 flex items-center justify-between">
        {!collapsed && (
          <Link 
            to={isUserAdmin ? '/admin/dashboard' : '/chat'} 
            className="flex items-center gap-2 hover:opacity-80 transition"
          >
            <span className="text-2xl">🏛️</span>
            <span className="text-lg font-bold text-white">HukukYZ</span>
          </Link>
        )}
        {collapsed && (
          <Link 
            to={isUserAdmin ? '/admin/dashboard' : '/chat'}
            className="hover:opacity-80 transition"
          >
            <span className="text-2xl">🏛️</span>
          </Link>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 hover:bg-gray-700 rounded transition"
        >
          <span className="text-white">{collapsed ? '→' : '←'}</span>
        </button>
      </div>

      {/* User Info */}
      {!collapsed && (
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-lg font-bold text-white">
              {user?.full_name?.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {user?.full_name}
              </p>
              <p className="text-xs text-gray-400 truncate">{user?.email}</p>
              {isUserAdmin && (
                <span className="inline-block mt-1 px-2 py-0.5 bg-blue-900 text-blue-300 text-xs rounded-full">
                  👨‍💼 Admin
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Menu Items */}
      <nav className="flex-1 overflow-y-auto p-2">
        <ul className="space-y-1">
          {menuItems.filter(item => item.show).map((item) => (
            <li key={item.path}>
              <Link
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg transition ${
                  location.pathname === item.path
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-700'
                }`}
                title={collapsed ? item.label : ''}
              >
                <span className="text-xl">{item.icon}</span>
                {!collapsed && <span className="text-sm font-medium">{item.label}</span>}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      {/* Logout Button */}
      <div className="p-2 border-t border-gray-700">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2 text-red-400 hover:bg-gray-700 rounded-lg transition"
          title={collapsed ? 'Çıkış Yap' : ''}
        >
          <span className="text-xl">🚪</span>
          {!collapsed && <span className="text-sm font-medium">Çıkış Yap</span>}
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
