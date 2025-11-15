import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AdminDashboard = () => {
  const [platformStats, setPlatformStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { token, isAdmin } = useAuth();

  useEffect(() => {
    if (!isAdmin()) {
      navigate('/chat');
      return;
    }
    fetchData();
  }, [isAdmin, navigate]);

  const fetchData = async () => {
    try {
      const [statsRes, healthRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/analytics/admin/platform-stats`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${BACKEND_URL}/api/chat/health`)
      ]);
      
      setPlatformStats({
        ...statsRes.data.platform_stats,
        health: healthRes.data
      });
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6" style={{ height: '100vh', overflowY: 'auto' }}>
      <h1 className="text-3xl font-bold text-white mb-6">🏠 Admin Ana Sayfa</h1>
      
      {platformStats && (
        <div className="space-y-6">
          {/* System Health */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
            <h2 className="text-xl font-bold text-white mb-4">🟢 Sistem Durumu</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-700 rounded-lg p-4">
                <p className="text-sm text-gray-400">Backend</p>
                <p className="text-lg font-bold text-green-400">✓ Çalışıyor</p>
              </div>
              <div className="bg-gray-700 rounded-lg p-4">
                <p className="text-sm text-gray-400">MongoDB</p>
                <p className="text-lg font-bold text-green-400">
                  {platformStats.health?.database?.status === 'connected' ? '✓ Bağlı' : '✗ Bağlı Değil'}
                </p>
              </div>
              <div className="bg-gray-700 rounded-lg p-4">
                <p className="text-sm text-gray-400">Qdrant</p>
                <p className="text-lg font-bold text-green-400">
                  {platformStats.health?.qdrant?.status === 'connected' ? '✓ Bağlı' : '✗ Bağlı Değil'}
                </p>
              </div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-blue-600 to-blue-800 rounded-lg p-6">
              <p className="text-blue-200 text-sm mb-2">Toplam Kullanıcı</p>
              <p className="text-4xl font-bold text-white">{platformStats.users.total}</p>
            </div>
            
            <div className="bg-gradient-to-br from-green-600 to-green-800 rounded-lg p-6">
              <p className="text-green-200 text-sm mb-2">Bugün Aktif</p>
              <p className="text-4xl font-bold text-white">{platformStats.users.active_today}</p>
            </div>
            
            <div className="bg-gradient-to-br from-purple-600 to-purple-800 rounded-lg p-6">
              <p className="text-purple-200 text-sm mb-2">Toplam Sorgu</p>
              <p className="text-4xl font-bold text-white">{platformStats.queries.total}</p>
            </div>
            
            <div className="bg-gradient-to-br from-orange-600 to-orange-800 rounded-lg p-6">
              <p className="text-orange-200 text-sm mb-2">Bugün</p>
              <p className="text-4xl font-bold text-white">{platformStats.queries.today}</p>
            </div>
          </div>

          {/* Top Users */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
            <h2 className="text-xl font-bold text-white mb-4">🏆 En Aktif Kullanıcılar (Son 7 Gün)</h2>
            <div className="space-y-2">
              {platformStats.top_users.slice(0, 5).map((user, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl font-bold text-gray-500">#{idx + 1}</span>
                    <div>
                      <p className="text-sm font-medium text-white">{user.email}</p>
                      <p className="text-xs text-gray-400">{user.queries} sorgu</p>
                    </div>
                  </div>
                  <span className="text-sm text-blue-400 font-semibold">
                    {user.credits_used.toFixed(2)} kredi
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Popular Collections */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
            <h2 className="text-xl font-bold text-white mb-4">📚 Popüler Hukuk Dalları</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {platformStats.popular_collections.map((col, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                  <span className="text-sm font-medium text-white">{col.name}</span>
                  <span className="px-3 py-1 bg-blue-600 text-white text-xs rounded-full font-bold">
                    {col.count}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
