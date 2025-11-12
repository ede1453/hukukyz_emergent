# 🏛️ HukukYZ - Türk Hukuku AI Asistanı

Türk hukuku üzerine gelişmiş RAG (Retrieval-Augmented Generation) tabanlı yapay zeka asistanı.

## 🚀 Hızlı Başlangıç

### Önkoşullar
- Docker & Docker Compose
- OpenAI API key

### 1. Clone & Setup

```bash
git clone https://github.com/your-username/hukukyz.git
cd hukukyz
cp .env.example backend/.env
```

`.env` dosyasını düzenle ve `OPENAI_API_KEY` ekle.

### 2. Docker ile Başlat

```bash
# Hızlı başlatma
./start.sh

# VEYA make ile
make up

# VEYA docker-compose ile
docker-compose up -d
```

### 3. Erişim

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8001/docs
- **Qdrant**: http://localhost:6333/dashboard

## 🏗️ Servisler

| Servis | Port | Açıklama |
|--------|------|----------|
| Frontend | 3000 | React UI |
| Backend | 8001 | FastAPI |
| Qdrant | 6333 | Vector DB |
| MongoDB | 27017 | Sessions |

## 📚 Kullanım

### Chat Query
```bash
curl -X POST http://localhost:8001/api/chat/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Anonim şirket nedir?", "session_id": "test"}'
```

### PDF Upload
```bash
curl -X POST http://localhost:8001/api/documents/upload \
  -F "file=@kanun.pdf" \
  -F "collection=ticaret_hukuku"
```

## 🎯 Özellikler

- ✅ Multi-Agent RAG System
- ✅ 7 Hukuk Dalı Desteği  
- ✅ PDF Otomatik İşleme
- ✅ Citation System
- ✅ Conversation History

## 🔧 Development

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn backend.main:app --reload

# Frontend
cd frontend && yarn install && yarn start
```

## 📁 Yapı

```
hukukyz/
├── backend/        # FastAPI + LangChain
├── frontend/       # React UI
├── docker-compose.yml
└── README.md
```

## ⚖️ Dikkat

Bu uygulama profesyonel hukuki danışmanlık yerine geçmez.
