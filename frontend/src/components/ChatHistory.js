import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Navbar from './Navbar';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ChatHistory = () => {
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { token, isAuthenticated } = useAuth();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    fetchSessions();
  }, [isAuthenticated, navigate]);

  const fetchSessions = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/chat/sessions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setSessions(response.data.sessions);
      }
    } catch (error) {
      console.error('Error fetching sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async (sessionId) => {
    try {
      const response = await axios.get(
        `${BACKEND_URL}/api/chat/history/${sessionId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.data.success) {
        setHistory(response.data.history);
        setSelectedSession(sessionId);
      }
    } catch (error) {
      console.error('Error fetching history:', error);
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
    <div className="min-h-screen bg-gray-900 text-white">
      <Navbar />
      
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">💬 Konuşma Geçmişi</h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Sessions List */}
          <div className="lg:col-span-1">
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
              <h2 className="text-lg font-bold mb-4">Oturumlar</h2>
              
              {sessions.length === 0 ? (
                <p className="text-gray-400 text-center py-8">Henüz konuşma bulunmuyor</p>
              ) : (
                <div className="space-y-2">
                  {sessions.map((session) => (
                    <div
                      key={session.session_id}
                      onClick={() => fetchHistory(session.session_id)}
                      className={`p-3 rounded-lg cursor-pointer transition ${
                        selectedSession === session.session_id
                          ? 'bg-blue-600'
                          : 'bg-gray-700 hover:bg-gray-600'
                      }`}
                    >
                      <p className="text-sm font-medium line-clamp-2">
                        {session.last_query}
                      </p>
                      <div className="flex justify-between items-center mt-2 text-xs text-gray-400">
                        <span>{session.message_count} mesaj</span>
                        <span>
                          {new Date(session.last_timestamp).toLocaleDateString('tr-TR')}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          
          {/* Chat History */}
          <div className="lg:col-span-2">
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
              {!selectedSession ? (
                <div className="text-center py-12 text-gray-400">
                  Görüntülemek için bir oturum seçin
                </div>
              ) : (
                <div className="space-y-4">
                  {history.map((msg, idx) => (
                    <div key={idx} className="border-b border-gray-700 pb-4 last:border-0">
                      <div className="mb-2">
                        <span className="text-blue-400 font-semibold">Soru:</span>
                        <p className="mt-1 text-gray-200">{msg.query}</p>
                      </div>
                      
                      <div className="mt-3">
                        <span className="text-green-400 font-semibold">Cevap:</span>
                        <p className="mt-1 text-gray-300 whitespace-pre-wrap">{msg.answer}</p>
                      </div>
                      
                      <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                        <span>⏱ {msg.response_time?.toFixed(2)}s</span>
                        {msg.credits_used > 0 && (
                          <span>💳 {msg.credits_used.toFixed(4)} kredi</span>
                        )}
                        <span>📅 {new Date(msg.timestamp).toLocaleString('tr-TR')}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatHistory;
