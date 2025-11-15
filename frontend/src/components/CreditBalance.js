import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const CreditBalance = ({ onBuyClick }) => {
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(true);
  const { token, isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      fetchBalance();
      // Refresh balance every 30 seconds
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
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated || loading) return null;

  return (
    <div className="flex items-center gap-2 bg-gray-800 rounded-lg px-4 py-2 border border-gray-700">
      <div className="flex items-center gap-2">
        <span className="text-yellow-400 text-lg">💳</span>
        <div className="text-left">
          <p className="text-xs text-gray-400">Credits</p>
          <p className="text-sm font-bold text-white">
            {balance !== null ? balance.toFixed(2) : '---'}
          </p>
        </div>
      </div>
      <button
        onClick={onBuyClick}
        className="ml-2 px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition"
        title="Kredi Yükle"
      >
        + Buy
      </button>
    </div>
  );
};

export default CreditBalance;
