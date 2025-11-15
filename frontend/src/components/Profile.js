import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import Navbar from './Navbar';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Profile = () => {
  const { user, logout, updateProfile, token } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [editing, setEditing] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  
  const navigate = useNavigate();

  const handleUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      await updateProfile(fullName);
      setMessage({ type: 'success', text: '✅ Profil başarıyla güncellendi' });
      setEditing(false);
    } catch (error) {
      setMessage({ type: 'error', text: '❌ Güncelleme başarısız oldu' });
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    
    if (newPassword !== confirmPassword) {
      setMessage({ type: 'error', text: '❌ Yeni şifreler eşleşmiyor' });
      return;
    }
    
    if (newPassword.length < 6) {
      setMessage({ type: 'error', text: '❌ Şifre en az 6 karakter olmalıdır' });
      return;
    }

    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      await axios.put(
        `${BACKEND_URL}/api/auth/change-password`,
        {
          current_password: currentPassword,
          new_password: newPassword
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      setMessage({ type: 'success', text: '✅ Şifre başarıyla değiştirildi' });
      setChangingPassword(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Şifre değiştirilemedi';
      setMessage({ type: 'error', text: `❌ ${errorMsg}` });
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-400 mb-4">Giriş yapmanız gerekiyor</p>
          <button
            onClick={() => navigate('/login')}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Giriş Yap
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-white">
              👤 Profil Ayarları
            </h1>
            <button
              onClick={() => navigate('/')}
              className="text-gray-400 hover:text-white transition"
            >
              ← Ana Sayfa
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
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

        {/* Profile Card */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 mb-6">
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <span>👤</span> Profil Bilgileri
          </h2>
          
          <div className="flex items-center gap-4 mb-8">
            <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-4xl font-bold text-white shadow-lg">
              {user.full_name.charAt(0).toUpperCase()}
            </div>
            <div>
              <h3 className="text-2xl font-bold text-white">{user.full_name}</h3>
              <p className="text-gray-400">{user.email}</p>
              {user.role && (
                <span className={`inline-block mt-2 px-3 py-1 rounded-full text-xs font-semibold ${
                  user.role === 'admin' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-green-600 text-white'
                }`}>
                  {user.role === 'admin' ? '👨‍💼 Admin' : '⚖️ Avukat'}
                </span>
              )}
            </div>
          </div>

          {/* Edit Form */}
          {editing ? (
            <form onSubmit={handleUpdate} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Ad Soyad
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                  className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
                >
                  {loading ? 'Kaydediliyor...' : 'Kaydet'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setEditing(false);
                    setFullName(user.full_name);
                  }}
                  className="px-6 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition"
                >
                  İptal
                </button>
              </div>
            </form>
          ) : (
            <div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div className="bg-gray-700 rounded-lg p-4">
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    📧 E-posta
                  </label>
                  <p className="text-lg text-white">{user.email}</p>
                </div>
                <div className="bg-gray-700 rounded-lg p-4">
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    👤 Ad Soyad
                  </label>
                  <p className="text-lg text-white">{user.full_name}</p>
                </div>
                {user.created_at && (
                  <div className="bg-gray-700 rounded-lg p-4">
                    <label className="block text-sm font-medium text-gray-400 mb-2">
                      📅 Kayıt Tarihi
                    </label>
                    <p className="text-lg text-white">
                      {new Date(user.created_at).toLocaleDateString('tr-TR', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })}
                    </p>
                  </div>
                )}
                <div className="bg-gray-700 rounded-lg p-4">
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    🔒 Hesap Durumu
                  </label>
                  <p className="text-lg text-green-400 font-semibold">✓ Aktif</p>
                </div>
              </div>

              <button
                onClick={() => setEditing(true)}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                ✏️ Profili Düzenle
              </button>
            </div>
          )}
        </div>

        {/* Password Change Card */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 mb-6">
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <span>🔐</span> Güvenlik Ayarları
          </h2>
          
          {changingPassword ? (
            <form onSubmit={handlePasswordChange} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Mevcut Şifre
                </label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                  className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Yeni Şifre
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={6}
                  className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Yeni Şifre (Tekrar)
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  minLength={6}
                  className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:outline-none focus:border-blue-500"
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
                >
                  {loading ? 'Değiştiriliyor...' : 'Şifreyi Değiştir'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setChangingPassword(false);
                    setCurrentPassword('');
                    setNewPassword('');
                    setConfirmPassword('');
                  }}
                  className="px-6 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition"
                >
                  İptal
                </button>
              </div>
            </form>
          ) : (
            <div>
              <p className="text-gray-400 mb-4">
                Hesabınızın güvenliği için düzenli olarak şifrenizi değiştirmenizi öneririz.
              </p>
              <button
                onClick={() => setChangingPassword(true)}
                className="px-6 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition"
              >
                🔑 Şifreyi Değiştir
              </button>
            </div>
          )}
        </div>

        {/* Credit History */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 mb-6">
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <span>💳</span> Kredi Geçmişi
          </h2>
          <CreditHistoryWidget />
        </div>

        {/* Logout Button */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-8">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <span>🚪</span> Oturum
          </h2>
          <p className="text-gray-400 mb-4">
            Hesabınızdan güvenli bir şekilde çıkış yapın.
          </p>
          <button
            onClick={handleLogout}
            className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition font-medium"
          >
            Çıkış Yap
          </button>
        </div>
      </div>
    </div>
  );
};

// Credit History Widget Component
const CreditHistoryWidget = () => {
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [historyRes, statsRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/credits/history?limit=10`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${BACKEND_URL}/api/credits/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      if (historyRes.data.success) {
        setHistory(historyRes.data.transactions);
      }
      if (statsRes.data.success) {
        setStats(statsRes.data.stats);
      }
    } catch (error) {
      console.error('Error fetching credit data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <p className="text-gray-400 text-center py-4">Yükleniyor...</p>;
  }

  return (
    <div>
      {/* Stats Summary */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-700 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-400 mb-1">Mevcut</p>
            <p className="text-xl font-bold text-white">{stats.current_balance.toFixed(2)}</p>
          </div>
          <div className="bg-gray-700 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-400 mb-1">Satın Alınan</p>
            <p className="text-xl font-bold text-green-400">{stats.total_purchased.toFixed(2)}</p>
          </div>
          <div className="bg-gray-700 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-400 mb-1">Harcanan</p>
            <p className="text-xl font-bold text-red-400">{stats.total_spent.toFixed(2)}</p>
          </div>
          <div className="bg-gray-700 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-400 mb-1">İşlem</p>
            <p className="text-xl font-bold text-blue-400">{stats.transaction_count}</p>
          </div>
        </div>
      )}

      {/* Recent Transactions */}
      {history.length === 0 ? (
        <p className="text-gray-400 text-center py-4">Henüz işlem bulunmuyor</p>
      ) : (
        <div className="space-y-2">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-sm font-semibold text-gray-300">Son 10 İşlem</h3>
            <a href="/credits" className="text-xs text-blue-400 hover:text-blue-300">
              Tümünü Gör →
            </a>
          </div>
          {history.map((transaction, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 bg-gray-700 rounded-lg hover:bg-gray-650 transition"
            >
              <div className="flex items-center gap-3">
                <span className={`text-2xl ${
                  transaction.type === 'credit' ? 'text-green-400' : 'text-red-400'
                }`}>
                  {transaction.type === 'credit' ? '➕' : '➖'}
                </span>
                <div>
                  <p className="text-sm text-white font-medium">{transaction.reason}</p>
                  <p className="text-xs text-gray-400">
                    {new Date(transaction.created_at).toLocaleString('tr-TR')}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className={`text-sm font-bold ${
                  transaction.amount > 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {transaction.amount > 0 ? '+' : ''}{transaction.amount.toFixed(4)}
                </p>
                <p className="text-xs text-gray-400">
                  Bakiye: {transaction.balance_after.toFixed(2)}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Profile;
