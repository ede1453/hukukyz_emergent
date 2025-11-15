import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Navbar = () => {
  const [balance, setBalance] = useState(null);
  const { user, token, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      fetchBalance();
      const interval = setInterval(fetchBalance, 30000);
      return () => clearInterval(interval);
    }
  }, [isAuthenticated, token]);

  const fetchBalance = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/credits/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setBalance(response.data.balance);
      }
    } catch (error) {
      console.error('Error fetching balance:', error);
    }
  };

  if (!isAuthenticated) return null;

  return (
    <nav className="bg-gray-800 border-b border-gray-700 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <span className="text-2xl">🏛️</span>
            <span className="text-xl font-bold text-white">HukukYZ</span>
          </Link>

          {/* Right side */}
          <div className="flex items-center gap-4">
            {/* Credit Balance */}
            <div 
              onClick={() => navigate('/credits')}
              className="flex items-center gap-2 bg-gray-900 rounded-lg px-3 py-2 border border-gray-600 cursor-pointer hover:border-blue-500 transition"
              title="Kredi Yönetimi"
            >
              <span className="text-yellow-400 text-lg">💳</span>
              <div className="text-left">
                <p className="text-xs text-gray-400">Credits</p>
                <p className="text-sm font-bold text-white">
                  {balance !== null ? balance.toFixed(2) : '---'}
                </p>
              </div>
            </div>

            {/* User Menu */}
            <div className="flex items-center gap-2">
              <Link
                to="/profile"
                className="flex items-center gap-2 text-gray-300 hover:text-white transition"
              >
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-sm font-bold text-white">
                  {user?.full_name?.charAt(0).toUpperCase()}
                </div>
                <span className="text-sm hidden md:block">{user?.full_name}</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
