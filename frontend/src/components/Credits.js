import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Navbar from './Navbar';

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

      if (balanceRes.data.success) {
        setBalance(balanceRes.data.balance);
      }
      if (statsRes.data.success) {
        setStats(statsRes.data.stats);
      }
      if (historyRes.data.success) {
        setHistory(historyRes.data.transactions);
      }
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
        {
          amount: purchaseAmount,
          payment_method: 'manual'
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
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
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Navbar />
      
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                💳 Kredi Yönetimi
              </h1>
              <p className="text-gray-400">Kredi bakiyenizi ve işlem geçmişinizi görüntüleyin</p>
            </div>
            <button
              onClick={() => navigate('/')}
              className="text-gray-400 hover:text-white transition"
            >
              ← Ana Sayfa
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Message */}
        {message.text && (
          <div className={`mb-6 p-4 rounded-lg border ${
            message.type === 'success' 
              ? 'bg-green-900 bg-opacity-30 border-green-700 text-green-300'
              : 'bg-red-900 bg-opacity-30 border-red-700 text-red-300'
          }`}>
            {message.text}
          </div>
        )}

        {/* Current Balance */}
        <div className="mb-6 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-8 text-center">
          <p className="text-blue-200 text-sm mb-2">Mevcut Bakiye</p>
          <p className="text-5xl font-bold text-white mb-4">{balance.toFixed(2)}</p>
          <p className="text-blue-200 text-sm">Kredi</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Purchase Credits */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <span>💰</span> Kredi Satın Al
            </h2>
            <p className="text-gray-400 text-sm mb-4">
              Kredi satın alarak platformu kullanmaya devam edin. Her chat sorgusu token kullanımına göre kredi tüketir.
            </p>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Kredi Miktarı
              </label>
              <input
                type="number"
                value={purchaseAmount}
                onChange={(e) => setPurchaseAmount(parseFloat(e.target.value) || 0)}
                min="1"
                step="1"
                className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:outline-none focus:border-blue-500"
              />
            </div>

            <div className="grid grid-cols-3 gap-2 mb-4">
              {[10, 50, 100].map(amount => (
                <button
                  key={amount}
                  onClick={() => setPurchaseAmount(amount)}
                  className="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600 transition text-sm"
                >
                  {amount} Kredi
                </button>
              ))}
            </div>

            <div className="mb-4 p-3 bg-gray-700 rounded-lg">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-400">Miktar:</span>
                <span className="text-white font-semibold">{purchaseAmount} Kredi</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Tutar:</span>
                <span className="text-white font-semibold">${(purchaseAmount * 0.01).toFixed(2)}</span>
              </div>
            </div>

            <button
              onClick={handlePurchase}
              className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
            >
              💳 Satın Al
            </button>

            <p className="text-xs text-gray-500 mt-3 text-center">
              * Demo amaçlı, gerçek ödeme alınmamaktadır
            </p>
          </div>

          {/* Stats */}
          {stats && (
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span>📊</span> İstatistikler
              </h2>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
                  <div>
                    <p className="text-gray-400 text-sm">Mevcut Bakiye</p>
                    <p className="text-2xl font-bold text-white">{stats.current_balance.toFixed(2)}</p>
                  </div>
                  <span className="text-3xl">💳</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
                  <div>
                    <p className="text-gray-400 text-sm">Toplam Satın Alınan</p>
                    <p className="text-2xl font-bold text-green-400">{stats.total_purchased.toFixed(2)}</p>
                  </div>
                  <span className="text-3xl">💰</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
                  <div>
                    <p className="text-gray-400 text-sm">Toplam Harcanan</p>
                    <p className="text-2xl font-bold text-red-400">{stats.total_spent.toFixed(2)}</p>
                  </div>
                  <span className="text-3xl">📉</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
                  <div>
                    <p className="text-gray-400 text-sm">Toplam İşlem</p>
                    <p className="text-2xl font-bold text-blue-400">{stats.transaction_count}</p>
                  </div>
                  <span className="text-3xl">📝</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Transaction History */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <span>📜</span> İşlem Geçmişi
          </h2>

          {history.length === 0 ? (
            <p className="text-gray-400 text-center py-8">Henüz işlem bulunmuyor</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Tarih</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Tip</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Açıklama</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">Miktar</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">Bakiye</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {history.map((transaction, index) => (
                    <tr key={index} className="hover:bg-gray-750">
                      <td className="px-4 py-3 text-sm text-gray-400">
                        {new Date(transaction.created_at).toLocaleString('tr-TR')}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          transaction.type === 'credit'
                            ? 'bg-green-900 text-green-300'
                            : 'bg-red-900 text-red-300'
                        }`}>
                          {transaction.type === 'credit' ? '➕ Kredi' : '➖ Kullanım'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-300">
                        {transaction.reason}
                      </td>
                      <td className={`px-4 py-3 text-sm text-right font-semibold ${
                        transaction.amount > 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {transaction.amount > 0 ? '+' : ''}{transaction.amount.toFixed(4)}
                      </td>
                      <td className="px-4 py-3 text-sm text-right text-white font-semibold">
                        {transaction.balance_after.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Credits;
