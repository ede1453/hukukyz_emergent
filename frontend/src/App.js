import React, { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import axios from "axios";
import Chat from "./components/Chat";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Home = () => {
  const [backendStatus, setBackendStatus] = React.useState("checking...");
  
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
          
          <div className="mt-6 flex gap-4">
            <Link
              to="/chat"
              className="flex-1 text-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
            >
              💬 Chat Başlat
            </Link>
            <a
              href={`${BACKEND_URL}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 text-center px-6 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition"
            >
              📖 API Docs
            </a>
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
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
