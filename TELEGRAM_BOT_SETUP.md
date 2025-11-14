# HukukYZ Telegram Bot Kurulum ve Kullanım

## 📱 Bot Bilgileri

- **Bot Adı:** HukukYZ_bot
- **Platform:** Telegram
- **Özellikler:** Hukuki soru-cevap, Madde referansları, İçtihat bilgisi

## 🚀 Kurulum Adımları

### 1. Bot Token Alma

1. Telegram'da [@BotFather](https://t.me/botfather) bot'una gidin
2. `/newbot` komutunu gönderin
3. Bot adını girin: `HukukYZ Bot`
4. Bot kullanıcı adını girin: `HukukYZ_bot` (veya uygun bir alternatif)
5. BotFather size bir **token** verecek (örnek: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Token'ı Yapılandırma

`.env` dosyasına token'ı ekleyin:

```bash
TELEGRAM_BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
```

### 3. Bot'u Başlatma

#### Development (Polling Mode):
```bash
cd /app
python3 backend/scripts/start_telegram_bot.py
```

#### Production (Webhook Mode):
```bash
python3 backend/scripts/start_telegram_bot.py \
  --webhook https://yourdomain.com/telegram-webhook \
  --port 8080
```

## 📋 Bot Komutları

### Kullanıcı Komutları

| Komut | Açıklama | Örnek |
|-------|----------|-------|
| `/start` | Bot'u başlat | `/start` |
| `/help` | Yardım menüsü | `/help` |
| `/ask <soru>` | Hukuki soru sor | `/ask TTK m.11 ne diyor?` |
| `/history` | Son 5 soruyu gör | `/history` |
| `/clear` | Geçmişi temizle | `/clear` |

### Direkt Mesaj
Komut kullanmadan doğrudan soru yazabilirsiniz:
```
Anonim şirket nasıl kurulur?
```

## 💬 Kullanım Örnekleri

### Örnek 1: Basit Soru
```
Kullanıcı: /ask Limited şirket nedir?

Bot: 
📖 Cevap:
Limited şirket, bir veya daha fazla gerçek veya tüzel kişi tarafından 
kurulabilen, sermayesi esas sermayeye bölünmüş, ortakların sorumluluğu 
koydukları sermaye ile sınırlı olan ticaret şirketidir.

🟢 Güven: 85%

📚 Kaynaklar:
1. TTK m.573 (Türk Ticaret Kanunu)
2. TTK m.574 (Türk Ticaret Kanunu)
```

### Örnek 2: Madde Referansı
```
Kullanıcı: TTK m.11

Bot:
📖 Cevap:
TTK Madde 11'e göre, anonim şirket bir veya daha fazla gerçek veya 
tüzel kişi tarafından kurulabilir...

🟢 Güven: 92%
```

### Örnek 3: Geçmiş Görme
```
Kullanıcı: /history

Bot:
📜 Son Sorularınız:

1. TTK m.11 ne diyor?
   🕐 2024-11-14T10:30:00

2. Anonim şirket nasıl kurulur?
   🕐 2024-11-14T10:25:00

3. Limited şirket nedir?
   🕐 2024-11-14T10:20:00
```

## 🔧 Teknik Detaylar

### Bot Mimarisi

```
Telegram User
     ↓
Telegram Bot API
     ↓
HukukYZBot Handler
     ↓
Workflow Engine
     ↓
Backend APIs
     ↓
Qdrant + MongoDB
```

### Özellikler

✅ **Async Processing**: Hızlı yanıt süreleri
✅ **Session Management**: Kullanıcı bazlı oturum takibi
✅ **History Tracking**: MongoDB'de soru geçmişi
✅ **Cache Support**: Redis ile hızlı yanıtlar
✅ **Rich Formatting**: Markdown desteği
✅ **Error Handling**: Güvenilir hata yönetimi
✅ **Inline Buttons**: Etkileşimli menüler

### Mesaj Limitleri

- Telegram mesaj limiti: 4096 karakter
- Bot otomatik olarak uzun cevapları parçalara böler
- Her sorgu maksimum 3 dakika içinde cevaplanır

### Rate Limiting

Telegram Bot API limitleri:
- 30 mesaj/saniye (grup başına)
- 20 mesaj/dakika (kullanıcı başına)

## 🐛 Sorun Giderme

### Bot Yanıt Vermiyor
```bash
# Log kontrolü
tail -f /var/log/supervisor/telegram_bot.log

# Servisi yeniden başlat
sudo supervisorctl restart telegram_bot
```

### Token Hatası
```
❌ Error: Telegram Bot Token not provided!
```
**Çözüm:** `.env` dosyasında `TELEGRAM_BOT_TOKEN` tanımlı mı kontrol edin.

### Bağlantı Hatası
```
❌ Service initialization failed
```
**Çözüm:** MongoDB ve Redis servislerinin çalıştığından emin olun:
```bash
sudo service mongodb status
sudo service redis-server status
```

## 📊 Monitoring

### Bot İstatistikleri
```python
# MongoDB'den kullanım istatistikleri
db.telegram_history.aggregate([
  { $group: { 
      _id: "$user_id", 
      count: { $sum: 1 } 
  }}
])
```

### Aktif Kullanıcılar
```python
# Son 24 saatte aktif kullanıcılar
from datetime import datetime, timedelta
yesterday = datetime.now() - timedelta(days=1)

db.telegram_history.distinct("user_id", {
  "timestamp": { "$gte": yesterday.isoformat() }
})
```

## 🔐 Güvenlik

### Token Güvenliği
- ❌ Token'ı asla public repository'de paylaşmayın
- ✅ Environment variable olarak saklayın
- ✅ `.env` dosyasını `.gitignore`'a ekleyin

### Kullanıcı Gizliliği
- Kullanıcı bilgileri MongoDB'de şifrelenmeli
- Soru geçmişi kullanıcı isteğiyle silinebilir
- GDPR/KVKK uyumlu veri saklama

## 🚀 Production Deployment

### Webhook Kurulumu (Önerilen)

1. **SSL sertifikası gereklidir**
2. **Public URL gereklidir**

```bash
# Webhook set et
curl -F "url=https://yourdomain.com/telegram-webhook" \
     https://api.telegram.org/bot<TOKEN>/setWebhook

# Bot'u webhook mode'da başlat
python3 backend/scripts/start_telegram_bot.py \
  --webhook https://yourdomain.com/telegram-webhook \
  --port 8080
```

### Supervisor ile Otomatik Başlatma

`/etc/supervisor/conf.d/telegram_bot.conf`:
```ini
[program:telegram_bot]
directory=/app
command=/usr/local/bin/python3 backend/scripts/start_telegram_bot.py
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/telegram_bot.err.log
stdout_logfile=/var/log/supervisor/telegram_bot.out.log
```

Başlat:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start telegram_bot
```

## 📈 Gelecek Özellikler

- [ ] Görsel (image) destekli cevaplar
- [ ] PDF belge gönderme
- [ ] Sesli mesaj desteği
- [ ] Çoklu dil desteği
- [ ] Premium kullanıcı özellikleri
- [ ] Bot analytics dashboard

## 📞 Destek

Sorun yaşıyorsanız:
1. Bu dokümantasyonu kontrol edin
2. Log dosyalarını inceleyin
3. GitHub Issues'da bildirin

---

**Not:** Bu bot genel bilgi amaçlıdır. Kesin hukuki tavsiye için avukata danışınız.
