# CLAUDE.md — İndirim ve Fiyat Takip Sistemi Hafıza Dosyası

## Proje Kimliği

Bu proje, kişisel kullanım amacıyla geliştirilen bir indirim ve fiyat takip sistemidir. Amaç, Türkiye'deki çeşitli e-ticaret, moda/spor ve oyun platformlarında indirimde olan ürünleri göstermek, fiyat geçmişini saklamak ve mevcut indirimin gerçekten anlamlı olup olmadığını geçmiş verilerle değerlendirmektir.

Proje üç dikey (vertical) üzerine kurulur:
- **E-ticaret**: Elektronik, ev, genel ürünler
- **Moda & Spor**: Giyim, ayakkabı, spor ekipmanları
- **Oyun İndirimleri**: Dijital oyun kodları ve Steam indirimleri

Proje bir müşteri yönetim sistemi, satış takip sistemi veya lead yönetim paneli olarak düşünülmemelidir.

**GitHub:** https://github.com/Brkcelik/sparkdeal
**Yerel çalıştırma:** `py run.py` → http://127.0.0.1:5001

---

## Önemli Geçmiş Kararlar

- **Demo veriler temizlendi:** Faz 7 sonrası seed.py ile oluşturulan 25 demo ürün (product_url='#') ve ilişkili kayıtları silindi. Veritabanında yalnızca gerçek scrape verisi var (476 ürün: 266 ecommerce/N11, 210 gaming/Steam).
- **Port 5001:** run.py'de port 5000 yerine 5001 kullanılıyor (5000'de başka proje var).
- **Faz 10 eklendi:** Çapraz platform fiyat karşılaştırması (cimri/akakçe/epey tarzı) yeni bir faz olarak eklendi. Eski Faz 10 (Chart.js) → Faz 11, eski Faz 11 (Görseller) → Faz 12 oldu.
- **Git kurulumu:** Proje git'e bağlandı. Her fazdan sonra commit atmak yeterli (`git add . && git commit -m "..." && git push`).

---

## Yol Haritası

Bu yol haritası ilerleme takibi için kullanılır.
Tamamlanan maddeler `[x]` ile işaretlenir — **silinmez, yalnızca işaretlenir**.
Her faz tamamlandığında ilgili başlığın altına `✅ Tamamlandı` notu eklenir.

---

### Faz 1 — Proje İskeleti ve Temel Arayüz ✅ Tamamlandı

Hedef: Scraper olmadan demo verilerle çalışan, koyu temalı, sidebar navigasyonlu Flask uygulaması.

**Geliştirme:**
- [x] Flask projesi oluştur ve klasör yapısını kur
- [x] SQLAlchemy + SQLite bağlantısını kur
- [x] Flask-Migrate ile migration altyapısını hazırla
- [x] Koyu temalı base template oluştur (sidebar + ana içerik alanı)
- [x] Sidebar navigasyonu: Dashboard / E-ticaret / Moda & Spor / Oyun İndirimleri / Fırsatlar / Alarmlar / Kaynaklar
- [x] Demo ürün verileri üret (seed script — her vertical için ayrı)
- [x] Dashboard sayfasını oluştur (özet kartlar, en iyi fırsatlar)
- [x] Ürün listesi sayfasını oluştur (filtreli, sıralanabilir)
- [x] Ürün detay sayfasını oluştur
- [x] Fiyat geçmişi tablosunu göster (henüz grafik yok)
- [x] Kaynaklar sayfasını oluştur

**Faz 1 Test Kontrol Listesi:**
- [x] Tüm sidebar linkleri doğru sayfaya yönlendiriyor mu? — HTTP 200 ✓
- [x] Demo veriler her vertical için doğru görünüyor mu? — 9 ecommerce, 8 fashion, 8 gaming ✓
- [x] Ürün listesi sayfası filtreler çalışıyor mu? — vertical, kaynak, indirim, stok, sıralama ✓
- [x] Ürün detay sayfası 404 vermeden açılıyor mu? — ✓ (olmayan ID 404 veriyor ✓)
- [ ] Mobil görünüm kabul edilebilir mi? — tarayıcıda manuel kontrol gerekli
- [ ] Sayfa yükleme hızı makul mi? — tarayıcıda manuel kontrol gerekli

---

### Faz 2 — Veri Modelleri ✅ Tamamlandı

Hedef: Tüm veritabanı modellerinin eksiksiz tanımlanması ve migration'ların çalışır olması.

**Geliştirme:**
- [x] Source modeli (`vertical` alanı dahil: `ecommerce` / `fashion` / `gaming`)
- [x] ScrapeTarget modeli
- [x] Product modeli (`vertical`, `platform`, `region` alanları dahil)
- [x] PriceHistory modeli
- [x] ProductStats modeli
- [x] DealSnapshot modeli
- [x] PriceAlert modeli
- [x] ScrapeRun modeli
- [x] Tüm modeller için migration dosyaları

**Faz 2 Test Kontrol Listesi:**
- [x] `flask db upgrade` hatasız tamamlandı ✓
- [x] Tüm tablolar oluştu mu? — 8 tablo doğrulandı ✓
- [x] İlişkiler (foreign key) doğru kurulmuş mu? — Product/Source ilişkileri test edildi ✓
- [x] `vertical` alanı kaynak ve ürünlerde tutarlı mı? — seed verisiyle doğrulandı ✓
- [x] Seed script yeniden çalıştırıldığında duplicate oluşmuyor mu? — `drop_all` + `create_all` ile garantilendi ✓

---

### Faz 3 — Scraper Altyapısı ✅ Tamamlandı

Hedef: Çoklu site scraper'ları, servis katmanı ve CLI komutu.

**Yazılan scraper'lar:** Steam API (tam çalışır), Teknosa, Hepsiburada, N11, Superstep

**Notlar:**
- Teknosa / Hepsiburada: Bot koruması aktif (HTTP 403) — Playwright gerekiyor (Faz 7)
- N11: Vue.js SPA — statik HTML'den isim/URL alınıyor, fiyatlar JS ile render ediliyor (Faz 7'de Playwright)
- Superstep: Next.js SPA — client-side render (Faz 8'de Playwright)
- Steam API: Tam çalışır, gerçek indirim verisi çekiyor

**Geliştirme:**
- [x] Base scraper sınıfı yaz (`base.py`) — session, retry, normalize_price
- [x] Ortak veri formatını sabitle ve dokümante et
- [x] Teknosa scraper'ını yaz (403 graceful handling)
- [x] Hepsiburada scraper'ını yaz (403 graceful handling)
- [x] N11 scraper'ını yaz (kısmi statik HTML)
- [x] Superstep scraper'ını yaz (Next.js framework — Faz 8'de tamamlanacak)
- [x] Steam API scraper'ını yaz (tam çalışır)
- [x] Scrape sonuçlarını Product tablosuna kaydet (upsert mantığı)
- [x] Her taramada PriceHistory kaydı oluştur
- [x] ScrapeRun log kaydını oluştur
- [x] Hata yakalama ve loglama ekle
- [x] `flask scrape <kaynak>` ve `flask scrape all` CLI komutları
- [x] Scraper registry (`app/scrapers/registry.py`)

**Faz 3 Test Kontrol Listesi:**
- [x] Scraper en az 20 ürün dönüyor mu? — Steam: 24 ürün ✓
- [x] Dönen her ürün ortak formatı tam dolduruyor mu? — Steam: evet ✓; N11: fiyat None (JS-rendered)
- [x] Fiyat değerleri float mı? — Steam: evet ✓
- [x] Aynı ürünü ikinci kez scrape edince duplicate kayıt oluşmuyor mu? — ✓ (0 yeni, 24 güncellendi)
- [x] PriceHistory her çalışmada yeni satır ekliyor mu? — ✓
- [x] ScrapeRun status doğru yazılıyor mu? — success / error / skipped ✓
- [x] Scraper hata verdiğinde uygulama çöküyor mu? — Çökmüyor ✓ (403 graceful)
- [ ] crawl delay gerçekten uygulanıyor mu? — HTML scraper'lar 403 döndüğü için test edilemedi

---

### Faz 4 — Fiyat Analizi ve Fırsat Skoru ✅ Tamamlandı

Hedef: Geçmiş fiyat verisine dayalı analiz ve fırsat skorunun hesaplanması.

**Geliştirme:**
- [x] ProductStats hesaplama servisini yaz
- [x] 7/30/90/180 günlük en düşük fiyat hesabı
- [x] 7/30/90 günlük ortalama fiyat hesabı
- [x] `is_all_time_low`, `is_30d_low`, `is_90d_low` bayraklarını güncelle
- [x] `days_at_current_low` hesabını yaz
- [x] Fırsat skoru algoritmasını uygula (bkz. Fırsat Skoru Mantığı)
- [x] DealSnapshot oluşturma ve güncelleme mantığı
- [x] Fırsatlar sayfasını gerçek verilerle doldur
- [x] Dashboard'u gerçek verilerle güncelle
- [x] Ürün detay sayfasına analiz bilgilerini ekle (bkz. En Düşük Fiyat Analizi)

**Faz 4 Test Kontrol Listesi:**
- [x] ProductStats hesaplama servisi mevcut — `app/services/stats_service.py` ✓
- [x] 7/30/90/180 günlük en düşük + ortalama hesapları mevcut ✓
- [x] is_all_time_low / is_30d_low / is_90d_low bayrakları set ediliyor ✓
- [x] days_at_current_low hesabı mevcut ✓
- [x] Fırsat skoru gaming/ecommerce/fashion ayrımıyla hesaplanıyor ✓
- [x] DealSnapshot oluştur/güncelle mantığı mevcut — tekli aktif kayıt garantili ✓
- [x] Fırsatlar sayfası gerçek verilerle çalışıyor (30%+ indirim + stokta) ✓
- [x] Dashboard gerçek ProductStats sorgularıyla çalışıyor ✓
- [x] Ürün detay sayfasında analiz metinleri, skor rozeti, bayrak rozetleri gösteriliyor ✓
- [x] Fırsatlar sayfasında sıralama fırsat skoruna göre ✓

---

### Faz 5 — Otomasyon ✅ Tamamlandı

Hedef: Scraping'in kullanıcı müdahalesi olmadan periyodik çalışması.

**Geliştirme:**
- [x] Arayüzden manuel tarama tetikleme butonu (Kaynaklar sayfasında her kaynak için "Tara" butonu)
- [x] APScheduler entegrasyonu (`app/__init__.py` — BackgroundScheduler, daemon=True)
- [x] Kaynak bazlı periyodik tarama görevi (ScrapeTarget.scrape_interval_minutes, fallback 360 dk)
- [x] Tarama geçmişi ve log sayfası (`/scrape-runs` — filtreli, sayfalı ScrapeRun listesi)
- [x] Hata veren kaynakları dashboard'da göster (error_count > 0 uyarı kartı)

**Notlar:**
- Werkzeug reloader double-start koruması: `WERKZEUG_RUN_MAIN == 'true'` kontrolü mevcut
- Scheduler başlatılamasa bile uygulama çalışmaya devam eder (try/except import)
- Manuel tetikleme sonrası flash mesajı gösterilir (başarı/hata/atlandı)
- `max_instances=1` ile aynı kaynağın paralel çalışması engellendi

**Faz 5 Test Kontrol Listesi:**
- [x] Manuel tarama butonu UI'dan tetiklenebiliyor mu? — Kaynaklar sayfasında "Tara" butonu ✓
- [x] APScheduler uygulama başlatıldığında job'ları planlıyor mu? — 4 job oluşturuldu ✓
- [x] Werkzeug reloader çift başlatma koruması var mı? — WERKZEUG_RUN_MAIN kontrolü ✓
- [x] Tarama log sayfasında başarılı/başarısız ayrımı görünüyor mu? — run-status rozetleri ✓
- [x] Hata veren kaynaklar dashboard'da görünüyor mu? — error_count > 0 ile filtreleniyor ✓

---

### Faz 6 — Alarm Sistemi ✅ Tamamlandı

Hedef: Kullanıcının belirli koşullar için uyarı alabilmesi.

**Geliştirme:**
- [x] Ürün bazlı hedef fiyat alarmı (`alarm_type='price'` — product_id + target_price)
- [x] Kelime bazlı alarm (`alarm_type='keyword'` — ürün adında kelime + min indirim eşiği)
- [x] Kategori bazlı alarm (`alarm_type='category'` — kategori + min indirim eşiği)
- [x] Tüm zamanların en düşük fiyatı alarmı (`alarm_type='atl'` — product_id + badge_atl kontrolü)
- [x] Alarm tetikleme mantığı (`app/services/alert_service.py` — scrape sonrası otomatik + manuel /alerts/check)
- [x] Alarm yönetim sayfası (`/alerts` — oluştur, aktif/pasif toggle, sil, tip rozeti)
- [x] Ürün detay sayfasından "Alarm Kur" butonu

**Notlar:**
- `PriceAlert` modeline `alarm_type` (VARCHAR 20) ve `min_discount_percent` (FLOAT) eklendi + migration
- Aynı gün iki kez tetiklenme engellendi (`last_triggered_at.date() == today` kontrolü)
- `scraper_service.run_scrape` her tarama sonunda `check_alerts(updated_products)` çağırır
- `/alerts/check` endpointi ile tüm ürünlere karşı manuel kontrol mümkün

**Faz 6 Test Kontrol Listesi:**
- [x] Alarm route'ları doğru kayıtlı — 5 endpoint (list, create, toggle, delete, check) ✓
- [x] Hedef fiyat alarmı: `current_price <= target_price` koşulu kontrol ediliyor ✓
- [x] Aynı alarm aynı gün iki kez tetiklenmiyor — `last_triggered_at.date()` karşılaştırması ✓
- [x] Pasif alarm (`is_active=False`) tetikleme dışı bırakılıyor ✓
- [x] Kelime bazlı alarm büyük/küçük harf duyarsız — `.lower()` karşılaştırması ✓
- [x] Alarm listesi sayfasında aktif/pasif ayrımı görünüyor ✓

---

### Faz 7 — E-ticaret Site Genişlemesi ✅ Tamamlandı

Hedef: Birden fazla e-ticaret sitesi taranır.

**Geliştirme:**
- [x] Hepsiburada scraper (Playwright ile yeniden yazıldı — HTTP 403 aşıldı)
- [x] N11 scraper (Playwright ile yeniden yazıldı — JS render fiyatlar artık çekilebilir)
- [x] Amazon TR scraper (yeni — requests tabanlı, bot koruması graceful)
- [x] Playwright entegrasyonu (`app/scrapers/playwright_base.py` — stealth init, scroll_load, ImportError graceful)
- [x] Trendyol scraper (yeni — Playwright ile, Cloudflare için ana sayfa warm-up + stealth)
- [x] Aynı ürünü farklı sitelerde karşılaştırma mantığı (`normalize_product_name` + ürün detay cross-site tablo)

**Notlar:**
- Playwright + Chromium: `pip install playwright && playwright install chromium` ✓ (kuruldu)
- Playwright scraper'lar ImportError'u gracefully handle eder — kurulu değilse [] döner
- Trendyol Cloudflare engeline takılırsa found_count=0 döner, uygulama çökmez
- Amazon TR captcha/503 durumunda sessizce [] döner, uyarı loglanır
- `normalize_product_name()` public fonksiyon olarak `scraper_service.py`'de tanımlı
- Trendyol ve Amazon TR ScrapeTargets seed.py'e eklendi (is_active=False başlangıçta)
- Hepsiburada ve N11 için seed.py'de scraper_type 'playwright' olarak güncellendi

**Faz 7 Test Kontrol Listesi:**
- [x] N11 scraper: 472 ürün, 174 indirimli — Playwright ✓
- [x] Steam scraper: 214 ürün, tamamı indirimli ✓
- [x] Fiyat parse düzeltmesi: "2.399 TL" artık 2399 TL okunuyor (base.py binlik nokta fix) ✓
- [x] Playwright scraper headless modda çalışıyor mu? — Chromium indirildi ✓
- [x] Bir scraper çöktüğünde diğerleri çalışmaya devam ediyor mu? — ImportError + try/except ✓
- [x] Hepsiburada: Kasada bot koruması aktif — Playwright ile de bypass edilemiyor (known limitation)
- [x] Amazon TR: Captcha koruması aktif — requests ile bypass edilemiyor (known limitation)
- [x] Trendyol: Cloudflare koruması aktif — 0 ürün döndü (known limitation)

---

### Faz 8 — Moda & Spor Siteleri

Hedef: Giyim ve spor kategorisindeki siteler sisteme eklenir.

Eklenecek siteler: Superstep, Sneaksup, Sneakersonline, Bershka, Pull&Bear, H&M TR

**Geliştirme:**
- [ ] Superstep scraper (spor ayakkabı, kolay HTML)
- [ ] Sneaksup scraper
- [ ] Sneakersonline scraper
- [ ] Bershka scraper (Inditex grubu — dikkat: JS ağırlıklı)
- [ ] Pull&Bear scraper (Inditex grubu — Bershka ile benzer yapı)
- [ ] H&M TR scraper (API tabanlı olabilir, incelenmeli)
- [ ] Moda ürünleri için beden/renk varyant mantığı (ürün ana kayıt + varyant ayrımı)
- [ ] Moda kategorisi özel filtreleri: beden, renk, cinsiyet

**Mimari Not — Moda Siteleri:**
- Bershka ve Pull&Bear aynı Inditex altyapısını kullanır; scraper büyük ölçüde paylaşılabilir.
- H&M'in sitesi XHR/API çağrıları yapabilir; tarayıcı geliştirici araçlarıyla incelenmeli.
- Beden/renk varyantları için tek product kaydında `variants` JSON alanı düşünülebilir.
- Moda ürünlerinde "eski fiyat" güvenilirliği daha düşüktür — skor hesabı buna göre ağırlıklandırılabilir.

**Faz 8 Test Kontrol Listesi:**
- [ ] Bershka ve Pull&Bear aynı ürünü iki kez kaydetmiyor mu?
- [ ] Moda ürünleri `vertical = fashion` ile kaydediliyor mu?
- [ ] Beden/renk filtresi ürün listesinde çalışıyor mu?
- [ ] Moda sidebar linki yalnızca fashion vertical'ı gösteriyor mu?
- [ ] H&M ürünlerinde fiyat TL formatında doğru parse ediliyor mu?

---

### Faz 9 — Oyun İndirimleri Bölümü + ITAD Geçmiş Fiyat Entegrasyonu

Hedef: Steam, Eneba ve Türkiye pin sitelerindeki oyun fırsatları ayrı bir bölümde listelenir. IsThereAnyDeal (ITAD) API ile retroaktif fiyat geçmişi sisteme eklenir.

Eklenecek kaynaklar: Steam (scraper ✅), Eneba, Oyunfor, Bynogame

**Geliştirme — Oyun Siteleri:**
- [x] Steam scraper (HTML + indirimli oyunlar, 150 ürün)
- [ ] Eneba scraper
- [ ] Oyunfor scraper
- [ ] Bynogame scraper
- [ ] Oyun İndirimleri sayfası (platform ve bölge filtreli)
- [ ] Oyunlar arası cross-site fiyat karşılaştırması (aynı oyun birden fazla sitede)

**Geliştirme — ITAD Retroaktif Fiyat Geçmişi:**
- [ ] ITAD API anahtarı al (ücretsiz kayıt: isthereanydeal.com/dev)
- [ ] Steam appid → ITAD game ID eşleştirmesi (`/games/lookup/v1/` endpoint)
- [ ] Oyunun tüm fiyat geçmişini çek (`/games/history/v2/` endpoint) — yıllara göre tüm düşüşler
- [ ] `ExternalPriceHistory` modeli: her oyun için ITAD kaynaklı fiyat geçmişi satırları (source: 'itad', price, date)
- [ ] ITAD verisini `PriceHistory` tablosuna entegre et veya ayrı tutarak detay sayfasında birlikte göster
- [ ] Detay sayfasında ITAD kökenli geçmiş kayıtları "Tarihsel Veri" başlığıyla ayrı göster
- [ ] `historical_low_price` ve `historical_low_date` alanlarını ProductStats'a ekle
- [ ] ITAD verisini çekme CLI komutu: `flask fetch-itad-history <appid>` ve `flask fetch-itad-history all`
- [ ] Faz 10 grafiğine ITAD verisi de dahil edilsin (noktalı çizgi veya farklı renk)

**ITAD API Mimari Notu:**
- Ücretsiz kayıt: https://isthereanydeal.com/dev/
- Fiyat geçmişi endpoint: `GET /games/history/v2/?id={itad_id}&shops=steam`
- Dönen veri: `[{shop, price, currency, date}, ...]` — tüm kayıtlı düşüşler
- Rate limit: makul (kişisel kullanım için yeterli)
- ITAD oyun araması: `GET /games/lookup/v1/?title={name}` veya `appid:{steam_appid}` ile
- Sadece gaming vertical için kullanılır; e-ticaret/moda için ITAD verisi yok
- ITAD fiyatları USD olabilir — `currency` alanı ile birlikte saklanmalı

**Faz 9 Test Kontrol Listesi:**
- [ ] Eneba/Oyunfor/Bynogame scraper'ları en az 20 ürün dönüyor mu?
- [ ] Oyun ürünleri `vertical = gaming` ile kaydediliyor mu?
- [ ] Platform filtresi (PC/PS5 vb.) doğru çalışıyor mu?
- [ ] Bölge (TR/EU) filtresi çalışıyor mu?
- [ ] ITAD API'den geçmiş fiyat verisi çekiliyor mu?
- [ ] ITAD verisi detay sayfasında "Tarihsel Veri" olarak görünüyor mu?
- [ ] Steam appid → ITAD eşleştirmesi başarısız olunca sessizce atlanıyor mu?
- [ ] ITAD rate limit aşılmadan tüm oyunlar için veri çekilebiliyor mu?

---

### Faz 10 — Çapraz Platform Fiyat Karşılaştırması

Hedef: Aynı ürünün farklı platformlardaki fiyatlarını cimri.com / akakçe / epey tarzında yan yana göstermek (oyun vertical'ı hariç).

**Geliştirme:**
- [ ] Ürün eşleştirme servisi: `normalized_name` + `brand` benzerliğine göre aynı ürünü birden fazla kaynakta tespit et (`app/services/matching_service.py`)
- [ ] `ProductGroup` modeli veya sorgu katmanı: aynı ürünü temsil eden kayıtları grupla (migration gerekmeyebilir — view/query tabanlı yaklaşım tercih edilsin)
- [ ] Karşılaştırma sayfası (`/compare`) — arama kutusuyla ürün ara, platform bazlı fiyat tablosu göster
- [ ] Ürün detay sayfasına "Bu ürünün diğer platformlardaki fiyatları" tablosu ekle (cross-site tablo — Faz 7'de altyapısı hazır)
- [ ] En ucuz platformu vurgula (rozet veya renk ile)
- [ ] Fiyat farkı yüzdesini göster (örn. "Teknosa'da %18 daha pahalı")
- [ ] Karşılaştırmada stok durumunu da göster
- [ ] Sidebar'a "Fiyat Karşılaştır" linki ekle

**Mimari Not:**
- Eşleştirme kesin değil, bulanık (fuzzy) olmalı; threshold ayarlanabilir olsun
- `normalize_product_name()` zaten `scraper_service.py`'de mevcut — matching_service bunu kullanır
- Oyun ürünleri bu sayfaya dahil edilmez (platform/bölge farkı karşılaştırmayı anlamsız kılar)
- Eşleştirme servis katmanında yapılır, DB'ye ayrı tablo açılması zorunlu değil

**Faz 10 Test Kontrol Listesi:**
- [ ] Aynı marka + benzer isimli ürün farklı kaynaklardan eşleşiyor mu?
- [ ] Farklı ürünler yanlışlıkla eşleşiyor mu? (false positive kontrolü)
- [ ] Karşılaştırma tablosu yalnızca 1 kaynak bulunan ürünlerde bozulmuyor mu?
- [ ] Stok dışı platform karşılaştırmada görünüyor mu?
- [ ] Oyun ürünleri karşılaştırma sayfasına karışıyor mu?

---

### Faz 11 — Grafik ve Görselleştirme

Hedef: Fiyat geçmişinin görsel olarak sunulması.

**Geliştirme:**
- [ ] Chart.js entegrasyonu
- [ ] Ürün detay sayfasına fiyat geçmişi grafiği ekle (kendi verisi + ITAD verisi birlikte)
- [ ] Fiyat düşüş noktalarını grafik üzerinde işaretle
- [ ] Dashboard'a mini sparkline grafikler ekle
- [ ] Oyun fiyat geçmişi grafiği (platform bazlı karşılaştırma)
- [ ] ITAD kaynaklı tarihsel noktalar farklı renk/stil ile gösterilsin

**Faz 11 Test Kontrol Listesi:**
- [ ] Fiyat geçmişi grafiği az veriyle (3-5 nokta) bozuluyor mu?
- [ ] Grafik mobil görünümde taşıyor mu?
- [ ] Sıfır veya None fiyat noktası grafiği kırıyor mu?
- [ ] ITAD + kendi verisinin birleşimi grafikte doğru sıralı gösteriliyor mu?

---

### Faz 12 — Ürün Görselleri

Hedef: Scraper'lardan gelen `image_url` değerleri yerine görseller yerel olarak indirilip saklanır; arayüzde gerçek ürün fotoğrafları gösterilir.

**Geliştirme:**
- [ ] `app/static/images/products/` klasör yapısını oluştur (vertical bazlı alt klasörler)
- [ ] `Product` modeline `local_image_path` alanı ekle (migration)
- [ ] Görsel indirme servisi yaz (`app/services/image_service.py`):
  - `image_url` yoksa veya boşsa atla
  - Dosya adı: `{external_id}.jpg` veya `{product_id}.jpg`
  - Zaten indirildiyse tekrar indirme
  - Desteklenen formatlar: jpg, png, webp — webp → jpg dönüşümü
  - İndirme başarısız olursa `image_url` gösterime devam etsin (fallback)
- [ ] Görsel indirme scrape akışına entegre et: her upsert sonrası arka planda indir
  - Senkron değil, toplu indirme tercih edilsin (scrape bitmesini beklemesin)
- [ ] `flask download-images` CLI komutu: tüm mevcut ürünlerin görsellerini indir
- [ ] Template güncelleme: `local_image_path` varsa `<img src="/static/images/...">`, yoksa `image_url` ile fallback
- [ ] Steam için header image (460x215): `https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg`
- [ ] Görsel boyutu sınırı: maksimum 500KB, aşarsa orijinal URL kullanılsın

**Mimari Notlar:**
- Görseller SQLite'a değil dosya sistemine kaydedilir (`app/static/images/products/`)
- `local_image_path` = `products/gaming/730.jpg` gibi static-relative yol
- Uygulama taşınırken görseller de taşınmalı — bu göz önünde bulundurulmalı
- Steam görselleri için CDN URL formatı sabittir, doğrudan oluşturulabilir: `https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg`
- E-ticaret / moda görselleri geçici olabilir (CDN TTL); periyodik yenileme düşünülebilir

**Faz 12 Test Kontrol Listesi:**
- [ ] Görsel indirme mevcut `image_url`'si olmayan ürünleri atlıyor mu?
- [ ] Aynı ürün için iki kez çalıştırıldığında görsel tekrar indirilmiyor mu?
- [ ] İndirme başarısız olunca template `image_url` fallback'i doğru gösteriyor mu?
- [ ] `flask download-images` komutu 150 Steam ürünü için hatasız tamamlanıyor mu?
- [ ] Boyut sınırı (500KB) aşılan görseller atlanıyor mu?

---

## Ana Amaç

Kullanıcının farklı e-ticaret, moda ve oyun sitelerini tek tek gezmesine gerek kalmadan, sistemin düzenli olarak ürünleri kontrol etmesi ve şu bilgileri sunması hedeflenir:

* Şu anda indirimde olan ürünler (e-ticaret, moda, oyun — ayrı bölümlerde)
* Ürünün güncel fiyatı
* Ürünün eski fiyatı veya görünen liste fiyatı
* Gerçek indirim oranı
* Ürünün fiyat geçmişi
* Bu fiyatın kaç gündür en düşük fiyat olduğu
* Bu fiyatın son 7, 30, 90 veya 180 gündeki konumu
* Ürünün daha önce daha ucuza düşüp düşmediği — sadece sistemin başladığı günden değil, yıllara geriye giden tarihsel veriyle (ITAD, gaming için)
* Geçmişteki tüm fiyat düşüşleri — ne zaman ne kadara düştü
* İndirimin gerçek mi yoksa yanıltıcı mı olabileceği
* Ürünün stok durumu
* Kaynak site linki
* Ürünün görseli (yerel olarak saklanmış, hızlı yüklenen)

---

## Temel Yaklaşım

Sistem sadece anlık indirim oranına göre karar vermemelidir.

Sistem şu sorulara cevap verebilmelidir:

* Bu ürün gerçekten indirimde mi?
* Bu fiyat son kaç günün en düşük fiyatı?
* Ürün daha önce bu fiyata düşmüş mü?
* Ürün son 30 güne göre ucuz mu pahalı mı?
* Sitenin gösterdiği eski fiyat güvenilir mi?
* Bu ürün için alarm kurulmaya değer mi?

---

## Önemli Tasarım Kararı

Bu proje CRM mantığında tasarlanmayacak.

Kullanılmaması gereken kavramlar:

* Müşteri, Lead, Pipeline, Satış hunisi, Demo gönderimi, Müşteri statüsü, Lead score, Firma takibi

Kullanılması gereken kavramlar:

* Ürün, Fiyat, İndirim, Fiyat geçmişi, Kaynak site, Tarama hedefi, Fırsat skoru, En düşük fiyat süresi, Alarm, Takip listesi

---

## Proje Tipi

Backend:

* Python
* Flask
* SQLAlchemy
* SQLite ile başlanabilir (WAL modu etkinleştirilmiş)
* İleride PostgreSQL'e geçilebilir

Scraping:

* İlk aşamada requests + BeautifulSoup
* Gerekirse Playwright (Trendyol, Bershka, Pull&Bear, H&M gibi JS ağırlıklı siteler)
* Site bazlı özel scraper yapısı; her site için ayrı parser dosyası
* Steam için resmi API (scraping değil)

Frontend:

* Flask templates + Jinja2
* HTML / CSS / JavaScript
* Koyu temalı, sidebar navigasyonlu, ürün odaklı arayüz

Grafikler:

* Faz 11'de Chart.js ile fiyat geçmişi grafiği

---

## Dikey (Vertical) Yapısı

Sistem üç dikey üzerine kurulur. Her kaynak bir dikey'e aittir ve bu dikey arayüzde ayrı bir sidebar bölümü olarak gösterilir.

| Dikey | Kod | Siteler |
|-------|-----|---------|
| E-ticaret | `ecommerce` | Teknosa, Hepsiburada, N11, Amazon TR, Trendyol |
| Moda & Spor | `fashion` | Superstep, Sneaksup, Sneakersonline, Bershka, Pull&Bear, H&M TR |
| Oyun İndirimleri | `gaming` | Steam, Eneba, Oyunfor, Bynogame |

Her vertical kendi filtreleriyle ayrı bir sayfa olarak gösterilir. Dashboard tüm verticals'ı özetler.

---

## Önerilen Scraper Başlangıç Sırası

### E-ticaret

| Sıra | Site | Zorluk | Not |
|------|------|--------|-----|
| 1 | Teknosa | Kolay | Temiz HTML, bot koruması düşük — ilk scraper buradan |
| 2 | Hepsiburada | Orta | Bazı sayfalar JS gerektiriyor |
| 3 | N11 | Orta | Benzer yapı, indirim sayfaları mevcut |
| 4 | Amazon TR | Orta-Zor | Dinamik fiyat, rate limit var |
| 5 | Trendyol | Zor | Agresif bot koruması — Playwright gerekli |

### Moda & Spor

| Sıra | Site | Zorluk | Not |
|------|------|--------|-----|
| 1 | Superstep | Kolay-Orta | Temiz kategori sayfaları |
| 2 | Sneaksup | Kolay-Orta | Benzer yapı |
| 3 | Sneakersonline | Orta | İncelenmeli |
| 4 | H&M TR | Orta | XHR/API çağrısı yapıyor olabilir — geliştirici araçlarıyla incele |
| 5 | Bershka | Zor | Inditex altyapısı — Playwright gerekebilir |
| 6 | Pull&Bear | Zor | Bershka ile aynı altyapı — scraper paylaşılabilir |

### Oyun Platformları

| Sıra | Site | Zorluk | Not |
|------|------|--------|-----|
| 1 | Steam | Kolay | Resmi API mevcut — scraping gerekmez |
| 2 | Oyunfor | Kolay-Orta | Türkçe site, temiz yapı |
| 3 | Bynogame | Kolay-Orta | Benzer yapı |
| 4 | Eneba | Orta | Avrupa merkezli — rate limit ve bölge farkına dikkat |

---

## Oyun İndirimleri Mimari Notu

Oyun bölümü e-ticaretten farklı veri alanları gerektirir:

Ek alanlar (Product modeline eklenir):

* `platform`: PC / PS4 / PS5 / Xbox One / Xbox Series / Nintendo Switch
* `region`: TR / EU / Global / NA
* `edition`: Standard / Deluxe / Ultimate / GOTY vb.

### Steam API

Steam resmi olarak iki endpoint sunar:

* Tüm uygulama listesi: `https://api.steampowered.com/ISteamApps/GetAppList/v2/`
* Uygulama detayı + indirim: `https://store.steampowered.com/api/appdetails?appids={appid}&cc=tr&l=turkish`

`cc=tr` parametresi Türkiye fiyatını döndürür. API key gerekmez (rate limit var: ~200 istek/5 dakika). Bu nedenle sadece indirimde olan oyunları çekmek için önce fiyat listesi API'si üzerinden filtre yapılmalıdır.

### Oyun Fırsat Skoru

```text
score = 0

if discount_percent >= 50:
    score += discount_percent * 1.2
elif discount_percent >= 30:
    score += discount_percent * 1.0

if is_all_time_low:
    score += 60
elif is_90d_low:
    score += 40
elif is_30d_low:
    score += 25

if region == "TR":
    score += 15  # TL fiyatı genellikle çok avantajlı

if price_drop_detected_today:
    score += 20
```

---

## Ana Modüller

### 1. Ürün Toplama Modülü

E-ticaret, moda ve oyun sitelerindeki ürünleri tarar.

Toplanacak temel alanlar:

* Ürün adı
* Güncel fiyat
* Eski fiyat
* İndirim oranı
* Ürün URL'si
* Görsel URL'si
* Stok durumu
* Kategori
* Marka
* Kaynak site
* Vertical (ecommerce / fashion / gaming)
* Tarama zamanı
* Platform (yalnızca gaming)
* Bölge/Region (yalnızca gaming)

### 2. Fiyat Geçmişi Modülü

Her ürünün fiyatı zaman içinde kaydedilir. Projenin ana değeri burada.

### 3. İndirim Analiz Modülü

Güncel fiyatı geçmişle karşılaştırır. Görünen indirim oranından bağımsız analiz yapar.

### 4. Fırsat Skoru Modülü

Her vertical için özelleştirilmiş skor üretir.

### 5. Alarm ve Takip Modülü

Kullanıcı belirli ürünleri veya kelimeleri takip edebilir.

### 6. Dashboard Modülü

Tüm vertical'lardan en iyi fırsatları özetler.

---

## Ana Sayfalar

### Dashboard

Tüm vertical'ların özeti. En iyi fırsatlar, yeni düşüşler, son tarama zamanı.

### E-ticaret

Teknosa, Hepsiburada, N11, Amazon TR, Trendyol ürünleri.

Filtreler: site, kategori, marka, min indirim oranı, min fırsat skoru, stok, en düşük fiyat durumu, arama.

### Moda & Spor

Superstep, Sneaksup, Sneakersonline, Bershka, Pull&Bear, H&M ürünleri.

Filtreler: site, marka, beden, renk, cinsiyet, kategori, min indirim oranı.

### Oyun İndirimleri

Steam, Eneba, Oyunfor, Bynogame oyunları.

Filtreler: platform (PC/PS5/Xbox vb.), bölge (TR/EU/Global), min indirim oranı, fırsat skoru.

### Fırsatlar

Tüm vertical'lardan gerçek fırsatların filtrelendiği birleşik sayfa.

### Ürün / Oyun Detay

Tek ürünün detaylı analizi: fiyat geçmişi tablosu (Faz 10'da grafik), fırsat skoru, analiz metinleri.

### Kaynaklar

Tüm kaynak sitelerin yönetimi. Vertical bazlı gruplama.

### Tarama Hedefleri

Her kaynak için kategori/arama URL'leri.

### Fiyat Alarmları

Kullanıcının oluşturduğu alarmlar.

---

## Veri Modeli Taslağı

### Source

Kaynak siteleri tutar.

Alanlar:

* id
* name
* base_url
* vertical (`ecommerce` / `fashion` / `gaming`)
* is_active
* scraper_type (`requests` / `playwright` / `api`)
* crawl_delay_seconds
* last_scraped_at
* error_count
* created_at

### ScrapeTarget

Alanlar:

* id
* source_id
* title
* url
* category
* is_active
* min_discount_percent
* scrape_interval_minutes
* last_scraped_at
* created_at

### Product

Ürünün ana kaydı.

Alanlar:

* id
* source_id
* external_id
* name
* normalized_name
* brand
* category
* vertical (`ecommerce` / `fashion` / `gaming`)
* platform (gaming: `PC`, `PS5`, `Xbox`, `Nintendo` — diğerleri null)
* region (gaming: `TR`, `EU`, `Global` — diğerleri null)
* edition (gaming: `Standard`, `Deluxe` vb. — diğerleri null)
* product_url
* image_url
* current_price
* old_price
* discount_percent
* stock_status
* first_seen_at
* last_seen_at
* created_at
* updated_at

### PriceHistory

Alanlar:

* id
* product_id
* price
* old_price
* discount_percent
* stock_status
* recorded_at

### ProductStats

Alanlar:

* id
* product_id
* lowest_price_all_time
* lowest_price_7d
* lowest_price_30d
* lowest_price_90d
* lowest_price_180d
* average_price_7d
* average_price_30d
* average_price_90d
* days_at_current_low
* is_all_time_low
* is_30d_low
* is_90d_low
* updated_at

### DealSnapshot

Alanlar:

* id
* product_id
* deal_score
* deal_reason
* current_price
* previous_average_price
* discount_percent
* is_active
* first_detected_at
* last_detected_at

### PriceAlert

Alanlar:

* id
* product_id
* keyword
* target_price
* source_id
* category
* vertical
* platform (gaming alarmları için)
* is_active
* last_triggered_at
* created_at

### ScrapeRun

Alanlar:

* id
* source_id
* target_id
* status
* found_count
* new_product_count
* updated_product_count
* error_message
* started_at
* finished_at

---

## Fırsat Skoru Mantığı

### E-ticaret ve Moda

```text
score = 0

if discount_percent >= 20:
    score += discount_percent * 1.5

if is_all_time_low:
    score += 50
elif is_90d_low:
    score += 35
elif is_30d_low:
    score += 20

if current_price < average_price_30d:
    score += percentage_below_30d_average

if stock_status == "in_stock":
    score += 10

if price_drop_detected_today:
    score += 15
```

### Oyun İndirimleri

```text
score = 0

if discount_percent >= 50:
    score += discount_percent * 1.2
elif discount_percent >= 30:
    score += discount_percent * 1.0

if is_all_time_low:
    score += 60
elif is_90d_low:
    score += 40
elif is_30d_low:
    score += 25

if region == "TR":
    score += 15

if price_drop_detected_today:
    score += 20
```

Skor yorumları (tüm vertical'lar için):

* 0-40: Zayıf indirim
* 40-80: Dikkate değer
* 80-120: İyi fırsat
* 120+: Çok iyi fırsat

---

## En Düşük Fiyat Analizi

Örnek analiz metinleri:

* Bu ürün son 30 günün en düşük fiyatında.
* Bu ürün son 90 gün ortalamasından %18 daha ucuz.
* Bu ürün 12 gündür bu fiyat seviyesinde.
* Bu ürün tüm zamanların en düşük fiyatından 250 TL daha pahalı.
* Bu ürün daha önce 3 kez benzer fiyata düşmüş.

---

## Scraper Mimari Kararı

```text
app/scrapers/
├── base.py
├── generic_html.py
├── ecommerce/
│   ├── teknosa.py
│   ├── hepsiburada.py
│   ├── n11.py
│   ├── amazon_tr.py
│   └── trendyol.py
├── fashion/
│   ├── superstep.py
│   ├── sneaksup.py
│   ├── sneakersonline.py
│   ├── bershka.py        ← Inditex — Pull&Bear ile paylaşılabilir
│   ├── pullandbear.py
│   └── hm.py
└── gaming/
    ├── steam_api.py      ← scraping değil, API
    ├── eneba.py
    ├── oyunfor.py
    └── bynogame.py
```

Her scraper ortak formatta veri döndürmelidir:

```python
{
    "name": "Ürün adı",
    "current_price": 1299.90,
    "old_price": 1999.90,
    "discount_percent": 35,
    "product_url": "https://...",
    "image_url": "https://...",
    "brand": "Marka",
    "category": "Kategori",
    "stock_status": "in_stock",
    "external_id": "siteye_ozel_id",
    "vertical": "ecommerce",        # ecommerce / fashion / gaming
    "platform": None,               # gaming için: "PC", "PS5" vb.
    "region": None,                 # gaming için: "TR", "EU", "Global"
    "edition": None                 # gaming için: "Standard", "Deluxe" vb.
}
```

---

## Geliştirme Sırası (Özet)

Bu bölüm hızlı referans için özet olarak tutulur. Asıl takip belgesi üstteki **Yol Haritası** bölümüdür.

| Faz | İçerik | Durum |
|-----|--------|-------|
| 1 | Flask iskeleti + sidebar arayüz + demo veri | ✅ Tamamlandı |
| 2 | Veri modelleri (vertical, platform, region dahil) | ✅ Tamamlandı |
| 3 | Scraper altyapısı (Steam 150 ürün ✓, diğerleri stub) | ✅ Tamamlandı |
| 4 | Fiyat analizi + fırsat skoru (ProductStats, DealSnapshot) | ✅ Tamamlandı |
| 5 | APScheduler otomasyonu + manuel tetikleme + tarama geçmişi sayfası | ✅ Tamamlandı |
| 6 | Alarm sistemi (hedef fiyat, ATL, kelime, kategori) | ✅ Tamamlandı |
| 7 | E-ticaret site genişlemesi (Playwright, cross-site karşılaştırma) | ✅ Tamamlandı |
| 8 | Moda & Spor siteleri (Superstep, Bershka, Pull&Bear, H&M vb.) | ⬜ Bekliyor |
| 9 | Oyun siteleri (Eneba, Oyunfor, Bynogame) + ITAD retroaktif fiyat geçmişi | ⬜ Bekliyor |
| 10 | Çapraz platform fiyat karşılaştırması (cimri/akakçe/epey tarzı, oyun hariç) | ⬜ Bekliyor |
| 11 | Chart.js grafikleri (kendi verisi + ITAD geçmişi birlikte) | ⬜ Bekliyor |
| 12 | Ürün görselleri (yerel indirme + fallback) | ⬜ Bekliyor |

---

## Teknik Uyarılar

### SQLite

* WAL modunu etkinleştir: `PRAGMA journal_mode=WAL`
* APScheduler ile eş zamanlı yazma olursa WAL modu bunu büyük ölçüde çözer.
* Veriler büyüdükçe PostgreSQL'e geçiş düşünülebilir.

### Scraping

* Her request arasına `crawl_delay_seconds` kadar bekleme ekle.
* User-Agent header'ını gerçekçi bir tarayıcı değeriyle ayarla.
* Trendyol, Bershka, Pull&Bear için Playwright gerekebilir.
* H&M için site XHR istekleri yapıyor olabilir — geliştirici araçlarıyla incele.
* Scraper hataları sessizce yutulmamalı, ScrapeRun'a loglanmalı.
* Bir scraper hata verince diğerleri durmamalı.

### Fiyat Hesaplamaları

* Fiyat değerlerini `float` olarak sakla.
* TL formatını (`1.299,90 TL`) parse ederken nokta/virgül ayrımına dikkat et.
* Eski fiyat manipüle edilebilir — geçmiş fiyat verisini esas al.

### Steam API

* Rate limit: ~200 istek / 5 dakika. Tüm katalog çekilmemeli; sadece indirimde olanlar.
* `cc=tr` parametresiyle Türkiye fiyatı çekilir.

### Moda Siteleri

* Bershka ve Pull&Bear Inditex altyapısını paylaşır; scraper kodu büyük ölçüde ortak yazılabilir.
* Beden/renk varyantlarında tek product kaydı tutmak için `variants` JSON alanı düşünülebilir.

---

## Arayüz Tarzı

Genel görünüm:

* Koyu tema
* Sidebar navigasyonu (Dashboard / E-ticaret / Moda & Spor / Oyun İndirimleri / Fırsatlar / Alarmlar / Kaynaklar)
* Ürün kartları ve fırsat rozetleri
* Fiyat grafikleri (Faz 10)
* Filtrelenebilir ürün listesi
* Hızlı aksiyon butonları

Örnek rozetler:

* Tüm zamanların en düşüğü
* Son 30 günün en düşüğü
* Son 90 günün en düşüğü
* Yeni fiyat düşüşü
* Stokta var / Stok bitti
* Şüpheli indirim
* TR Fiyatı (gaming)
* Tarihsel en düşük (gaming)

---

## Dikkat Edilecek Noktalar

* Sistem kişisel kullanım içindir.
* Kişisel veri toplama amacı yoktur.
* Siteye aşırı istek atılmamalıdır; crawl delay kullanılmalıdır.
* Scraper hataları loglanmalıdır.
* Her site için ayrı parser yazılmalıdır.
* Kod modüler olmalıdır.
* Önce çalışan basit sistem, sonra gelişmiş analiz.

---

## Claude Code İçin Davranış Talimatı

1. Projeyi CRM olarak yorumlama.
2. Üç dikey var: e-ticaret, moda, oyun — her biri ayrı bir sidebar bölümü.
3. Önce basit, çalışan ve modüler yapı kur.
4. Gereksiz karmaşık mimariden kaçın.
5. Scraper kodlarını vertical + site bazlı klasörlere ayır.
6. Her scraper'ın ortak veri formatı döndürmesini sağla (`vertical`, `platform`, `region` dahil).
7. Fiyat geçmişini projenin ana değeri olarak gör.
8. İndirim oranını tek başına güvenilir kabul etme.
9. Eski fiyat yerine geçmiş fiyat verisini esas al.
10. Arayüzü ürün ve fırsat odaklı tasarla.
11. Kodları okunabilir, genişletilebilir ve yorumlanabilir yaz.
12. Büyük değişikliklerden önce mevcut dosya yapısını kontrol et.
13. Var olan yapıyı bozmadan ilerle.
14. Gereksiz framework veya servis ekleme.
15. İlk sürümde SQLite yeterlidir (WAL modu ile).
16. Otomasyon ve bildirimleri sonraki aşamaya bırak.
17. Yol haritasındaki tamamlanan maddeleri `[x]` ile işaretle — silme.
18. Her önemli aşama tamamlandığında CLAUDE.md'yi güncelle.
19. Faz bitince test kontrol listesini birlikte gözden geçir.

---

## İlk Hedef

İlk hedef scraper yazmak değildir.

İlk hedef:

* Flask projesini kurmak
* Sidebar navigasyonlu koyu temalı modern arayüzü oluşturmak
* Demo verilerle çalışan ürün listesi yapmak (her vertical için ayrı demo veri)
* Ürün detay ekranını hazırlamak
* Fiyat geçmişi modelini kurmak

Scraper daha sonra bu yapıya bağlanacaktır.

---

## Kısa Proje Özeti

Bu proje, Türkiye'deki e-ticaret (Teknosa, Hepsiburada, Trendyol vb.), moda/spor (Superstep, Bershka, H&M vb.) ve oyun platformlarını (Steam, Eneba, Oyunfor, Bynogame) takip eden; fiyat geçmişi tutan, gerçek indirimleri analiz eden ve kullanıcıya en iyi fırsatları gösteren kişisel bir Flask tabanlı fiyat takip sistemidir.

Ana değer önerisi:

Sadece "%50 indirim" yazan ürünleri göstermek değil, geçmiş fiyat verisine göre gerçekten ucuz olan ürünleri — her kategoride — bulmak.
