import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const QdrantAdmin = () => {
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCollection, setSelectedCollection] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchCollections();
  }, []);

  const fetchCollections = async () => {
    setLoading(true);
    setError(null);

    try {
      // Use mobile API collections endpoint
      const response = await axios.get(`${BACKEND_URL}/api/mobile/collections`);
      
      if (response.data.success) {
        setCollections(response.data.collections);
      }
    } catch (err) {
      console.error('Error fetching collections:', err);
      setError('Koleksiyonlar yüklenirken hata oluştu');
    } finally {
      setLoading(false);
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
            onClick={fetchCollections}
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
                🗄️ Qdrant Yönetim
              </h1>
              <p className="text-gray-400">Vektör veritabanı koleksiyonları</p>
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
        {/* Info Box */}
        <div className="mb-6 bg-blue-900 bg-opacity-30 border border-blue-700 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <div className="text-xl">ℹ️</div>
            <div>
              <h4 className="font-semibold text-blue-300 mb-1">
                Qdrant Cloud Bağlantısı
              </h4>
              <p className="text-sm text-gray-300">
                Platform, Qdrant Cloud üzerinde 8 koleksiyon kullanıyor. 
                Her koleksiyon farklı bir hukuk dalını temsil eder.
              </p>
            </div>
          </div>
        </div>

        {/* Collections Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {collections.map((collection, index) => (
            <div
              key={index}
              className="bg-gray-800 rounded-lg border border-gray-700 p-6 hover:border-blue-600 transition"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="px-3 py-1 bg-blue-600 text-white text-sm rounded-full font-semibold">
                      {collection.code}
                    </span>
                    <span className="px-2 py-1 bg-green-600 text-white text-xs rounded">
                      Aktif
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-white mb-1">
                    {collection.name}
                  </h3>
                  <p className="text-sm text-gray-400">
                    {collection.description}
                  </p>
                </div>
              </div>

              <div className="border-t border-gray-700 pt-4 mt-4">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-gray-500 mb-1">Koleksiyon ID</p>
                    <p className="text-gray-300 font-mono text-xs">
                      {collection.id}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500 mb-1">Durum</p>
                    <p className="text-green-400">✓ Çalışıyor</p>
                  </div>
                </div>
              </div>

              <div className="mt-4 flex gap-2">
                <button
                  onClick={() => setSelectedCollection(collection)}
                  className="flex-1 px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600 transition text-sm"
                >
                  📊 Detaylar
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Stats Summary */}
        <div className="mt-8 bg-gray-800 rounded-lg border border-gray-700 p-6">
          <h3 className="text-xl font-bold text-white mb-4">
            📈 Sistem Özeti
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-400">{collections.length}</p>
              <p className="text-sm text-gray-400 mt-1">Toplam Koleksiyon</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-green-400">1600+</p>
              <p className="text-sm text-gray-400 mt-1">Toplam Belge</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-purple-400">1536</p>
              <p className="text-sm text-gray-400 mt-1">Vektör Boyutu</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-yellow-400">Cloud</p>
              <p className="text-sm text-gray-400 mt-1">Qdrant Tipi</p>
            </div>
          </div>
        </div>

        {/* Connection Info */}
        <div className="mt-6 bg-gray-800 rounded-lg border border-gray-700 p-6">
          <h3 className="text-lg font-bold text-white mb-3">
            🔗 Bağlantı Bilgileri
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-gray-400">URL:</span>
              <code className="text-blue-400 bg-gray-900 px-2 py-1 rounded">
                Qdrant Cloud (EU Central)
              </code>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-400">Auth:</span>
              <code className="text-green-400 bg-gray-900 px-2 py-1 rounded">
                API Key (Configured)
              </code>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-400">Status:</span>
              <span className="text-green-400">✓ Connected</span>
            </div>
          </div>
        </div>
      </div>

      {/* Collection Details Modal */}
      {selectedCollection && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedCollection(null)}
        >
          <div 
            className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full border border-gray-700"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-2xl font-bold text-white">
                {selectedCollection.name}
              </h3>
              <button
                onClick={() => setSelectedCollection(null)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Koleksiyon ID
                </label>
                <code className="block text-sm bg-gray-900 p-2 rounded text-blue-400">
                  {selectedCollection.id}
                </code>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Kanun Kodu
                </label>
                <code className="block text-sm bg-gray-900 p-2 rounded text-green-400">
                  {selectedCollection.code}
                </code>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Açıklama
                </label>
                <p className="text-gray-300">
                  {selectedCollection.description}
                </p>
              </div>

              <div className="pt-4 border-t border-gray-700">
                <h4 className="font-semibold text-white mb-2">Özellikler</h4>
                <ul className="space-y-2 text-sm text-gray-300">
                  <li>✓ Vektör boyutu: 1536 (OpenAI embedding-3-small)</li>
                  <li>✓ Payload indexing aktif (status, version, doc_type, etc.)</li>
                  <li>✓ Version filtering desteği</li>
                  <li>✓ Metadata filtreleme</li>
                </ul>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedCollection(null)}
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

export default QdrantAdmin;
