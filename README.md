# SparkDeal — Türkiye Fiyat Takip Sistemi

Türkiye'deki e-ticaret, moda/spor ve oyun platformlarını takip eden; fiyat geçmişi tutan ve gerçek indirimleri analiz eden kişisel Flask uygulaması.

## Özellikler

- **Çoklu platform takibi** — Teknosa, Hepsiburada, N11, Steam ve daha fazlası
- **Fiyat geçmişi** — Her ürünün fiyat değişimi zaman içinde kaydedilir
- **Fırsat skoru** — Anlık indirime değil, geçmiş veriye dayalı analiz
- **En düşük fiyat tespiti** — 7 / 30 / 90 / 180 günlük en düşük ve ortalama
- **Alarm sistemi** — Hedef fiyat, tüm zamanların en düşüğü, kelime ve kategori alarmları
- **Otomatik tarama** — APScheduler ile periyodik scraping
- **Çapraz platform karşılaştırma** — Aynı ürünün farklı sitelerdeki fiyatları (yakında)

## Vertical'lar

| Vertical | Siteler |
|----------|---------|
| E-ticaret | Teknosa, Hepsiburada, N11, Amazon TR, Trendyol |
| Moda & Spor | Superstep ✅, Sneaksup ✅, Sneakersonline ✅, Bershka ❌, Pull&Bear ❌, H&M TR ❌ |
| Oyun | Steam ✅, Eneba, Oyunfor, Bynogame |

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

## Teknolojiler

- **Backend:** Python, Flask, SQLAlchemy, SQLite (WAL)
- **Scraping:** requests + BeautifulSoup, Playwright
- **Otomasyon:** APScheduler
- **Frontend:** Jinja2, HTML/CSS/JS (koyu tema)

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
| 8.5 | Fashion sitelerine sayfalama (Superstep 10 sayfa → 413 ürün) | ✅ |
| 8.5v2 | E-ticaret + oyun sitelerine sayfalama (N11 5 sayfa, Steam 10×2 URL → ~820 oyun) | ✅ |
| 9 | Oyun siteleri (Eneba, Oyunfor, Bynogame, Epic Games) + ITAD geçmişi | ⬜ |
| 10 | Çapraz platform fiyat karşılaştırması | ⬜ |
| 11 | Chart.js grafikleri | ⬜ |
| 12 | Ürün görselleri | ⬜ |
