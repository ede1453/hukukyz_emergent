import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Dashboard = () => {
  const [mostCited, setMostCited] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMostCited();
  }, []);

  const fetchMostCited = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/citations/most-cited?limit=20`);
      if (response.data.success) {
        setMostCited(response.data.most_cited);
      }
    } catch (error) {
      console.error('Error:', error);
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
    <div style={{ height: '100vh', overflowY: 'auto' }} className="bg-gray-900 text-white p-6">
      <h1 className="text-3xl font-bold mb-6">📊 Popüler Maddeler</h1>
      
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
        <div className="space-y-3">
          {mostCited.map((item, idx) => (
            <div key={idx} className="flex items-center justify-between p-4 bg-gray-700 rounded-lg hover:bg-gray-600">
              <div className="flex items-center gap-4">
                <span className="text-2xl font-bold text-gray-500">#{idx + 1}</span>
                <div>
                  <p className="font-semibold text-lg">{item.reference}</p>
                  <p className="text-sm text-gray-400">{item.count} kez alıntılandı</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
