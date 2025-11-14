# 🚀 HukukYZ Telegram Bot - Hızlı Başlangıç

## Adım 1: Bot Oluştur

1. **Telegram'ı Aç** (Mobil veya Desktop)

2. **BotFather'ı Ara:**
   - Arama kutusuna yazın: `@BotFather`
   - Veya direkt linke tıklayın: https://t.me/botfather

3. **Yeni Bot Oluştur:**
   ```
   /start
   /newbot
   ```

4. **Bot İsmi Gir:**
   ```
   HukukYZ Bot
   ```
   (Bu isim kullanıcılara görünecek)

5. **Bot Username Gir:**
   ```
   HukukYZ_bot
   ```
   veya başka bir username (boştaysa)
   - Username sonunda 'bot' olmalı
   - Benzersiz olmalı (eğer alınmışsa farklı deneyin: HukukYZ_assistant_bot)

6. **Token'ı Kopyala:**
   BotFather size şöyle bir token verecek:
   ```
   7654321098:AAHfB3XyZ9QWErTyUiOpLkJhGfDsSaQwErTy
   ```
   ⚠️ BU TOKEN'I SAKLAYIN! Sadece size verilir.

## Adım 2: Token'ı Sisteme Ekle

### Yöntem 1: Manuel Ekleme
```bash
# .env dosyasını düzenle
nano /app/backend/.env

# Bu satırı bul ve token'ı yapıştır:
TELEGRAM_BOT_TOKEN="BURAYA_TOKEN_YAPIŞTIR"

# Ctrl+X, Y, Enter ile kaydet
```

### Yöntem 2: Komut ile Ekleme
```bash
# Eski satırı sil ve yeni token ekle
sed -i 's/TELEGRAM_BOT_TOKEN=".*"/TELEGRAM_BOT_TOKEN="YOUR_ACTUAL_TOKEN"/' /app/backend/.env
```

## Adım 3: Bot'u Başlat

### Test Modu (Geliştirme):
```bash
cd /app
PYTHONPATH=/app python3 backend/scripts/start_telegram_bot.py
```

### Başarılı Başlangıç Çıktısı:
```
🚀 HukukYZ Telegram Bot Starting...
============================================================
📦 Connecting to MongoDB...
✅ MongoDB connected
🔄 Connecting to Redis cache...
✅ Redis connected
🔄 Starting in POLLING mode (development)
🤖 Starting HukukYZ_bot...
✅ Telegram bot application built
✅ HukukYZ_bot is running!
```

## Adım 4: Bot'u Test Et

### Test 1: /start Komutu
1. Telegram'da bot'unuzu arayın: `@HukukYZ_bot` (veya kullandığınız username)
2. "START" butonuna tıklayın veya `/start` yazın
3. Hoş geldin mesajı görmeli ve 3 buton görmeli:
   - 📝 Soru Sor
   - 📚 Yardım
   - 📊 Hakkında

### Test 2: Direkt Soru
```
Anonim şirket nedir?
```

Beklenen Cevap:
```
🔍 Sorgunuz işleniyor...
⏳ Lütfen bekleyin...

[5-10 saniye sonra]

📖 Cevap:
Anonim şirket, bir ticaret unvanı altında kurulan...

🟢 Güven: 85%

📚 Kaynaklar:
1. TTK m.329 (Türk Ticaret Kanunu)
```

### Test 3: Komut ile Soru
```
/ask Limited şirket kaç kişi ile kurulur?
```

### Test 4: Geçmiş Kontrolü
```
/history
```

## ❌ Sorun Giderme

### Problem 1: "Bot is not responding"
**Kontrol:**
```bash
# Bot çalışıyor mu?
ps aux | grep telegram_bot

# Log'lara bak
tail -f /tmp/telegram_bot.log
```

**Çözüm:** Bot'u yeniden başlat

### Problem 2: "Unauthorized"
**Neden:** Token yanlış veya geçersiz

**Kontrol:**
```bash
# Token'ı göster (ilk 20 karakter)
grep TELEGRAM_BOT_TOKEN /app/backend/.env | cut -c1-40
```

**Çözüm:** Token'ı BotFather'dan tekrar kopyala

### Problem 3: "Connection refused"
**Neden:** MongoDB veya Redis çalışmıyor

**Kontrol:**
```bash
sudo service mongodb status
sudo service redis-server status
```

**Çözüm:**
```bash
sudo service mongodb start
sudo service redis-server start
```

### Problem 4: Bot yavaş yanıt veriyor
**Normal:** İlk sorgu 10-15 saniye sürebilir (cache'leme yok)
**İkinci sorgu:** 3-5 saniye (cache var)

## 🔍 Debug Log'ları

### Bot Log'larını İzle:
```bash
# Bot çalışırken başka bir terminalde
tail -f /var/log/supervisor/telegram_bot.log

# Veya direkt script çıktısını izle (eğer manuel başlattıysanız)
```

### MongoDB Log'larını İzle:
```bash
# Telegram history kayıtları
mongo hukukyz --eval "db.telegram_history.find().pretty()"
```

## 📊 Test Senaryoları

### Senaryo 1: Basit Soru
```
User: Borçlu ödeme yapmazsa ne olur?
Expected: [TBK maddeleri ile cevap]
```

### Senaryo 2: Madde Referansı
```
User: TTK m.11
Expected: [TTK Madde 11 tam metni]
```

### Senaryo 3: Karmaşık Soru
```
User: Anonim şirket kurmak için hangi belgeler gerekir?
Expected: [Detaylı cevap + çoklu referanslar]
```

### Senaryo 4: Geçmiş
```
User: /history
Expected: [Son 5 soru listesi]
```

### Senaryo 5: Temizleme
```
User: /clear
Expected: "✅ X adet soru geçmişiniz temizlendi."
```

## 🎯 Başarı Kriterleri

✅ Bot /start'a cevap veriyor
✅ Hoş geldin mesajı görünüyor
✅ Inline butonlar çalışıyor
✅ Direkt mesajlar işleniyor
✅ /ask komutu çalışıyor
✅ Cevaplar 15 saniye içinde geliyor
✅ Kaynaklar gösteriliyor
✅ Güven skoru görünüyor
✅ /history çalışıyor
✅ /clear çalışıyor

## 🚀 Production'a Alırken

### 1. Supervisor ile Otomatik Başlatma
```bash
sudo nano /etc/supervisor/conf.d/telegram_bot.conf
```

İçerik:
```ini
[program:telegram_bot]
directory=/app
command=/usr/local/bin/python3 backend/scripts/start_telegram_bot.py
environment=PYTHONPATH="/app"
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/telegram_bot.err.log
stdout_logfile=/var/log/supervisor/telegram_bot.out.log
user=root
```

Başlat:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start telegram_bot
sudo supervisorctl status telegram_bot
```

### 2. Webhook Mode (Production)
```bash
python3 backend/scripts/start_telegram_bot.py \
  --webhook https://yourdomain.com/telegram-webhook \
  --port 8080
```

## 📞 Hızlı Yardım

### Bot durumu kontrol:
```bash
sudo supervisorctl status telegram_bot
```

### Bot'u yeniden başlat:
```bash
sudo supervisorctl restart telegram_bot
```

### Son 50 log satırı:
```bash
tail -50 /var/log/supervisor/telegram_bot.out.log
```

### Bot çalışıyor mu?
```bash
ps aux | grep start_telegram_bot
```

---

**Sorun devam ederse:** Log dosyalarını paylaşın, beraber inceleyelim!
