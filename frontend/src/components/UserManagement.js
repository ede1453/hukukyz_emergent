import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [confirmDialog, setConfirmDialog] = useState(null);
  const [actionLoading, setActionLoading] = useState(null);
  const [message, setMessage] = useState({ type: '', text: '' });
  const navigate = useNavigate();
  const { isAdmin } = useAuth();

  useEffect(() => {
    if (!isAdmin()) {
      navigate('/');
      return;
    }
    fetchUsers();
  }, [isAdmin, navigate]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${BACKEND_URL}/api/auth/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setUsers(response.data.users);
      }
    } catch (err) {
      console.error('Error fetching users:', err);
      setError(err.response?.data?.detail || 'Kullanıcılar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (userEmail, newRole) => {
    setActionLoading(userEmail);
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${BACKEND_URL}/api/auth/users/${userEmail}/role`,
        { role: newRole },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      setMessage({ type: 'success', text: `✅ Kullanıcı rolü '${newRole}' olarak güncellendi` });
      await fetchUsers();
    } catch (err) {
      console.error('Role update error:', err);
      const errorMsg = err.response?.data?.detail || 'Rol güncellenemedi';
      setMessage({ type: 'error', text: `❌ ${errorMsg}` });
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteUser = async (userEmail) => {
    setActionLoading(userEmail);
    try {
      const token = localStorage.getItem('token');
      await axios.delete(
        `${BACKEND_URL}/api/auth/users/${userEmail}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      setMessage({ type: 'success', text: '✅ Kullanıcı başarıyla silindi' });
      await fetchUsers();
      setConfirmDialog(null);
    } catch (err) {
      console.error('Delete error:', err);
      const errorMsg = err.response?.data?.detail || 'Kullanıcı silinemedi';
      setMessage({ type: 'error', text: `❌ ${errorMsg}` });
    } finally {
      setActionLoading(null);
    }
  };

  const handleResetPassword = async (userEmail) => {
    setActionLoading(userEmail);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${BACKEND_URL}/api/auth/users/${userEmail}/reset-password`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      const newPassword = response.data.default_password;
      setMessage({ 
        type: 'success', 
        text: `✅ Şifre sıfırlandı. Yeni şifre: ${newPassword}` 
      });
      setConfirmDialog(null);
    } catch (err) {
      console.error('Reset password error:', err);
      const errorMsg = err.response?.data?.detail || 'Şifre sıfırlanamadı';
      setMessage({ type: 'error', text: `❌ ${errorMsg}` });
    } finally {
      setActionLoading(null);
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

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">❌ {error}</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Ana Sayfaya Dön
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                👥 Kullanıcı Yönetimi
              </h1>
              <p className="text-gray-400">Kullanıcı rolleri ve yetkilendirme</p>
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

        {/* Info Box */}
        <div className="mb-6 bg-blue-900 bg-opacity-30 border border-blue-700 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <div className="text-xl">ℹ️</div>
            <div>
              <h4 className="font-semibold text-blue-300 mb-1">
                Roller ve Yetkiler
              </h4>
              <ul className="text-sm text-gray-300 space-y-1">
                <li>• <strong>Admin:</strong> Tüm özelliklere erişim (belge yükleme, Qdrant yönetimi, kullanıcı yönetimi)</li>
                <li>• <strong>Avukat:</strong> Sohbet, dashboard ve profil erişimi</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
            <p className="text-gray-400 text-sm mb-1">Toplam Kullanıcı</p>
            <p className="text-3xl font-bold text-white">{users.length}</p>
          </div>
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
            <p className="text-gray-400 text-sm mb-1">Admin Sayısı</p>
            <p className="text-3xl font-bold text-blue-400">
              {users.filter(u => u.role === 'admin').length}
            </p>
          </div>
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
            <p className="text-gray-400 text-sm mb-1">Avukat Sayısı</p>
            <p className="text-3xl font-bold text-green-400">
              {users.filter(u => u.role === 'avukat').length}
            </p>
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Kullanıcı
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Rol
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Kayıt Tarihi
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  İşlemler
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {users.map((user, index) => (
                <tr key={index} className="hover:bg-gray-750">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-lg font-bold text-white">
                        {user.full_name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-white">{user.full_name}</p>
                        <p className="text-xs text-gray-400">{user.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <select
                      value={user.role || 'avukat'}
                      onChange={(e) => handleRoleChange(user.email, e.target.value)}
                      disabled={actionLoading === user.email}
                      className="bg-gray-700 text-white text-sm rounded px-3 py-1 border border-gray-600 focus:border-blue-500 focus:outline-none disabled:opacity-50"
                    >
                      <option value="avukat">⚖️ Avukat</option>
                      <option value="admin">👨‍💼 Admin</option>
                    </select>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-400">
                    {user.created_at ? new Date(user.created_at).toLocaleDateString('tr-TR') : 'N/A'}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => setConfirmDialog({ type: 'reset', user })}
                        disabled={actionLoading === user.email}
                        className="px-3 py-1 bg-yellow-600 text-white text-xs rounded hover:bg-yellow-700 transition disabled:opacity-50"
                        title="Şifre Sıfırla"
                      >
                        🔑 Sıfırla
                      </button>
                      <button
                        onClick={() => setConfirmDialog({ type: 'delete', user })}
                        disabled={actionLoading === user.email}
                        className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 transition disabled:opacity-50"
                        title="Kullanıcıyı Sil"
                      >
                        🗑️ Sil
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {users.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-400">Henüz kullanıcı bulunmuyor</p>
          </div>
        )}
      </div>

      {/* Confirmation Dialog */}
      {confirmDialog && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setConfirmDialog(null)}
        >
          <div 
            className="bg-gray-800 rounded-lg p-6 max-w-md w-full border border-gray-700"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-xl font-bold text-white mb-4">
              {confirmDialog.type === 'delete' ? '⚠️ Kullanıcıyı Sil' : '🔑 Şifre Sıfırla'}
            </h3>
            <p className="text-gray-300 mb-6">
              {confirmDialog.type === 'delete' 
                ? `'${confirmDialog.user.full_name}' kullanıcısını silmek istediğinizden emin misiniz? Bu işlem geri alınamaz!`
                : `'${confirmDialog.user.full_name}' kullanıcısının şifresini sıfırlamak istediğinizden emin misiniz?`
              }
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setConfirmDialog(null)}
                className="flex-1 px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600 transition"
              >
                İptal
              </button>
              <button
                onClick={() => {
                  if (confirmDialog.type === 'delete') {
                    handleDeleteUser(confirmDialog.user.email);
                  } else {
                    handleResetPassword(confirmDialog.user.email);
                  }
                }}
                className={`flex-1 px-4 py-2 text-white rounded transition ${
                  confirmDialog.type === 'delete'
                    ? 'bg-red-600 hover:bg-red-700'
                    : 'bg-yellow-600 hover:bg-yellow-700'
                }`}
              >
                {confirmDialog.type === 'delete' ? 'Evet, Sil' : 'Evet, Sıfırla'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
