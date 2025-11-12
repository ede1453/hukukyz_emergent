import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Chat = () => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Merhaba! Ben HukukYZ, Türk hukuku konusunda size yardımcı olabilirim. Sorularınızı yazabilirsiniz.',
      confidence: 1.0
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/chat/query`,
        {
          query: userMessage,
          session_id: 'web-session-' + Date.now()
        },
        { timeout: 120000 }
      );

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.data.answer,
        confidence: response.data.confidence,
        citations: response.data.citations,
        metadata: response.data.metadata
      }]);
    } catch (error) {
      console.error('Query error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin. Hata: ' + (error.response?.data?.detail || error.message),
        confidence: 0.0
      }]);
    } finally {
      setLoading(false);
    }
  };

  const exampleQueries = [
    'Anonim şirket nasıl kurulur?',
    'Limited şirket ve anonim şirket farkı nedir?',
    'TTK 11. madde nedir?',
    'Sözleşme nasıl kurulur?'
  ];

  return (
    <div className="flex flex-col h-screen bg-gray-900">
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold text-white">🏛️ HukukYZ</h1>
          <p className="text-sm text-gray-400">Türk Hukuku AI Asistanı</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-2xl rounded-lg p-4 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-100 border border-gray-700'
                }`}
              >
                {message.role === 'assistant' && (
                  <div className="flex items-center gap-2 mb-2 text-sm text-gray-400">
                    <span>🤖 HukukYZ</span>
                    {message.confidence !== undefined && (
                      <span className="ml-auto">
                        Güven: {(message.confidence * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                )}
                
                <div className="whitespace-pre-wrap">{message.content}</div>
                
                {message.citations && message.citations.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-700">
                    <p className="text-xs font-semibold text-gray-400 mb-2">
                      📚 Kaynaklar ({message.citations.length}):
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {message.citations.map((citation, i) => (
                        <button
                          key={i}
                          onClick={() => setSelectedCitation(citation)}
                          className="px-3 py-1 text-xs bg-gray-700 text-blue-300 rounded-full hover:bg-gray-600 transition cursor-pointer border border-gray-600"
                          title="Detayları görüntüle"
                        >
                          {citation.source || `Kaynak ${i + 1}`}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {message.metadata && (
                  <div className="mt-2 text-xs text-gray-500">
                    <span>{message.metadata.documents_retrieved} belge tarandı</span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-800 text-gray-100 border border-gray-700 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                  <span className="text-sm">Düşünüyorum...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {messages.length === 1 && (
        <div className="p-4 bg-gray-800 border-t border-gray-700">
          <div className="max-w-4xl mx-auto">
            <p className="text-sm text-gray-400 mb-3">Örnek sorular:</p>
            <div className="flex flex-wrap gap-2">
              {exampleQueries.map((query, index) => (
                <button
                  key={index}
                  onClick={() => setInput(query)}
                  className="px-3 py-1 text-sm bg-gray-700 text-gray-300 rounded-full hover:bg-gray-600 transition"
                >
                  {query}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="p-4 bg-gray-800 border-t border-gray-700">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Hukuki sorunuzu yazın..."
              disabled={loading}
              className="flex-1 px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:outline-none focus:border-blue-500 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {loading ? '⏳' : 'Gönder'}
            </button>
          </form>
          <p className="text-xs text-gray-500 mt-2 text-center">
            ⚠️ Test amaçlıdır. Profesyonel hukuki danışmanlık yerine geçmez.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Chat;
