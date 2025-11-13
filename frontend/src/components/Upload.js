import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Upload = () => {
  const [collections, setCollections] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);  // Support multiple files
  const [selectedCollection, setSelectedCollection] = useState('');  // Empty by default - user must select
  const [createNew, setCreateNew] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState(null);
  const [stats, setStats] = useState(null);
  const [bulkMode, setBulkMode] = useState(false);

  useEffect(() => {
    loadCollections();
    loadStats();
  }, []);

  const loadCollections = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/documents/collections`);
      setCollections(response.data);
      if (response.data.length > 0) {
        setSelectedCollection(response.data[0].name);
      }
    } catch (error) {
      console.error('Collections yüklenemedi:', error);
    }
  };

  const loadStats = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/documents/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Stats yüklenemedi:', error);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setUploadResult(null);
    } else {
      alert('Lütfen sadece PDF dosyası seçin');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      alert('Lütfen bir PDF dosyası seçin');
      return;
    }

    if (!createNew && !selectedCollection) {
      alert('Lütfen bir koleksiyon seçin');
      return;
    }

    if (createNew && !newCollectionName.trim()) {
      alert('Lütfen yeni koleksiyon ismi girin');
      return;
    }

    setUploading(true);
    setUploadResult(null);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('collection', selectedCollection);
    formData.append('create_new', createNew);
    if (createNew) {
      formData.append('new_collection_name', newCollectionName);
    }

    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/documents/upload`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 180000, // 3 minutes
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setUploadProgress(percentCompleted);
          }
        }
      );

      setUploadResult({
        success: true,
        ...response.data
      });

      // Refresh collections and stats
      await loadCollections();
      await loadStats();

      // Clear form
      setSelectedFile(null);
      setNewCollectionName('');
      setCreateNew(false);

    } catch (error) {
      setUploadResult({
        success: false,
        message: error.response?.data?.detail || error.message
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold text-white">📄 PDF Yükleme</h1>
          <p className="text-sm text-gray-400">Hukuki PDF belgelerini yükleyin ve otomatik indexleyin</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto p-6">
        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="text-3xl font-bold text-blue-400">{stats.total_documents}</div>
              <div className="text-sm text-gray-400">Toplam Belge</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="text-3xl font-bold text-green-400">{stats.total_collections}</div>
              <div className="text-sm text-gray-400">Koleksiyon</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="text-3xl font-bold text-purple-400">
                {collections.find(c => c.name === selectedCollection)?.document_count || 0}
              </div>
              <div className="text-sm text-gray-400">Seçili Koleksiyon</div>
            </div>
          </div>
        )}

        {/* Upload Form */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">PDF Yükle</h2>

          {/* File Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              PDF Dosyası
            </label>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              disabled={uploading}
              className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 
                       focus:outline-none focus:border-blue-500 disabled:opacity-50
                       file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0
                       file:text-sm file:font-semibold file:bg-blue-600 file:text-white
                       hover:file:bg-blue-700"
            />
            {selectedFile && (
              <p className="mt-2 text-sm text-gray-400">
                Seçili: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            )}
          </div>

          {/* Collection Selection */}
          <div className="mb-4">
            <label className="flex items-center text-sm font-medium text-gray-300 mb-2">
              <input
                type="checkbox"
                checked={createNew}
                onChange={(e) => setCreateNew(e.target.checked)}
                disabled={uploading}
                className="mr-2"
              />
              Yeni koleksiyon oluştur
            </label>

            {!createNew ? (
              <select
                value={selectedCollection}
                onChange={(e) => setSelectedCollection(e.target.value)}
                disabled={uploading}
                className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 
                         focus:outline-none focus:border-blue-500 disabled:opacity-50"
              >
                {collections.map((col) => (
                  <option key={col.name} value={col.name}>
                    {col.display_name} ({col.document_count} belge)
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                value={newCollectionName}
                onChange={(e) => setNewCollectionName(e.target.value)}
                placeholder="Yeni koleksiyon ismi (örn: vergi_hukuku)"
                disabled={uploading}
                className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 
                         focus:outline-none focus:border-blue-500 disabled:opacity-50"
              />
            )}

            {selectedCollection && !createNew && (
              <p className="mt-2 text-sm text-gray-400">
                {collections.find(c => c.name === selectedCollection)?.description}
              </p>
            )}
          </div>

          {/* Upload Button */}
          <button
            onClick={handleUpload}
            disabled={uploading || !selectedFile}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 
                     transition disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {uploading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Yükleniyor...
              </span>
            ) : (
              '📤 PDF Yükle'
            )}
          </button>

          {/* Progress Bar */}
          {uploading && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-400 mb-2">
                <span>Yükleme İlerlemesi</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-blue-500 h-full rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${uploadProgress}%` }}
                >
                  <div className="h-full w-full bg-gradient-to-r from-blue-400 to-blue-600 animate-pulse"></div>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {uploadProgress < 100 
                  ? 'PDF işleniyor ve vektör veritabanına yükleniyor...' 
                  : 'Tamamlanıyor...'}
              </p>
            </div>
          )}
        </div>

        {/* Upload Result */}
        {uploadResult && (
          <div className={`mt-6 p-4 rounded-lg border ${
            uploadResult.success 
              ? 'bg-green-900 border-green-700' 
              : 'bg-red-900 border-red-700'
          }`}>
            <h3 className={`font-semibold mb-2 ${
              uploadResult.success ? 'text-green-100' : 'text-red-100'
            }`}>
              {uploadResult.success ? '✅ Başarılı!' : '❌ Hata'}
            </h3>
            <p className={uploadResult.success ? 'text-green-200' : 'text-red-200'}>
              {uploadResult.message}
            </p>
            {uploadResult.success && (
              <div className="mt-3 text-sm text-green-300">
                <p>• Kanun: {uploadResult.law_code} - {uploadResult.law_name}</p>
                <p>• Koleksiyon: {uploadResult.collection}</p>
                <p>• Yüklenen Madde: {uploadResult.articles_count}</p>
              </div>
            )}
          </div>
        )}

        {/* Collections List */}
        <div className="mt-6 bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Mevcut Koleksiyonlar</h2>
          <div className="space-y-2">
            {collections.map((col) => (
              <div 
                key={col.name}
                className="flex items-center justify-between p-3 bg-gray-700 rounded-lg hover:bg-gray-600 transition"
              >
                <div>
                  <div className="font-medium text-white">{col.display_name}</div>
                  <div className="text-sm text-gray-400">{col.description}</div>
                </div>
                <div className="text-2xl font-bold text-blue-400">
                  {col.document_count}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Upload;
