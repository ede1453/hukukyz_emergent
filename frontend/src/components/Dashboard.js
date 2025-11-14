import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [mostCited, setMostCited] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [limit, setLimit] = useState(20);
  
  // Article content modal states
  const [articleContent, setArticleContent] = useState(null);
  const [relatedArticles, setRelatedArticles] = useState(null);
  const [loadingArticle, setLoadingArticle] = useState(false);
  const [loadingRelated, setLoadingRelated] = useState(false);
  const [navigationStack, setNavigationStack] = useState([]);

  useEffect(() => {
    fetchDashboardData();
  }, [limit]);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch stats
      const statsResponse = await axios.get(`${BACKEND_URL}/api/citations/stats`);
      
      // Fetch most cited articles
      const citedResponse = await axios.get(
        `${BACKEND_URL}/api/citations/most-cited?limit=${limit}`
      );

      if (statsResponse.data.success) {
        setStats(statsResponse.data.data);
      }

      if (citedResponse.data.success) {
        setMostCited(citedResponse.data.data);
      }

    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Dashboard verileri yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchDashboardData();
  };

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

  if (loading && !stats) {
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
            onClick={handleRefresh}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Tekrar Dene
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
                📊 HukukYZ Dashboard
              </h1>
              <p className="text-gray-400">Citation İstatistikleri ve Popüler Maddeler</p>
            </div>
            <button
              onClick={handleRefresh}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2"
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Yükleniyor
                </>
              ) : (
                <>
                  🔄 Yenile
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <div className="text-gray-400 text-sm mb-2">Toplam Alıntı</div>
            <div className="text-3xl font-bold text-blue-400">
              {stats?.total_citations || 0}
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <div className="text-gray-400 text-sm mb-2">Benzersiz Madde</div>
            <div className="text-3xl font-bold text-green-400">
              {stats?.unique_references || 0}
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <div className="text-gray-400 text-sm mb-2">Ortalama Alıntı</div>
            <div className="text-3xl font-bold text-purple-400">
              {stats?.avg_citations_per_ref || 0}
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <div className="text-gray-400 text-sm mb-2">Takip Edilen Belge</div>
            <div className="text-3xl font-bold text-yellow-400">
              {stats?.documents_tracked || 0}
            </div>
          </div>
        </div>

        {/* Most Cited Articles */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-white">
              🏆 En Çok Alıntılanan Maddeler
            </h2>
            <div className="flex items-center gap-2">
              <label className="text-gray-400 text-sm">Göster:</label>
              <select
                value={limit}
                onChange={(e) => setLimit(parseInt(e.target.value))}
                className="bg-gray-700 text-white px-3 py-1 rounded border border-gray-600 focus:outline-none focus:border-blue-500"
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
            </div>
          </div>

          {mostCited.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <p className="text-lg mb-2">📭 Henüz veri yok</p>
              <p className="text-sm">Kullanıcılar soru sordukça veriler toplanacak</p>
            </div>
          ) : (
            <div className="space-y-3">
              {mostCited.map((item, index) => {
                const percentage = stats?.total_citations > 0 
                  ? (item.citation_count / stats.total_citations * 100).toFixed(1)
                  : 0;

                return (
                  <div
                    key={index}
                    className="bg-gray-900 p-4 rounded-lg border border-gray-700 hover:border-blue-600 transition"
                  >
                    <div className="flex items-center gap-4">
                      {/* Rank */}
                      <div className={`text-2xl font-bold ${
                        index === 0 ? 'text-yellow-400' :
                        index === 1 ? 'text-gray-400' :
                        index === 2 ? 'text-orange-400' :
                        'text-gray-500'
                      }`}>
                        {index === 0 ? '🥇' : 
                         index === 1 ? '🥈' : 
                         index === 2 ? '🥉' : 
                         `#${index + 1}`}
                      </div>

                      {/* Reference */}
                      <div className="flex-1">
                        <div className="text-lg font-semibold text-blue-300 mb-1">
                          {item.reference}
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-400">
                          <span>{item.citation_count} alıntı</span>
                          <span>•</span>
                          <span>{percentage}% oranında</span>
                        </div>
                      </div>

                      {/* Progress Bar */}
                      <div className="w-48">
                        <div className="bg-gray-700 rounded-full h-3">
                          <div
                            className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-500"
                            style={{ width: `${Math.min(percentage * 2, 100)}%` }}
                          />
                        </div>
                      </div>

                      {/* Count Badge */}
                      <div className="px-4 py-2 bg-blue-600 rounded-full text-white font-bold">
                        {item.citation_count}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Top 5 Quick View */}
        {stats?.most_cited && stats.most_cited.length > 0 && (
          <div className="mt-8 bg-gray-800 rounded-lg border border-gray-700 p-6">
            <h3 className="text-xl font-bold text-white mb-4">
              ⚡ Top 5 Hızlı Görünüm
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
              {stats.most_cited.map(([ref, count], index) => (
                <div
                  key={index}
                  className="bg-gray-900 p-4 rounded-lg border border-gray-700 text-center"
                >
                  <div className="text-sm text-gray-400 mb-2">#{index + 1}</div>
                  <div className="font-semibold text-blue-300 mb-2 text-sm">
                    {ref}
                  </div>
                  <div className="text-2xl font-bold text-white">
                    {count}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">alıntı</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Info Box */}
        <div className="mt-8 bg-blue-900 bg-opacity-30 border border-blue-700 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <div className="text-2xl">ℹ️</div>
            <div>
              <h4 className="font-semibold text-blue-300 mb-2">
                Citation Tracking Nasıl Çalışır?
              </h4>
              <p className="text-sm text-gray-300 leading-relaxed">
                Sistem, kullanıcı sorularına verilen cevaplarda referans edilen hukuki maddeleri 
                otomatik olarak takip eder. Her maddenin ne sıklıkla kullanıldığı, hangi maddelerle 
                ilişkili olduğu ve popülerlik trendleri MongoDB'de saklanır. Bu veriler, kullanıcılara 
                daha iyi öneriler sunmak ve sistemin hukuki analiz yeteneklerini geliştirmek için kullanılır.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
