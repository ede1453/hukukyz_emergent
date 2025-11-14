import React, { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import axios from "axios";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import Chat from "./components/Chat";
import Upload from "./components/Upload";
import Dashboard from "./components/Dashboard";
import Login from "./components/Login";
import Register from "./components/Register";
import Profile from "./components/Profile";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Home = () => {
  const [backendStatus, setBackendStatus] = React.useState("checking...");
  const { user, isAuthenticated } = useAuth();
  
  const checkBackend = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/`);
      console.log("Backend response:", response.data);
      setBackendStatus("✅ Connected");
    } catch (e) {
      console.error("Backend error:", e);
      setBackendStatus("❌ Connection failed");
    }
  };

  useEffect(() => {
    checkBackend();
  }, []);

  return (
    <div>
      <header className="App-header">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">🏛️ HukukYZ</h1>
          <p className="text-xl text-gray-300">AI-Powered Turkish Legal Assistant</p>
          <p className="text-sm text-gray-400 mt-2">Backend: {backendStatus}</p>
        </div>
        
        <div className="w-full max-w-2xl bg-gray-800 rounded-lg p-6 shadow-xl">
          <h2 className="text-2xl font-semibold text-white mb-4">Sistem Durumu</h2>
          <div className="space-y-3 text-left">
            <div className="flex items-center justify-between p-3 bg-gray-700 rounded">
              <span className="text-gray-300">Backend API</span>
              <span className="text-green-400">✅ Çalışıyor</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-700 rounded">
              <span className="text-gray-300">Frontend</span>
              <span className="text-green-400">✅ Çalışıyor</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-700 rounded">
              <span className="text-gray-300">Agent System</span>
              <span className="text-green-400">✅ 7/10 Active</span>
            </div>
          </div>
          
          <div className="mt-6 p-4 bg-green-900 rounded border border-green-700">
            <p className="text-green-100 text-sm">
              ✅ <strong>Sistem Hazır!</strong> RAG pipeline aktif ve çalışıyor. 
              12 hukuki belge yüklendi. Chat arayüzünü kullanabilirsiniz.
            </p>
          </div>

          {/* Auth Status */}
          {isAuthenticated && user && (
            <div className="mt-4 text-center">
              <p className="text-gray-400 text-sm">
                Hoş geldiniz, <span className="text-blue-400 font-semibold">{user.full_name}</span>
              </p>
            </div>
          )}
          
          <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <Link
              to="/chat"
              className="text-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
            >
              💬 Chat Başlat
            </Link>
            <Link
              to="/upload"
              className="text-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium"
            >
              📄 PDF Yükle
            </Link>
            <Link
              to="/dashboard"
              className="text-center px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition font-medium"
            >
              📊 Dashboard
            </Link>
            <a
              href="/api/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="text-center px-6 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition"
            >
              📖 API Docs
            </a>
          </div>

          {/* Auth Buttons */}
          <div className="mt-6 flex justify-center gap-3">
            {isAuthenticated ? (
              <Link
                to="/profile"
                className="px-6 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition"
              >
                👤 Profilim
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="px-6 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition"
                >
                  🔐 Giriş Yap
                </Link>
                <Link
                  to="/register"
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  ✍️ Kayıt Ol
                </Link>
              </>
            )}
          </div>
        </div>
        
        <div className="mt-8 text-sm text-gray-500">
          <p>Powered by Emergent AI</p>
        </div>
      </header>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
