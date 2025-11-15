import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Chat = () => {
  const { token, isAuthenticated, user, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [creditBalance, setCreditBalance] = useState(null);
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
  const [relatedArticles, setRelatedArticles] = useState(null);
  const [articleContent, setArticleContent] = useState(null);
  const [loadingRelated, setLoadingRelated] = useState(false);
  const [loadingArticle, setLoadingArticle] = useState(false);
  const [navigationStack, setNavigationStack] = useState([]); // For back navigation
  const [sessionId] = useState('web-session-' + Date.now());
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [includeDeprecated, setIncludeDeprecated] = useState(false);
  const messagesEndRef = useRef(null);
  const isUserAdmin = isAdmin();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    
    // Fetch credit balance for non-admin users
    if (!isUserAdmin) {
      fetchCreditBalance();
      const interval = setInterval(fetchCreditBalance, 30000);
      return () => clearInterval(interval);
    }
  }, [isAuthenticated, isUserAdmin, navigate]);

  const fetchCreditBalance = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/credits/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.success) {
        setCreditBalance(response.data.balance);
      }
    } catch (error) {
      console.error('Error fetching balance:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchArticleContent = async (reference) => {
    setLoadingArticle(true);
    try {
      const response = await axios.get(
        `${BACKEND_URL}/api/citations/article/${encodeURIComponent(reference)}`
      );
      
      if (response.data.success) {
        // Save current state to navigation stack
        if (articleContent) {
          setNavigationStack(prev => [...prev, articleContent]);
        }
        
        setArticleContent(response.data.data);
        
        // Also fetch related articles
        const relatedResponse = await axios.get(
          `${BACKEND_URL}/api/citations/related/${encodeURIComponent(reference)}?limit=5`
        );
        
        if (relatedResponse.data.success) {
          setRelatedArticles({
            reference,
            articles: relatedResponse.data.data
          });
        }
      } else {
        setArticleContent({
          reference,
          error: response.data.error || 'İçerik bulunamadı'
        });
      }
    } catch (error) {
      console.error('Error fetching article:', error);
      setArticleContent({
        reference,
        error: 'İçerik yüklenirken hata oluştu'
      });
    } finally {
      setLoadingArticle(false);
    }
  };

  const goBack = () => {
    if (navigationStack.length > 0) {
      const previous = navigationStack[navigationStack.length - 1];
      setNavigationStack(prev => prev.slice(0, -1));
      setArticleContent(previous);
      
      // Fetch related for the previous article
      fetchRelatedArticles(previous.reference);
    } else {
      // Close modal
      setArticleContent(null);
      setRelatedArticles(null);
    }
  };

  const fetchRelatedArticles = async (reference) => {
    setLoadingRelated(true);
    try {
      const response = await axios.get(
        `${BACKEND_URL}/api/citations/related/${encodeURIComponent(reference)}?limit=5`
      );
      
      if (response.data.success) {
        setRelatedArticles({
          reference,
          articles: response.data.data
        });
      }
    } catch (error) {
      console.error('Error fetching related articles:', error);
      setRelatedArticles({
        reference,
        articles: [],
        error: 'İlgili maddeler yüklenirken hata oluştu'
      });
    } finally {
      setLoadingRelated(false);
    }
  };

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
          session_id: sessionId,
          include_deprecated: includeDeprecated
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
    'Cayma hakkı nedir?',
    'Kıdem tazminatı nasıl hesaplanır?'
  ];

  // Auto-linking function: Convert legal references to clickable links
  const autoLinkReferences = (text) => {
    // Regex to match legal references like "TTK m.365", "TBK m.1", "İİK m.165"
    const referenceRegex = /(TTK|TBK|TMK|İİK|HMK)\s+m\.(\d+)/gi;
    
    const parts = [];
    let lastIndex = 0;
    let match;
    
    while ((match = referenceRegex.exec(text)) !== null) {
      // Add text before match
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: text.substring(lastIndex, match.index)
        });
      }
      
      // Add matched reference as link
      parts.push({
        type: 'link',
        content: match[0],
        reference: match[0]
      });
      
      lastIndex = match.index + match[0].length;
    }
    
    // Add remaining text
    if (lastIndex < text.length) {
      parts.push({
        type: 'text',
        content: text.substring(lastIndex)
      });
    }
    
    return parts.length > 0 ? parts : [{ type: 'text', content: text }];
  };

  const copyToClipboard = (text, index) => {
    try {
      // Create textarea element
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.top = '0';
      textArea.style.left = '0';
      textArea.style.width = '2em';
      textArea.style.height = '2em';
      textArea.style.padding = '0';
      textArea.style.border = 'none';
      textArea.style.outline = 'none';
      textArea.style.boxShadow = 'none';
      textArea.style.background = 'transparent';
      
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      
      const successful = document.execCommand('copy');
      document.body.removeChild(textArea);
      
      if (successful) {
        setCopiedIndex(index);
        setTimeout(() => setCopiedIndex(null), 2000);
      } else {
        alert('Kopyalama başarısız oldu');
      }
    } catch (err) {
      console.error('Copy failed:', err);
      alert('Kopyalama hatası: ' + err.message);
    }
  };

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
                
                <div className="flex items-start gap-2">
                  <div className="flex-1 whitespace-pre-wrap">
                    {message.role === 'assistant' ? (
                      // Auto-link legal references in assistant messages
                      autoLinkReferences(message.content).map((part, i) => (
                        part.type === 'link' ? (
                          <button
                            key={i}
                            onClick={() => {
                              setNavigationStack([]);
                              fetchArticleContent(part.reference);
                            }}
                            className="text-blue-400 hover:text-blue-300 underline cursor-pointer font-semibold"
                            title="İçeriğini görüntüle"
                          >
                            {part.content}
                          </button>
                        ) : (
                          <span key={i}>{part.content}</span>
                        )
                      ))
                    ) : (
                      // User messages without auto-linking
                      message.content
                    )}
                  </div>
                  {message.role === 'assistant' && (
                    <button
                      onClick={() => copyToClipboard(message.content, index)}
                      className="flex-shrink-0 p-2 text-gray-400 hover:text-gray-200 transition"
                      title="Kopyala"
                    >
                      {copiedIndex === index ? '✓' : '📋'}
                    </button>
                  )}
                </div>
                
                {message.citations && message.citations.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-700">
                    <p className="text-xs font-semibold text-gray-400 mb-2">
                      📚 Kaynaklar ({message.citations.length}):
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {message.citations.map((citation, i) => (
                        <div key={i} className="flex gap-1">
                          <button
                            onClick={() => setSelectedCitation(citation)}
                            className="px-3 py-1 text-xs bg-gray-700 text-blue-300 rounded-full hover:bg-gray-600 transition cursor-pointer border border-gray-600"
                            title="Detayları görüntüle"
                          >
                            {citation.source || `Kaynak ${i + 1}`}
                          </button>
                          <button
                            onClick={() => {
                              setNavigationStack([]);
                              fetchArticleContent(citation.source || citation.law_name);
                            }}
                            className="px-2 py-1 text-xs bg-purple-700 text-purple-200 rounded-full hover:bg-purple-600 transition cursor-pointer border border-purple-600"
                            title="İçerik ve ilgili maddeleri gör"
                          >
                            🔗
                          </button>
                        </div>
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
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="flex gap-2">
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
            </div>
            
            {/* Deprecated checkbox */}
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-2 cursor-pointer text-sm text-gray-400 hover:text-gray-300">
                <input
                  type="checkbox"
                  checked={includeDeprecated}
                  onChange={(e) => setIncludeDeprecated(e.target.checked)}
                  className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-2"
                />
                <span>Eski/iptal edilmiş belge versiyonlarını da dahil et</span>
                <span className="text-xs text-yellow-500">(⚠️ Güncel olmayan bilgiler içerebilir)</span>
              </label>
            </div>
          </form>
          
          <p className="text-xs text-gray-500 mt-2 text-center">
            ⚠️ Test amaçlıdır. Profesyonel hukuki danışmanlık yerine geçmez.
          </p>
        </div>
      </div>

      {/* Article Content Modal with Related Articles */}
      {articleContent && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => {
            setArticleContent(null);
            setRelatedArticles(null);
            setNavigationStack([]);
          }}
        >
          <div 
            className="bg-gray-800 rounded-lg p-6 max-w-4xl w-full border border-gray-700 shadow-2xl max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header with Back/Close */}
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                {navigationStack.length > 0 && (
                  <button
                    onClick={goBack}
                    className="px-3 py-1 bg-gray-700 text-gray-300 rounded hover:bg-gray-600 transition flex items-center gap-1"
                    title="Geri"
                  >
                    ← Geri
                  </button>
                )}
                <h3 className="text-xl font-bold text-white">
                  📖 {articleContent.reference}
                </h3>
              </div>
              <button
                onClick={() => {
                  setArticleContent(null);
                  setRelatedArticles(null);
                  setNavigationStack([]);
                }}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            {loadingArticle ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                <span className="ml-3 text-gray-400">Yükleniyor...</span>
              </div>
            ) : articleContent.error ? (
              <div className="text-center py-12 text-gray-400">
                <p>❌ {articleContent.error}</p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Article Content */}
                <div className="bg-gray-900 p-5 rounded-lg border border-gray-700">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="px-2 py-1 bg-blue-600 text-white text-xs rounded">
                      {articleContent.kaynak || articleContent.law_code}
                    </span>
                    {articleContent.status && (
                      <span className={`px-2 py-1 text-xs rounded ${
                        articleContent.status === 'active' 
                          ? 'bg-green-600 text-white' 
                          : 'bg-yellow-600 text-white'
                      }`}>
                        {articleContent.status === 'active' ? 'Güncel' : 'Eski'}
                      </span>
                    )}
                  </div>
                  
                  {articleContent.title && (
                    <h4 className="text-lg font-semibold text-gray-200 mb-3">
                      {articleContent.title}
                    </h4>
                  )}
                  
                  <p className="text-gray-300 whitespace-pre-wrap leading-relaxed">
                    {articleContent.content}
                  </p>
                </div>
                
                {/* Related Articles Section */}
                {relatedArticles && (
                  <div className="border-t border-gray-700 pt-5">
                    <h4 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                      🔗 İlgili Maddeler
                    </h4>
                    
                    {loadingRelated ? (
                      <div className="flex items-center justify-center py-8">
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-500"></div>
                        <span className="ml-2 text-gray-400">Yükleniyor...</span>
                      </div>
                    ) : relatedArticles.articles.length === 0 ? (
                      <div className="text-center py-6 text-gray-400">
                        <p className="text-sm">📭 İlgili madde bulunamadı</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {relatedArticles.articles.map((article, i) => (
                          <button
                            key={i}
                            onClick={() => fetchArticleContent(article.reference)}
                            className="bg-gray-900 p-4 rounded-lg border border-gray-700 hover:border-purple-600 transition text-left"
                          >
                            <p className="font-semibold text-blue-300 mb-1">
                              {article.reference}
                            </p>
                            <p className="text-xs text-gray-500 capitalize">
                              {article.relationship === 'related' ? '🔗 İlişkili' : 
                               article.relationship === 'cited-by' ? '⬅️ Buna atıf yapan' :
                               article.relationship === 'cites' ? '➡️ Bunun atıf yaptığı' :
                               article.relationship}
                            </p>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
            
            {/* Footer */}
            <div className="mt-6 flex justify-between items-center border-t border-gray-700 pt-4">
              {navigationStack.length > 0 && (
                <button
                  onClick={goBack}
                  className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition"
                >
                  ← Geri
                </button>
              )}
              <button
                onClick={() => {
                  setArticleContent(null);
                  setRelatedArticles(null);
                  setNavigationStack([]);
                }}
                className={`px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition ${
                  navigationStack.length === 0 ? 'ml-auto' : ''
                }`}
              >
                Kapat
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Citation Modal */}
      {selectedCitation && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedCitation(null)}
        >
          <div 
            className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full border border-gray-700 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                📖 {selectedCitation.source || 'Kaynak'}
              </h3>
              <button
                onClick={() => setSelectedCitation(null)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-4">
              {selectedCitation.text && (
                <div>
                  <p className="text-sm font-semibold text-gray-400 mb-2">📄 İçerik:</p>
                  <p className="text-gray-200 bg-gray-900 p-4 rounded border border-gray-700 whitespace-pre-wrap">
                    {selectedCitation.text}
                  </p>
                </div>
              )}
              
              {selectedCitation.doc_type && (
                <div>
                  <p className="text-sm font-semibold text-gray-400">📚 Tip:</p>
                  <p className="text-gray-300">{selectedCitation.doc_type}</p>
                </div>
              )}
              
              {selectedCitation.relevance !== undefined && (
                <div>
                  <p className="text-sm font-semibold text-gray-400">🎯 Alakalılık:</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${selectedCitation.relevance * 100}%` }}
                      />
                    </div>
                    <span className="text-gray-300 text-sm">
                      {(selectedCitation.relevance * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              )}
              
              {selectedCitation.url && (
                <div>
                  <a
                    href={selectedCitation.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 text-sm"
                  >
                    🔗 Kaynağı Görüntüle
                  </a>
                </div>
              )}
            </div>
            
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedCitation(null)}
                className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition"
              >
                Kapat
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chat;
