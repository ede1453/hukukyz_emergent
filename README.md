# HukukYZ - AI-Powered Legal Assistant Platform

> **Türk Hukuku için Gelişmiş Yapay Zeka Tabanlı Hukuk Asistanı**

[![Status](https://img.shields.io/badge/status-in%20development-yellow)]() 
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]() 
[![React](https://img.shields.io/badge/react-19.0-blue)]() 
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## 🎯 Proje Hakkında

**HukukYZ**, Türk hukuku alanında uzmanlaşmış, ileri düzey yapay zeka teknolojileri kullanan kapsamlı bir hukuki asistan platformudur. Platform, aşağıdaki özellikleri sunar:

- 📚 **Çoklu Hukuk Alanları**: Ticaret, Borçlar, İcra-İflas, Medeni, Tüketici, Bankacılık, HMK
- 🤖 **Gelişmiş AI Agents**: LangGraph, LangChain, CrewAI ile multi-agent sistemi
- 🔍 **RAG Pipeline**: Semantic, keyword ve hybrid search stratejileri
- 📝 **Versiyon Kontrolü**: Kanun değişikliklerini takip ve geçmiş sorguları
- 📱 **Multi-Platform**: Web, Telegram Bot, Mobil Uygulama
- 🔐 **MCP Protokolü**: Standartlaştırılmış araç entegrasyonu

---

## 🏗️ Mimari

```
╭──────────────────────────────────────────╮
│          Frontend Layer                │
│  React Web │ Telegram Bot │ Mobile  │
╰───────────────┬───────────────────────────╯
               │
╭───────────────▼───────────────────────────╮
│        FastAPI Gateway            │
╰───────────────┬───────────────────────────╯
               │
╭───────────────▼───────────────────────────╮
│   LangGraph Agent System        │
│  (Multi-Agent Orchestration)    │
╰───────────────┬───────────────────────────╯
               │
╭───────────────▼───────────────────────────╮
│      MCP Tool Layer             │
│  (Standardized Interfaces)      │
╰───────────────┬───────────────────────────╯
               │
╭───────────────▼───────────────────────────╮
│   Qdrant  │ MongoDB │ Redis   │
╰──────────────────────────────────────────╯
```

Detaylı mimari için: [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## 🚀 Özellikler

### 🤖 AI Agents

- **Meta-Controller**: Görev yönlendirme ve koleksiyon seçimi
- **Planner**: Çok adımlı sorgu ayrıştırma
- **Gatekeeper**: Belirsizlik tespiti ve netlik sağlama
- **Researcher**: Çoklu stratejili doküman arama
- **Analyst**: Hukuki analiz ve çapraz referanslama
- **Auditor**: Kalite kontrol ve doğrulama
- **Synthesizer**: Nihai cevap sentezi ve kaynak gösterme

### 🔍 Retrieval Strategies

- **Vector Search**: Semantik benzerlik
- **Keyword Search**: BM25 tam metin arama
- **Hybrid Search**: RRF ile kombine yaklaşım
- **Cross-Encoder Reranking**: Hassas sıralama

### 📚 Legal-Specific Tools

- **Madde/Fıkra/Bent Parser**: "TTK m.11/2-c" gibi referansları ayrıştırma
- **Citation Tracker**: Kanunlar arası atıf takibi
- **Historical Query**: Tarihsel versiyon sorgulama
- **Comparative Analyzer**: Kanun karşılaştırma
- **Precedent Linker**: İçtihat bağlantılama

### 📄 Document Management

- **Transactional Upload**: Güvenli doküman yükleme
- **Version Control**: Kanun değişiklik takibi
- **Shadow Collections**: Test ve doğrulama
- **Rollback Support**: Hatalı yüklemelerde geri alma

---

## 💻 Teknoloji Stackı

### Backend
- **Framework**: FastAPI 0.110+
- **AI/ML**: 
  - LangGraph (Agent orchestration)
  - LangChain (Tool integration)
  - CrewAI (Multi-agent collaboration)
  - OpenAI GPT-4 (LLM)
- **Databases**:
  - Qdrant (Vector DB)
  - MongoDB (Document store)
  - Redis (Cache)
- **Tools**: MCP (Model Context Protocol)

### Frontend
- **Framework**: React 19
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Library**: Radix UI
- **State**: React Query + Context API

### DevOps
- **Containerization**: Docker
- **Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana

---

## 🛠️ Kurulum

### Gereksinimler

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Qdrant (local veya cloud)
- MongoDB (local veya Atlas)

### 1. Repository'yi Klonlama

```bash
git clone https://github.com/your-org/hukukyz.git
cd hukukyz
```

### 2. Environment Variables

```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env ve API keylerini ekle

# Frontend
cp frontend/.env.example frontend/.env
# Edit frontend/.env
```

**Gerekli API Keys**:
- `OPENAI_API_KEY`: OpenAI API key
- `TAVILY_API_KEY`: Web search API key (opsiyonel)
- `QDRANT_URL`: Qdrant instance URL
- `MONGO_URL`: MongoDB connection string

### 3. Backend Kurulumu

```bash
cd backend

# Virtual environment oluştur
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies yükle
pip install -r requirements.txt

# MCP servers çalıştır
python -m mcp.servers.legal_documents
python -m mcp.servers.document_processor
python -m mcp.servers.web_search
python -m mcp.servers.version_control

# FastAPI server çalıştır
uvicorn main:app --reload --port 8001
```

### 4. Frontend Kurulumu

```bash
cd frontend

# Dependencies yükle
yarn install

# Development server
yarn start
```

### 5. Docker ile Çalıştırma (Alternatif)

```bash
# Tüm servisleri başlat
docker-compose up -d

# Logları kontrol et
docker-compose logs -f
```

---

## 📚 Dokümantasyon

- **[ARCHITECTURE.md](./ARCHITECTURE.md)**: Detaylı sistem mimarisi
- **[DEVELOPMENT_CHECKLIST.md](./DEVELOPMENT_CHECKLIST.md)**: Geliştirme kontrol listesi
- **[MCP_INTEGRATION.md](./MCP_INTEGRATION.md)**: MCP protokolü entegrasyonu
- **[PROJECT_PLAN.md](./PROJECT_PLAN.md)**: Proje planı ve zaman çizelgesi

---

## 🧪 Kullanım

### Web Arayüzü

1. Tarayıcıda `http://localhost:3000` adresini açın
2. Sohbet arayüzünde sorgunuzu yazın:
   ```
   TTK 11. maddeye göre ticaret şirketlerinin kuruluşu nasıl olur?
   ```

3. AI agent süreci takip edin:
   - Sorgu optimizasyonu
   - Doküman arama
   - Analiz
   - Cevap sentezi

4. Kaynak gösterimli cevabı alın
### API Kullanımı

```python
import requests

response = requests.post(
    "http://localhost:8001/api/chat/query",
    json={
        "query": "TTK 11. maddeye göre ticaret şirketlerinin kuruluşu",
        "user_id": "user123",
        "session_id": "session456"
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

print(response.json())
```

### Doküman Yükleme

```python
import requests

files = {'file': open('yeni_kanun.pdf', 'rb')}
data = {
    'doc_type': 'kanun',
    'hukuk_dali': 'ticaret',
    'version': '2024.1'
}

response = requests.post(
    "http://localhost:8001/api/documents/upload",
    files=files,
    data=data,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

print(response.json())
```

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v --cov=.
```

### Frontend Tests

```bash
cd frontend
yarn test
```

### E2E Tests

```bash
cd frontend
yarn test:e2e
```

---

## 📈 Monitoring

### Metrics Dashboard

Prometheus metrics: `http://localhost:8001/metrics`

Grafana dashboard: `http://localhost:3001`

### Logging

Loklar: `/var/log/hukukyz/`

```bash
# Backend logs
tail -f /var/log/hukukyz/backend.log

# Agent activity
tail -f /var/log/hukukyz/agents.log
```

---

## 👥 Katkıda Bulunma

Katkılarınızı bekliyoruz! Lütfen:

1. Fork yapın
2. Feature branch oluşturun:
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. Değişikliklerinizi commit edin:
   ```bash
   git commit -m 'Add amazing feature'
   ```

4. Branch'i push edin:
   ```bash
   git push origin feature/amazing-feature
   ```

5. Pull Request açın

---

## 📝 Roadmap

### Phase 1 (Current)
- [x] Proje mimarisi tasarımı
- [ ] Backend core development
- [ ] MCP servers implementation
- [ ] Agent system development

### Phase 2
- [ ] RAG pipeline completion
- [ ] Web frontend
- [ ] Document upload system

### Phase 3
- [ ] Telegram bot
- [ ] Mobile app
- [ ] Advanced features

### Future
- [ ] Graph memory (Neo4j)
- [ ] Multi-modal (vision)
- [ ] Voice interface
- [ ] Fine-tuned Turkish legal LLM

---

## 💬 Destek

- **Email**: support@hukukyz.com
- **Discord**: [HukukYZ Community](https://discord.gg/hukukyz)
- **Issues**: [GitHub Issues](https://github.com/your-org/hukukyz/issues)

---

## 📜 Lisans

MIT License - Detaylar için [LICENSE](./LICENSE) dosyasına bakın

---

## 🚀 Deployment

### Production Deployment

Detaylı deployment rehberi için [DEPLOYMENT.md](./DEPLOYMENT.md) dosyasına bakın

```bash
# Docker production build
docker-compose -f docker-compose.prod.yml up -d

# Kubernetes deployment
kubectl apply -f k8s/
```

---

## ⚠️ Disclaimer

Bu platform yalnızca bilgilendirme amaçlıdır. Sunulan bilgiler hukuki tavsiye niteliğinde değildir. Önemli hukuki konularda mutlaka lisanslı bir avukata danışın.

---

## 🚀 Başlangıç

Projeyi başlatmak için:

```bash
# 1. İlk setup
make setup

# 2. Development başlat
make dev

# 3. Tarayıcıda aç
make open
```

---

**HukukYZ** - Türk Hukuku için Yapay Zeka Gücü ⚖️🤖

İyi kodlamalar! 🚀
