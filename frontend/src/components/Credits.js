import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Credits = () => {
  const [balance, setBalance] = useState(0);
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [purchaseAmount, setPurchaseAmount] = useState(10);
  const [message, setMessage] = useState({ type: '', text: '' });
  const navigate = useNavigate();
  const { token, isAuthenticated } = useAuth();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    fetchData();
  }, [isAuthenticated, navigate]);

  const fetchData = async () => {
    try {
      const [balanceRes, statsRes, historyRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/credits/balance`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${BACKEND_URL}/api/credits/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${BACKEND_URL}/api/credits/history?limit=20`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      if (balanceRes.data.success) setBalance(balanceRes.data.balance);
      if (statsRes.data.success) setStats(statsRes.data.stats);
      if (historyRes.data.success) setHistory(historyRes.data.transactions);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePurchase = async () => {
    if (purchaseAmount < 1) {
      setMessage({ type: 'error', text: 'Minimum 1 kredi satın alabilirsiniz' });
      return;
    }

    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/credits/purchase`,
        { amount: purchaseAmount, payment_method: 'manual' },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.data.success) {
        setMessage({ type: 'success', text: response.data.message });
        await fetchData();
        setPurchaseAmount(10);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Kredi satın alma başarısız';
      setMessage({ type: 'error', text: errorMsg });
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
    <div style={{ height: '100vh', overflowY: 'auto' }} className="bg-gray-900 text-white p-6">
      <h1 className="text-3xl font-bold mb-6">💳 Kredi Yönetimi</h1>
      
      {message.text && (
        <div className={`mb-6 p-4 rounded-lg border ${
          message.type === 'success' 
            ? 'bg-green-900 bg-opacity-30 border-green-700 text-green-300'
            : 'bg-red-900 bg-opacity-30 border-red-700 text-red-300'
        }`}>
          {message.text}
        </div>
      )}

      <div className="mb-6 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-8 text-center">
        <p className="text-blue-200 text-sm mb-2">Mevcut Bakiye</p>
        <p className="text-5xl font-bold text-white mb-4">{balance.toFixed(2)}</p>
        <p className="text-blue-200 text-sm">Kredi</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <h2 className="text-xl font-bold mb-4">💰 Kredi Satın Al</h2>
          <input
            type="number"
            value={purchaseAmount}
            onChange={(e) => setPurchaseAmount(parseFloat(e.target.value) || 0)}
            min="1"
            className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg mb-4"
          />
          <div className="grid grid-cols-3 gap-2 mb-4">
            {[10, 50, 100].map(amount => (
              <button
                key={amount}
                onClick={() => setPurchaseAmount(amount)}
                className="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600"
              >
                {amount}
              </button>
            ))}
          </div>
          <button
            onClick={handlePurchase}
            className="w-full px-6 py-3 bg-blue-600 rounded-lg hover:bg-blue-700"
          >
            Satın Al
          </button>
        </div>

        {stats && (
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
            <h2 className="text-xl font-bold mb-4">📊 İstatistikler</h2>
            <div className="space-y-4">
              <div className="p-4 bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-400">Toplam Satın Alınan</p>
                <p className="text-2xl font-bold text-green-400">{stats.total_purchased.toFixed(2)}</p>
              </div>
              <div className="p-4 bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-400">Toplam Harcanan</p>
                <p className="text-2xl font-bold text-red-400">{stats.total_spent.toFixed(2)}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
        <h2 className="text-xl font-bold mb-4">📜 İşlem Geçmişi</h2>
        {history.length === 0 ? (
          <p className="text-gray-400 text-center py-8">Henüz işlem bulunmuyor</p>
        ) : (
          <div className="space-y-2">
            {history.map((t, i) => (
              <div key={i} className="flex justify-between p-3 bg-gray-700 rounded">
                <div>
                  <p className="text-sm font-medium">{t.reason}</p>
                  <p className="text-xs text-gray-400">
                    {new Date(t.created_at).toLocaleString('tr-TR')}
                  </p>
                </div>
                <p className={`font-bold ${
                  t.amount > 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {t.amount > 0 ? '+' : ''}{t.amount.toFixed(4)}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Credits;
