import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Navbar from './Navbar';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Analytics = () => {
  const [platformStats, setPlatformStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { token, isAdmin } = useAuth();

  useEffect(() => {
    if (!isAdmin()) {
      navigate('/');
      return;
    }
    fetchPlatformStats();
  }, [isAdmin, navigate]);

  const fetchPlatformStats = async () => {
    try {
      const response = await axios.get(
        `${BACKEND_URL}/api/analytics/admin/platform-stats`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.data.success) {
        setPlatformStats(response.data.platform_stats);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div style={{ height: '100vh', overflowY: 'auto' }} className="bg-gray-900 text-white p-6">
      <h1 className="text-3xl font-bold mb-6">📊 Platform Analitikleri</h1>
      
      <div>
        {platformStats && (
          <div className="space-y-6">
            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
                <p className="text-gray-400 text-sm">Toplam Kullanıcı</p>
                <p className="text-3xl font-bold text-white mt-2">
                  {platformStats.users.total}
                </p>
              </div>
              
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
                <p className="text-gray-400 text-sm">Bugün Aktif</p>
                <p className="text-3xl font-bold text-green-400 mt-2">
                  {platformStats.users.active_today}
                </p>
              </div>
              
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
                <p className="text-gray-400 text-sm">Toplam Sorgu</p>
                <p className="text-3xl font-bold text-blue-400 mt-2">
                  {platformStats.queries.total}
                </p>
              </div>
              
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
                <p className="text-gray-400 text-sm">Ort. Yanıt Süresi</p>
                <p className="text-3xl font-bold text-purple-400 mt-2">
                  {platformStats.performance.avg_response_time.toFixed(2)}s
                </p>
              </div>
            </div>
            
            {/* Top Users */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
              <h2 className="text-xl font-bold mb-4">🏆 En Aktif Kullanıcılar</h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-700">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs">Kullanıcı</th>
                      <th className="px-4 py-2 text-right text-xs">Sorgu</th>
                      <th className="px-4 py-2 text-right text-xs">Kredi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {platformStats.top_users.map((user, idx) => (
                      <tr key={idx}>
                        <td className="px-4 py-2 text-sm">{user.email}</td>
                        <td className="px-4 py-2 text-sm text-right">{user.queries}</td>
                        <td className="px-4 py-2 text-sm text-right">
                          {user.credits_used.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            
            {/* Popular Collections */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
              <h2 className="text-xl font-bold mb-4">📚 Popüler Koleksiyonlar</h2>
              <div className="space-y-2">
                {platformStats.popular_collections.map((col, idx) => (
                  <div key={idx} className="flex justify-between items-center p-3 bg-gray-700 rounded">
                    <span className="font-medium">{col.name}</span>
                    <span className="text-blue-400 font-bold">{col.count} sorgu</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Analytics;
