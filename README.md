# SparkDeal — Türkiye Fiyat Takip Sistemi

Türkiye'deki e-ticaret, moda/spor ve oyun platformlarını takip eden; fiyat geçmişi tutan ve gerçek indirimleri analiz eden kişisel Flask uygulaması.

## Özellikler

- **Çoklu platform takibi** — Teknosa, Hepsiburada, N11, Steam, Epic Games ve daha fazlası
- **Fiyat geçmişi** — Her ürünün fiyat değişimi zaman içinde kaydedilir
- **Fırsat skoru** — Anlık indirime değil, geçmiş veriye dayalı analiz
- **En düşük fiyat tespiti** — 7 / 30 / 90 / 180 günlük en düşük ve ortalama
- **ITAD entegrasyonu** — Steam oyunları için yıllara geriye giden tarihsel fiyat geçmişi
- **Çapraz platform karşılaştırması** — Aynı ürünü farklı sitelerde ara, en ucuz platformu göster (/compare)
- **Rakip fiyat karşılaştırması** — Eneba ve Bynogame fiyatları gaming ürünlerinde gösterilir
- **Fiyat geçmişi grafikleri** — Chart.js ile interaktif fiyat çizgisi; düşüş noktaları yeşil, ITAD geçmişi turuncu noktalı
- **Dashboard sparkline'ları** — Her ürün kartında trend mini grafik
- **Alarm sistemi** — Hedef fiyat, tüm zamanların en düşüğü, kelime ve kategori alarmları
- **Otomatik tarama** — APScheduler ile periyodik scraping

## Vertical'lar

| Vertical | Siteler |
|----------|---------|
| E-ticaret | Teknosa, Hepsiburada ✅, N11 ✅, Amazon TR, Trendyol |
| Moda & Spor | Superstep ✅, Sneaksup ✅, Sneakersonline ✅, Bershka ❌, Pull&Bear ❌, H&M TR ❌ |
| Oyun | Steam ✅, Epic Games ✅, Eneba (karşılaştırma), Bynogame (karşılaştırma) |

❌ = Bot koruması nedeniyle devre dışı

## Kurulum

```bash
# Bağımlılıkları kur
pip install -r requirements.txt

# Playwright (JS tabanlı siteler için)
playwright install chromium

# Veritabanını oluştur
flask db upgrade

# Uygulamayı başlat
py run.py
```

Uygulama `http://127.0.0.1:5001` adresinde çalışır.

## Konfigürasyon

`.env` dosyası oluşturun (git'te takip edilmez):

```
ITAD_CLIENT_ID=...
ITAD_CLIENT_SECRET=...
ITAD_API_KEY=...
```

ITAD API key için: https://isthereanydeal.com/dev/

ITAD OAuth akışı (tek seferlik):
```bash
flask itad-auth              # Yetkilendirme URL'ini alın
flask itad-exchange <code>   # Kodu token'a çevirin
flask fetch-itad-history     # Tüm oyunlar için geçmiş çekin
```

## Teknolojiler

- **Backend:** Python, Flask, SQLAlchemy, SQLite (WAL)
- **Scraping:** requests + BeautifulSoup, Playwright
- **Otomasyon:** APScheduler
- **Frontend:** Jinja2, HTML/CSS/JS (koyu tema), Chart.js v4.4.3

## Yol Haritası

| Faz | İçerik | Durum |
|-----|--------|-------|
| 1 | Flask iskeleti + arayüz | ✅ |
| 2 | Veri modelleri | ✅ |
| 3 | Scraper altyapısı | ✅ |
| 4 | Fiyat analizi + fırsat skoru | ✅ |
| 5 | Otomasyon | ✅ |
| 6 | Alarm sistemi | ✅ |
| 7 | E-ticaret site genişlemesi (Playwright) | ✅ |
| 8 | Moda & Spor siteleri (Superstep, Sneaksup, Sneakersonline) | ✅ |
| 8.5 | Fashion sitelerine sayfalama | ✅ |
| 8.5v2 | E-ticaret + oyun sitelerine sayfalama | ✅ |
| 9 | Epic Games + Eneba/Bynogame karşılaştırma + ITAD | ✅ |
| 9.5 | ITAD OAuth akışı (authorization_code, token yönetimi) | ✅ |
| 10 | Çapraz platform fiyat karşılaştırması (/compare, Jaccard gruplama) | ✅ |
| 11 | Chart.js fiyat geçmişi grafikleri + dashboard sparklines | ✅ |
| 12 | Ürün görselleri (yerel indirme) | ⬜ |
| 13 | Fiyat toplayıcı: cimri.com + akakce.com | ⬜ |
| 14 | Yeni siteler: Boyner, Morhipo, MediaMarkt TR, Vatan vb. | ⬜ |
| 15 | Tasarım revizyonu (responsive, tema, UX) | ⬜ |
| 16 | Güvenlik + kurulum sihirbazı | ⬜ |
| 17 | Çoklu kullanıcı + admin paneli | ⬜ |
| 18 | Halka açılım hazırlığı (opsiyonel) | ⬜ |
| 19 | Mobil uygulama (PWA veya React Native) | ⬜ |
