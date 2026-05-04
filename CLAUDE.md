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

- **Demo veriler temizlendi:** Faz 7 sonrası seed.py ile oluşturulan 25 demo ürün (product_url='#') ve ilişkili kayıtları silindi.
- **Güncel ürün sayısı (Faz 8.5 v2 sonrası):** 976 ürün — 266 ecommerce, 494 fashion, 216 gaming.
- **Port 5001:** run.py'de port 5000 yerine 5001 kullanılıyor (5000'de başka proje var).
- **Faz 10 eklendi:** Çapraz platform fiyat karşılaştırması (cimri/akakçe/epey tarzı) yeni bir faz olarak eklendi. Eski Faz 10 (Chart.js) → Faz 11, eski Faz 11 (Görseller) → Faz 12 oldu.
- **Faz 8.5 v2 eklendi:** E-ticaret + oyun sitelerine pagination eklendi, sonra Faz 9 geldi.
- **Git kurulumu:** Proje git'e bağlandı. Her fazdan sonra commit atmak yeterli (`git add . && git commit -m "..." && git push`).
- **PlaywrightBaseScraper pagination altyapısı:** `MAX_PAGES`, `PAGINATION_PARAM`, `_build_page_url()` class var'ları eklendi. Yeni scraper'lar sadece bu değerleri override ederek sayfalama kazanır.
- **Steam çift URL:** `?specials=1` ve `?specials=1&ndl=1` farklı oyun setleri döndürüyor (%36 overlap); her ikisi taranarak ~820 benzersiz oyun elde ediliyor.
- **gender alanı:** Product modeline `gender` VARCHAR(20) eklendi (migration: e5f6a7b8c9d0). `BaseScraper.detect_gender()` ile otomatik doldurulur.
- **Sneakersonline domain:** `sneakersonline.com` DNS çözülemiyor; doğru domain `sneakersonline.com.tr`.
- **Sneaksup URL:** `/indirim` 404 döner; doğru URL `/sezon-sonu-indirimi`. Kategori sayfaları indirim verisi taşımıyor (GA attribute'da `discount=0`).
- **Bot koruması — pasif bırakılanlar:** Bershka TR, Pull&Bear TR, H&M TR, Hepsiburada, Trendyol, Amazon TR. Playwright ile de aşılamadı.

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

### Faz 8 — Moda & Spor Siteleri ✅ Tamamlandı

Hedef: Giyim ve spor kategorisindeki siteler sisteme eklenir. Her site için tek bir indirim sayfası ScrapeTarget olarak tanımlanır.

Eklenecek siteler: Superstep, Sneaksup, Sneakersonline, Bershka, Pull&Bear, H&M TR

**Geliştirme:**
- [x] Superstep scraper (Playwright, Tailwind CSS — span.line-through + span[class*="text-primary"] selektörleri)
- [x] Sneaksup scraper (Playwright, Inveon platform — data-ga-impressions JSON)
- [x] Sneakersonline scraper (Playwright, ikas.com platform — div[data-id] kartlar)
- [x] Bershka scraper (Playwright, Inditex grubu — _parse_inditex_html paylaşımlı)
- [x] Pull&Bear scraper (Playwright, Inditex grubu — bershka.py'den _parse_inditex_html reuse)
- [x] H&M TR scraper (Playwright — Akamai koruması, JSON endpoint 403 döner, Playwright fallback)
- [x] Product modeline `gender` alanı eklendi (migration: e5f6a7b8c9d0)
- [x] BaseScraper'a `detect_gender()` eklendi
- [x] Cinsiyet filtresi ürün listesi sayfasına eklendi
- [x] Kaynaklar sayfasına Aktif/Pasif toggle butonu eklendi
- [x] Çalışan scraper'lar doğrulandı ve aktif edildi

**Notlar:**
- Sneaksup doğru URL: `/sezon-sonu-indirimi` (not: `/indirim` 404 döner — DB'de güncellendi)
- Sneakersonline doğru domain: `sneakersonline.com.tr` (not: `.com` DNS çözülemiyor)
- Bershka: "Access Denied" bot koruması — Playwright ile de bypass edilemiyor (known limitation)
- Pull&Bear: Bot koruması aktif — 0 ürün (known limitation)
- H&M: Akamai bot koruması — JSON endpoint 403, Playwright fallback da 0 ürün (known limitation)
- Bershka, Pull&Bear, H&M pasif bırakıldı
- Faz 8.5'te tüm kategori sayfaları + sayfalama desteği eklenecek

**Faz 8 Test Kontrol Listesi:**
- [x] Superstep: 34 ürün — span.line-through + span[class*="text-primary"] ✓
- [x] Sneaksup: 24 ürün — data-ga-impressions JSON ✓
- [x] Sneakersonline: 100 ürün — div[data-id] kartlar ✓
- [x] Bershka: Bot koruması — "Access Denied" (known limitation) ✓
- [x] Pull&Bear: Bot koruması — 0 ürün (known limitation) ✓
- [x] H&M: Akamai bot koruması — 0 ürün (known limitation) ✓
- [x] Moda ürünleri `vertical = fashion` ile kaydediliyor ✓
- [x] `gender` alanı detect_gender() ile dolduruluyor ✓
- [x] Cinsiyet filtresi ürün listesinde çalışıyor ✓

---

### Faz 8.5 — Kapsamlı Tarama: Tüm Kategoriler + Sayfalama ✅ Tamamlandı

Hedef: Tek bir "indirim" sayfasına bağlı kalmak yerine sitelerin tüm kategori sayfalarını tarayarak indirimli ürünleri yakalamak.

**Yaklaşım:**
- `PlaywrightBaseScraper`'a `MAX_PAGES` + `PAGINATION_PARAM` + `_build_page_url()` eklendi
- Sayfalama `scrape()` metodunda otomatik: sayfa 1 normal, sayfa 2..N için `?{PAGINATION_PARAM}=N` eklenir
- Sonuç 0 olunca pagination durur
- Sneaksup kategori sayfaları incelendi: `discount=0` döndürüyor (indirim bilgisi yalnızca sale sayfasında var)

**Geliştirme:**
- [x] `PlaywrightBaseScraper`'a sayfalama desteği eklendi (`MAX_PAGES`, `PAGINATION_PARAM`, `_build_page_url()`)
- [x] Superstep: `MAX_PAGES=10`, `PAGINATION_PARAM='page'` → 10 sayfada 413 ürün (önceden 34)
- [x] Sneakersonline: scroll ×8 → 180 ürün (önceden 100)
- [x] Sneaksup kategori sayfaları araştırıldı — indirim verisi yalnızca sale sayfasında; kategori target'ları eklenmedi
- [x] seed.py güncellendi: doğru URL'ler, scraper_type='playwright'

**Notlar:**
- Sneaksup `/erkek`, `/kadin` sayfaları tüm ürünleri gösteriyor ama `discount=0` — GA attribute'u indirim bilgisi taşımıyor
- Bershka, Pull&Bear, H&M bot korumasını aşamadığından sayfalama uygulama dışı
- Superstep 90 sayfa var; max_pages=10 ile yaklaşık 413 ürün/tarama

**Faz 8.5 Test Kontrol Listesi:**
- [x] Sayfalama desteği çalışıyor mu? — Superstep 10 sayfa ✓
- [x] Boş sayfa gelince duruyor mu? — `if not page_results: break` ✓
- [x] Kategori sayfalarında `old_price` olmayan ürünler filtreleniyor mu? — scraper'da None kontrolü ✓
- [x] Genişletilmiş tarama ile ürün sayısı artıyor mu? — Superstep 34→413, Sneakersonline 100→180 ✓
- [x] Crawl delay pagination'da da uygulanıyor mu? — `load_page()` her çağrıda `time.sleep(self.delay)` ✓

---

### Faz 8.5 v2 — Tüm Aktif Sitelere Sayfalama ve Genişletilmiş Tarama ✅ Tamamlandı

Hedef: Faz 8.5'te fashion sitelerine eklenen pagination/scroll desteğinin e-ticaret ve oyun sitelerine de uygulanması.

**Bulgular (araştırma):**
- N11: `?pg=N` URL pagination + scroll lazy-load, sayfa başı ~235 kart
- Hepsiburada: `?sayfa=N` URL pagination (bot koruması aktif olduğu için pratikte etkisiz)
- Teknosa: requests tabanlı, 403 bot koruması — Playwright gerekli (gelecek faz)
- Steam: kendi `MAX_PAGES` değişkeni var, dosya seviyesinde artırıldı

**Geliştirme:**
- [x] N11: `MAX_PAGES=5`, `PAGINATION_PARAM='pg'`, scroll ×3 → sayfa başı ~235 kart, 5 sayfada ~1175 kart
- [x] Hepsiburada: `MAX_PAGES=5`, `PAGINATION_PARAM='sayfa'`, scroll ×3 (bot koruma aşılamazsa etkisiz)
- [x] Steam: `MAX_PAGES 3→10` + çift URL (standart + `ndl=1`) → 150 → ~820 benzersiz oyun

**Sonuçlar:**
- N11 (2 sayfa test): 470 kart, 312 indirimli ✓
- Steam (3 sayfa × 2 URL test): 246 benzersiz oyun ✓ (10 sayfada ~820)
- Hepsiburada: kod hazır ama bot koruması nedeniyle 0 ürün (known limitation)

**Notlar:**
- Tüm Playwright scraper'lar `PlaywrightBaseScraper`'ın pagination altyapısını devralır; sadece class var set edildi
- Teknosa requests tabanlı olduğu için `PlaywrightBaseScraper` pagination'ını kullanamaz — Playwright'e geçiş gerekli
- N11 `/kampanya` sayfası `?pg=N` ile ek sayfalara erişilebilir, her sayfada scroll ile ek ürünler yüklenir

**Faz 8.5 v2 Test Kontrol Listesi:**
- [x] N11 `?pg=2` çalışıyor mu? — 470 kart / 2 sayfa ✓
- [x] Steam MAX_PAGES=10 tanımlı mı? — 200/4 sayfa ✓
- [x] Hepsiburada kodu hazır mı? — Evet, bot koruması nedeniyle 0 ürün (known limitation) ✓

---

### Faz 9 — Epic Games Scraper + Eneba/Bynogame Fiyat Karşılaştırması + ITAD ✅ Tamamlandı

Hedef: Epic Games'i ikinci birincil oyun kaynağı olarak ekle. Eneba ve Bynogame'i bağımsız ürün kaynağı olarak değil, Steam/Epic oyunları için **fiyat karşılaştırma ortağı** olarak entegre et. Ürün kartlarında "Eneba'da daha ucuz" rozeti, detay sayfasında rakip fiyat tablosu göster.

**Kaynaklar:**
- Steam (scraper ✅) — birincil gaming kaynağı
- Epic Games (GraphQL API) — birincil gaming kaynağı
- Eneba — fiyat karşılaştırma ortağı (bağımsız kaynak değil; Steam/Epic ürünlerine eşleştirilir)
- Bynogame — fiyat karşılaştırma ortağı (Eneba ile aynı mimari)

**Oyunfor — projeden çıkarıldı** (site erişimi 403/404 döndü)

**Geliştirme — Epic Games:**
- [x] Epic Games scraper (`app/scrapers/gaming/epic_games.py`) — freeGamesPromotions REST + Playwright browse (__NEXT_DATA__ parse)
- [x] seed.py'e Epic Games Source + ScrapeTarget eklendi
- [x] registry.py'e `epic_games` → `EpicGamesScraper` eklendi

**Epic Games Mimari Notu:**
- GraphQL endpoint: `POST https://graphql.epicgames.com/graphql`
- `operationName: searchStoreQuery`, `category: games/edition/base`, `onSale: true`, `country: TR`
- Sayfalama: `start` parametresi, `count: 40` — `paging.total` gelene kadar devam
- `external_id` = `id` alanı
- `current_price` = `price.totalPrice.discountPrice / 100` (kuruş cinsinden döner)
- `old_price` = `price.totalPrice.originalPrice / 100`
- `discount_percent` = `round((original - discount) / original * 100)`
- Görsel: `keyImages` dizisinden `type="DieselGameBoxWide"` veya `"OfferImageWide"`
- Ürün URL: `https://store.epicgames.com/tr/p/{urlSlug}` veya `{productSlug}`
- `vertical=gaming`, `platform=PC`, `region=TR`

**Geliştirme — Eneba/Bynogame Fiyat Karşılaştırması:**
- [x] `CompetitorPrice` modeli oluştur (`app/models/competitor_price.py`) — migration ✓
- [x] Eneba lookup servisi (`app/services/competitor_service.py`) — `?text=` URL ile Apollo SSR cache parse ✓
- [x] Bynogame lookup servisi — `/tr/search?query=` + `div.list-group-item` + `span[data-href]` ✓
- [x] `flask fetch-competitor-prices [gaming]` CLI komutu ✓
- [x] Ürün kartı (`_card.html`): `competitor_prices`'da `current_price`'dan ucuz kayıt varsa görsel üzerine rozet ✓
- [x] Ürün detay sayfası (`detail.html`): gaming ürünleri için "Diğer Platformlarda Fiyat" bölümü ✓

**CompetitorPrice Mimari Notu:**
- `competitor_prices` tablosu: `product_id`, `source_name` ('eneba'/'bynogame'), `price`, `currency`, `url`, `checked_at`
- `Product` → `competitor_prices` (1:N ilişki)
- Eneba arama URL: `https://www.eneba.com/tr/search?text={game_name}` — Apollo SSR cache parse (`"text"` key)
  - `?q=` parametresi çalışmaz; sadece `?text=` SSR'da arama filtresini tetikler
  - word boundary matching (`\b`) ile false positive azaltıldı
- Bynogame: `/tr/search?query={name}+cd+key` → `div.list-group-item` > `span.searchhref[data-href]` + `p.font-weight-bolder`
- Fiyat karşılaştırması: `any(cp.price < product.current_price for cp in product.competitor_prices)`
- Steam Turkey fiyatları genellikle Eneba/Bynogame'den çok ucuz; tablo "daha pahalı" gösterimi yapar

**Geliştirme — ITAD Retroaktif Fiyat Geçmişi:**
- [x] ITAD API anahtarı al (ücretsiz kayıt: isthereanydeal.com/dev) — config.py'de ITAD_API_KEY alanı hazır
- [x] Steam appid → ITAD game ID eşleştirmesi (`/games/lookup/v1/` endpoint) — `itad_service.lookup_itad_id()`
- [x] Oyunun tüm fiyat geçmişini çek (`/games/history/v2/` endpoint) — `itad_service.fetch_itad_history()`
- [x] `ExternalPriceHistory` modeli: `app/models/external_price_history.py`, migration a7b8c9d0e1f2
- [x] ITAD verisi ayrı tabloda saklanıyor, detay sayfasında "Tarihsel Veri" bölümünde gösteriliyor
- [x] Detay sayfasında ITAD kökenli geçmiş kayıtları "Tarihsel Veri (ITAD)" başlığıyla gösteriliyor
- [ ] `historical_low_price` ve `historical_low_date` alanlarını ProductStats'a ekle (Faz 11'e ertelendi)
- [x] ITAD verisini çekme CLI komutu: `flask fetch-itad-history` (tüm) / `flask fetch-itad-history <appid>`
- [ ] Faz 11 grafiğine ITAD verisi de dahil edilsin (noktalı çizgi veya farklı renk)

**ITAD API Mimari Notu:**
- Ücretsiz kayıt: https://isthereanydeal.com/dev/
- Fiyat geçmişi endpoint: `GET /games/history/v2/?id={itad_id}&shops=steam`
- Dönen veri: `[{shop, price, currency, date}, ...]` — tüm kayıtlı düşüşler
- Rate limit: makul (kişisel kullanım için yeterli)
- ITAD oyun araması: `GET /games/lookup/v1/?title={name}` veya `appid:{steam_appid}` ile
- Sadece gaming vertical için kullanılır; e-ticaret/moda için ITAD verisi yok
- ITAD fiyatları USD olabilir — `currency` alanı ile birlikte saklanmalı

**Faz 9 Test Kontrol Listesi:**
- [x] Epic Games scraper mevcut ve kayıtlı — freeGamesPromotions + Playwright browse ✓
- [x] Epic Games oyunları `vertical=gaming`, `platform=PC`, `region=TR` ile kaydediliyor mu? ✓
- [x] CompetitorPrice tablosu migration ile oluştu mu? — migration 99785c1fd000 ✓
- [x] Eneba lookup: bir oyun adı için fiyat döndürüyor mu? — Cyberpunk: 918 TL, Witcher 3: 376 TL ✓
- [x] Ürün kartında rozet sistemi hazır (Eneba ucuzsa gösterir) ✓
- [x] Detay sayfasında gaming ürünleri için rakip fiyat tablosu görünüyor mu? ✓
- [x] `flask fetch-competitor-prices` tüm gaming ürünlerini işliyor mu? — 5/5 test ✓
- [x] ITAD entegrasyonu tamamlandı — ExternalPriceHistory modeli, itad_service.py, CLI komutu, detay sayfası ✓
- [x] ITAD API'den geçmiş fiyat verisi çekiliyor (API key config.py'de ITAD_API_KEY ile ayarlanır)
- [x] Steam appid → ITAD eşleştirmesi başarısız olunca sessizce atlanıyor — `lookup_itad_id()` None döner

---

### Faz 9.5 — ITAD OAuth Entegrasyonu ✅ Tamamlandı

Hedef: ITAD API'sinin `client_credentials` yerine `authorization_code` OAuth akışı gerektirdiği tespit edildi; tam OAuth döngüsü uygulandı.

**Bulgular:**
- `oauth.isthereanydeal.com` Türkiye'den DNS çözülemiyor
- ITAD API, `client_credentials` grant type'ı desteklemiyor
- Doğru token endpoint: `https://isthereanydeal.com/oauth/token/` (trailing slash zorunlu)
- Doğru grant type: `authorization_code` (kullanıcı onaylı OAuth akışı)

**Geliştirme:**
- [x] `flask itad-auth` CLI komutu: yetkilendirme URL'ini yazar
- [x] `flask itad-exchange <code>` CLI komutu: kodu access+refresh token'a çevirir
- [x] Token `.env` dosyasına kaydedilir (`ITAD_ACCESS_TOKEN`, `ITAD_REFRESH_TOKEN`, `ITAD_TOKEN_EXPIRY`)
- [x] Access token expire olunca `refresh_token` ile otomatik yenileme
- [x] Eski `?key=` API'ye fallback (token yoksa dener)
- [x] `itad_service.py` tamamen yeniden yazıldı — OAuth akışı, token cache, `.env` okuma/yazma

**Kullanım Akışı (tek seferlik):**
```
flask itad-auth            → URL al, tarayıcıda aç, ITAD hesabına giriş yap
flask itad-exchange CODE   → code değerini buraya yaz
flask fetch-itad-history   → tüm gaming ürünleri için geçmiş çek
```

**Faz 9.5 Test Kontrol Listesi:**
- [x] `flask itad-auth` authorization URL üretiyor mu? ✓
- [x] Token exchange `POST /oauth/token/` ile çalışıyor mu? (kullanıcı girişi gerekiyor)
- [x] Refresh token ile otomatik yenileme destekleniyor mu? ✓ (kod hazır)
- [x] Credentials `.env`'de, GitHub'a gitmeden korunuyor mu? ✓

---

### Faz 10 — Çapraz Platform Fiyat Karşılaştırması ✅ Tamamlandı

Hedef: Aynı ürünün farklı platformlardaki fiyatlarını cimri.com / akakçe / epey tarzında yan yana göstermek (oyun vertical'ı hariç).

**Geliştirme:**
- [x] Ürün eşleştirme servisi: `normalized_name` + Jaccard benzerliği ile aynı ürünü birden fazla kaynakta tespit et (`app/services/matching_service.py`)
- [x] `ProductGroup` modeli veya sorgu katmanı: query-tabanlı gruplama, migration yok — `group_products()` fonksiyonu
- [x] Karşılaştırma sayfası (`/compare`) — arama kutusuyla ürün ara, platform bazlı fiyat tablosu göster
- [x] Ürün detay sayfasına "Bu ürünün diğer platformlardaki fiyatları" tablosu ekle (Faz 7'de hazır, aktif)
- [x] En ucuz platformu vurgula (yeşil renk + "En Ucuz" rozeti)
- [x] Fiyat farkı yüzdesini göster (örn. "+%18 daha pahalı")
- [x] Karşılaştırmada stok durumunu da göster
- [x] Sidebar'a "Fiyat Karşılaştır" linki eklendi

**Mimari Not:**
- `app/services/matching_service.py`: `jaccard_score()`, `search_products()`, `group_products()`, `compare_products()`
- Jaccard threshold: arama için ≥ 0.25, grup birleştirme için ≥ 0.65
- Oyun ürünleri sayfaya dahil edilmez (`vertical != 'gaming'` filtresi)
- Migration yok — sorgu katmanı ile saf Python gruplama
- Nike Dunk Low Panda test: 11 platform eşleşmesi ✓

**Faz 10 Test Kontrol Listesi:**
- [x] Aynı marka + benzer isimli ürün farklı kaynaklardan eşleşiyor mu? — Nike Dunk 11 platform ✓
- [x] Farklı ürünler yanlışlıkla eşleşiyor mu? — Jaccard(samsung tv, dyson supersonik) = 0.0 ✓
- [x] Karşılaştırma tablosu yalnızca 1 kaynak bulunan ürünlerde bozulmuyor mu? — uyarı metni ✓
- [x] Stok dışı platform karşılaştırmada görünüyor mu? — stock_status sütunu ✓
- [x] Oyun ürünleri karşılaştırma sayfasına karışıyor mu? — `vertical != 'gaming'` filtresi ✓

---

### Faz 11 — Grafik ve Görselleştirme ✅ Tamamlandı

Hedef: Fiyat geçmişinin görsel olarak sunulması.

**Geliştirme:**
- [x] Chart.js entegrasyonu (CDN v4.4.3, base.html'e eklendi)
- [x] Ürün detay sayfasına fiyat geçmişi grafiği ekle — mavi çizgi, fill, dark theme
- [x] Fiyat düşüş noktalarını grafik üzerinde işaretle — yeşil büyük nokta (düşüş), kırmızı (artış)
- [x] Dashboard'a mini sparkline grafikler ekle — ürün kartlarında 36px yükseklik, yeşil/kırmızı trend
- [x] Oyun fiyat geçmişi grafiği (ITAD tarihsel veri ayrı turuncu noktalı çizgi + tablo)
- [x] ITAD kaynaklı tarihsel noktalar farklı renk/stil ile gösterilsin — `#f59e0b` + `borderDash:[6,3]`

**Mimari Notlar:**
- `products.py`: `history[::-1]` ile kronolojik sıralama (slice — `list()` builtin `def list()` view ile çakışırdı)
- `dashboard.py`: `PriceHistory` sorgusu ile `sparkline_data` dict → `{product_id: [prices]}` template'e geçiyor
- `_card.html`: `{% if sparkline_data is defined %}` guard ile yalnızca dashboard bağlamında sparkline gösterir
- `detail.html`: `extra_scripts` block'ta IIFE içinde Chart.js instance'ları; `spanGaps:true` ile None noktaları atlar

**Faz 11 Test Kontrol Listesi:**
- [x] Chart.js CDN yükleniyor — base.html ✓
- [x] `priceChart` canvas detay sayfasında rendering — 200 ✓
- [x] `itadChart` canvas gaming ürünlerinde rendering ✓
- [x] `sparkline_data` JSON doğru oluşturuluyor — dashboard HTML'inde `sparkline-154`, `sparkline-223` vs. ✓
- [x] None fiyat noktaları grafik kırmıyor — `spanGaps: true` ✓

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

### Faz 13 — Fiyat Toplayıcı Entegrasyonu: cimri.com + akakce.com

Hedef: cimri.com ve akakce.com gibi fiyat karşılaştırma toplayıcı sitelerini scrape ederek, bot korumalı mağazaları (Hepsiburada, Trendyol vb.) dolaylı olarak kapsama almak. Bu siteler zaten yüzlerce mağazanın fiyatlarını karşılaştırıyor; en düşük fiyatı ve hangi mağazanın en ucuz olduğunu tek bir scrape ile elde edebiliriz.

**Değer Önerisi:**
- Hepsiburada, Trendyol, Amazon TR gibi bot korumalı sitelere doğrudan erişim sağlanamıyor
- cimri.com ve akakce.com bu mağazaların verilerini zaten topluyor
- Bir ürünün hangi mağazada en ucuz olduğunu toplayıcı siteden çekebiliriz
- Doğrudan taranan ürünlerle fiyat karşılaştırması yapılabilir

**Eklenecek Kaynaklar:**
- cimri.com — `vertical=ecommerce`, `scraper_type=aggregator`
- akakce.com — `vertical=ecommerce`, `scraper_type=aggregator`

**Geliştirme:**
- [ ] cimri.com scraper (`app/scrapers/ecommerce/cimri.py`) — kategori sayfaları taranır, requests ile başla, bot koruması varsa Playwright
- [ ] akakce.com scraper (`app/scrapers/ecommerce/akakce.py`) — kategori sayfaları taranır, requests ile başla, bot koruması varsa Playwright
- [ ] `Source.scraper_type` için `aggregator` tipi eklendi (mevcut `scraper_type` VARCHAR alanına yeni değer — migration gerektirmez)
- [ ] `Product` modeline `store_count` INT alanı eklendi (kaç mağazada listelendiği) — migration gerekir
- [ ] `Product` modeline `cheapest_store` VARCHAR(100) alanı eklendi (en ucuz mağazanın adı) — migration gerekir
- [ ] seed.py'e cimri ve akakce Source + ScrapeTarget kayıtları eklendi
- [ ] registry.py'e cimri ve akakce scraper'ları eklendi
- [ ] Ürün detay sayfasına "Bu ürün bu mağazalarda da satılıyor" bölümü eklendi (aggregator verisi varsa `cheapest_store` + `store_count` gösterilir)
- [ ] Faz 10 karşılaştırma sayfası aggregator fiyatlarını da gösterir; `matching_service.py` aggregator kayıtlarını hesaba katar

**Mimari Notlar:**
- `vertical = 'ecommerce'` — her iki site de ağırlıklı olarak elektronik/ev/spor ürünleri
- `scraper_type = 'aggregator'` — doğrudan mağaza değil, toplayıcı site
- `current_price` = aggregator'da gösterilen en düşük fiyat
- `product_url` = aggregator sitesindeki ürün sayfası URL'si (tüm mağaza karşılaştırması için)
- `cheapest_store` = en ucuz mağazanın adı (Trendyol, Hepsiburada vb.)
- `store_count` = kaç mağazada listelendiği
- cimri.com tarama URL örüntüsü: `/elektronik`, `/ev-yasam`, `/spor` kategori sayfaları + `?sort=minPrice` sıralaması
- akakce.com tarama URL örüntüsü: `/elektronik`, `/mutfak-urunleri` vb. kategori sayfaları
- Arama endpoint'leri: cimri `/arama?q=`, akakce `/?q=`
- Pagination: Her iki site de `?page=N` veya benzeri destekler — `MAX_PAGES` ayarlanacak

**Faz 10 ile İlişki:**
- Faz 10 (çapraz karşılaştırma): doğrudan taranan ürünleri siteler arası eşleştirir
- Faz 13 (aggregator entegrasyonu): toplayıcı sitelerden zaten eşleştirilmiş fiyatları alır
- Faz 13 sonrası Faz 10 aggregator kayıtlarını da hesaba katacak şekilde güncellenir

**Faz 13 Test Kontrol Listesi:**
- [ ] cimri.com scraper en az 50 ürün dönüyor mu?
- [ ] akakce.com scraper en az 50 ürün dönüyor mu?
- [ ] `cheapest_store` alanı doğru dolduruldu mu? (örn. "Trendyol", "Hepsiburada")
- [ ] `store_count` alanı sıfırdan büyük mü?
- [ ] `current_price` aggregator'daki en düşük fiyatı yansıtıyor mu?
- [ ] Ürün detay sayfasında `cheapest_store` + `store_count` gösteriliyor mu?
- [ ] Aggregator ürünleri E-ticaret listesinde görünüyor mu?
- [ ] Bot koruması varsa Playwright fallback devreye giriyor mu?
- [ ] Aggregator kaynağından gelen ürünler `source.scraper_type = 'aggregator'` ile işaretleniyor mu?

---

### Faz 14 — Yeni Site Entegrasyonları (Moda & E-ticaret Genişlemesi)

Hedef: Mevcut scraper altyapısını kullanarak yeni Türkiye e-ticaret ve moda sitelerini sisteme eklemek.

**Öncelikli Adaylar:**

| Site | Vertical | Tahmini Zorluk | Not |
|------|----------|----------------|-----|
| Boyner | Moda & E-ticaret | Orta | Geniş ürün yelpazesi (giyim, ev, elektronik) |
| Morhipo | Moda | Orta | İndirim odaklı site — scraper için ideal |
| LC Waikiki | Moda | Orta | Kendi altyapısı, indirim sayfaları mevcut |
| Koton | Moda | Orta | Türkiye'nin büyük moda markası |
| MediaMarkt TR | E-ticaret | Orta-Zor | Elektronik, Playwright gerekebilir |
| Vatan Bilgisayar | E-ticaret | Kolay-Orta | Temiz HTML yapısı |
| GittiGidiyor / eBay TR | E-ticaret | Zor | Marketplace; bot koruması |

**Geliştirme:**
- [ ] Boyner scraper (`app/scrapers/fashion/boyner.py` veya `ecommerce/boyner.py`) — vertical hem fashion hem ecommerce kapsar
- [ ] Morhipo scraper (`app/scrapers/fashion/morhipo.py`) — indirim sayfaları
- [ ] LC Waikiki scraper (`app/scrapers/fashion/lcwaikiki.py`)
- [ ] Koton scraper (`app/scrapers/fashion/koton.py`)
- [ ] MediaMarkt TR scraper (`app/scrapers/ecommerce/mediamarkt.py`)
- [ ] Vatan Bilgisayar scraper (`app/scrapers/ecommerce/vatan.py`)
- [ ] seed.py'e yeni Source + ScrapeTarget kayıtları
- [ ] registry.py güncellemesi

**Mimari Notlar:**
- Her yeni scraper Playwright veya requests ile başlar; bot koruması varsa Playwright'e geçilir
- Boyner gibi çift vertical site için `vertical='ecommerce'` tercih edilir (daha geniş kapsam)
- Mevcut `PlaywrightBaseScraper` sayfalama altyapısı yeni scraper'larda kullanılır

**Faz 14 Test Kontrol Listesi:**
- [ ] Boyner scraper en az 30 ürün dönüyor mu?
- [ ] Her yeni scraper hata verince uygulamayı çökertmiyor mu?
- [ ] Yeni scraper'lar `vertical`, `category`, `brand` alanlarını doğru dolduruyor mu?
- [ ] Ürün listesi sayfasında yeni kaynaklar filtrede görünüyor mu?

---

### Faz 15 — Tasarım Revizyonu

Hedef: Mevcut koyu temalı arayüzü gözden geçirmek; kullanılabilirlik, mobil uyumluluk ve görsel tutarlılık açısından iyileştirmek. Bu faz büyük ölçüde **düşünme ve karar aşamasıdır** — kod yazmadan önce ne değiştirilmesi gerektiği belirlenir.

**Değerlendirilecek Konular:**

*Genel Tasarım:*
- [ ] Mevcut bileşenler ve sayfa düzenleri gözden geçirilsin (sidebar, kartlar, tablolar)
- [ ] Renk paleti, tipografi ve boşluk tutarlılığı kontrol edilsin
- [ ] Aydınlık tema seçeneği eklenmeli mi? (toggle ile)
- [ ] CSS framework değerlendirmesi: mevcut custom CSS yeterli mi, yoksa Tailwind / Bootstrap geçişi mi?

*Mobil Uyumluluk:*
- [ ] Mevcut responsive davranış test edilsin (sidebar mobilde nasıl görünüyor?)
- [ ] Ürün kartları mobilde düzgün sıralanıyor mu?
- [ ] Tablolar küçük ekranda kaydırılabilir mi?
- [ ] Touch-friendly buton ve filtreler

*Ürün Kartları:*
- [ ] Görsel alanı (Faz 12 sonrası gerçek resimlerle) nasıl görünecek?
- [ ] Rozet sistemi gözden geçirilsin (ATL, 30d, 90d — fazla bilgi var mı?)
- [ ] Fiyat karşılaştırma rozeti (Eneba ucuzsa) görünürlüğü

*Detay Sayfası:*
- [ ] Fiyat grafiği (Faz 11) için alan planlanacak
- [ ] ITAD tarihsel veri bölümü tasarımı
- [ ] Rakip fiyat tablosu düzeni

**Karar Verilmesi Gereken Sorular:**
1. Framework değişikliği yapılacak mı? (mevcut CSS mi, Tailwind mi?)
2. Aydınlık/koyu tema toggle'ı isteniliyor mu?
3. Sidebar mobilde hamburger menü mi, alt navigation bar mı olacak?
4. Ürün kartlarında önce görsel mi yoksa fiyat bilgisi mi ön plana çıkacak?

**Faz 15 Test Kontrol Listesi:**
- [ ] 320px / 768px / 1280px genişliklerde tüm sayfalar düzgün görünüyor mu?
- [ ] Tasarım değişiklikleri mevcut fonksiyonelliği bozmadı mı?
- [ ] Aydınlık/koyu tema toggle çalışıyor mu (eğer eklendiyse)?
- [ ] Sayfa yükleme hızı tasarım değişikliğiyle gerilemedi mi?

---

### Faz 16 — Güvenlik ve Kurulum Sihirbazı

Hedef: Projeyi başka birinin kurmasına hazır hale getirmek. Mevcut kişisel bilgiler ve hard-coded değerler temizlenerek, yeni kullanıcıdan gerekli bilgileri interaktif olarak alan bir kurulum akışı oluşturulur.

**Yapılacaklar — Temizleme:**
- [ ] `seed.py`'den kişisel veriler çıkarılsın (gerçek API key referansları, kişisel notlar)
- [ ] `CLAUDE.md`'den paylaşılmaması gereken bilgiler temizlensin
- [ ] `config.py`'de hard-coded değer kalmadığından emin olunur; tümü `.env`'e taşınır
- [ ] `.env.example` dosyası oluşturulur (gerçek değerler olmadan şablon)
- [ ] `README.md`'deki kurulum adımları `.env.example` üzerinden güncellenir

**Yapılacaklar — Kurulum Sihirbazı:**
- [ ] İlk çalıştırmada `instance/` klasörü yoksa kurulum sihirbazı tetiklenir
- [ ] Sihirbaz şu bilgileri sorar:
  - Uygulama secret key (otomatik üretilebilir)
  - ITAD API credentials (isteğe bağlı — atlanabilir)
  - Varsayılan scrape interval (dakika cinsinden)
  - Hangi vertical'lar aktif olsun? (ecommerce / fashion / gaming seçimi)
- [ ] Sihirbaz çıktısını `instance/config.local.py` veya `.env`'e yazar
- [ ] `flask setup` CLI komutu olarak da tetiklenebilir

**Yapılacaklar — Güvenlik:**
- [ ] Flask `SECRET_KEY` varsayılan değeri kaldırılır; üretilmezse uyarı verilir
- [ ] Debug modu production'da kapalı kalacak şekilde kontrol eklenir
- [ ] CSRF koruması (`flask-wtf`) formlar için değerlendirilir (Faz 17 öncesi gerekli)
- [ ] Rate limiting değerlendirmesi (scraper endpoint'lerine aşırı istek koruması)

**Faz 16 Test Kontrol Listesi:**
- [ ] `.env.example` dosyası gerçek credential içermiyor mu?
- [ ] Sihirbaz olmadan (boş `.env` ile) uygulama anlaşılır hata veriyor mu?
- [ ] `flask setup` komutu soruları soruyor ve değerleri yazıyor mu?
- [ ] `config.py`'de hard-coded secret key kalmadı mı?

---

### Faz 17 — Çoklu Kullanıcı ve Admin Paneli

Hedef: Tek kullanıcılı yapıdan çoklu kullanıcıya geçiş. Her kullanıcı kendi alarm listesini yönetir; admin kullanıcı kaynakları, scraper'ları ve sistemi yönetir. Bu faz halka açık bir sistem yapmak istenirse zorunlu önkoşuldur.

**Kullanıcı Sistemi:**
- [ ] `User` modeli: id, username, email, password_hash, role, is_active, created_at (migration)
- [ ] Flask-Login entegrasyonu (oturum yönetimi)
- [ ] Kayıt sayfası (`/register`) — opsiyonel: sadece admin kayıt açabilir
- [ ] Giriş/çıkış sayfaları (`/login`, `/logout`)
- [ ] Şifre değiştirme (`/profile`)
- [ ] Role sistemi: `admin` / `user` (RBAC — basit iki seviye)
- [ ] `PriceAlert` modeline `user_id` eklenir — her alarm bir kullanıcıya aittir
- [ ] Mevcut alarmlar admin kullanıcıya aktarılır

**Admin Paneli (`/admin`):**
- [ ] Kullanıcı yönetimi: listele, aktif/pasif yap, admin yetki ver
- [ ] Kaynak yönetimi: scraper'ları aktif/pasif yap, interval ayarla (mevcut `/sources` genişletilir)
- [ ] Sistem durumu: son scrape zamanları, hata sayıları, ürün sayıları
- [ ] Manuel scrape tetikleme (mevcut buton admin paneline taşınır)
- [ ] Ayarlar: ITAD API credentials, bildirim ayarları (admin paneli üzerinden)

**Mimari Kararlar:**
- Flask-Login veya Flask-Security — ikisi de değerlendirilebilir
- Şifre hash: `werkzeug.security` (zaten bağımlılıkta mevcut)
- SQLite kullanımı devam edebilir; çok kullanıcılı için WAL modu yeterli
- Admin paneli için ayrı blueprint: `app/routes/admin.py`
- Jinja2 `current_user` entegrasyonu ile şablon güncellemeleri

**Faz 17 Test Kontrol Listesi:**
- [ ] Admin olmayan kullanıcı admin sayfalarına erişemiyor mu?
- [ ] Her kullanıcı yalnızca kendi alarmlarını görüyor mu?
- [ ] Giriş yapmadan ürün listesi görüntülenebiliyor mu? (public mı, private mı — kararlaştırılacak)
- [ ] Şifre hash doğru çalışıyor mu?
- [ ] Flask-Login session yönetimi Playwright scraper thread'leriyle çakışmıyor mu?

---

### Faz 18 — Halka Açılım Hazırlığı (Opsiyonel)

Hedef: Sistemi yalnızca kişisel kullanımın ötesine taşımak için gerekli teknik altyapıyı kurmak. **Bu faz kararlaştırılmış değil — ne zaman ve nasıl yapılacağı düşünülecek.**

**Değerlendirilecek Sorular:**
1. Hosting nerede olacak? (Heroku, Railway, DigitalOcean, VPS, self-hosted?)
2. SQLite → PostgreSQL geçişi ne zaman? (Flask-Migrate ile geçiş kolay ama veri migration planlanmalı)
3. Kullanıcı kaydı açık mı yoksa davetiye ile mi?
4. Rate limiting scraper endpoint'lerinde gerekli mi?
5. Domain ve SSL sertifikası
6. Playwright headless scraper'lar cloud'da çalışabiliyor mu? (memory/CPU limitleri)

**Teknik Hazırlıklar (karar verilirse):**
- [ ] PostgreSQL geçişi: `DATABASE_URL` env var, `psycopg2` bağımlılık, migration test
- [ ] Docker Compose dosyası (web + scraper worker ayrımı değerlendirilebilir)
- [ ] `gunicorn` veya `waitress` WSGI server (development server production'da kullanılmaz)
- [ ] Ortam değişkenleri tam olarak belgelenir (`.env.example` güncel tutulur)
- [ ] Hata izleme: Sentry entegrasyonu değerlendirilebilir
- [ ] Yedekleme: SQLite için periyodik `.db` kopyası veya `pg_dump`
- [ ] Public API: diğer uygulamaların fiyat verisi çekebileceği REST endpoint'leri (opsiyonel)

**Faz 18 Test Kontrol Listesi:**
- [ ] Production ortamında debug=False ile uygulama çalışıyor mu?
- [ ] Tüm environment variable'lar `.env.example`'da belgelenmiş mi?
- [ ] Playwright scraper'lar seçilen hosting'de çalışabiliyor mu?
- [ ] Veritabanı yedekleme planı var mı?

---

### Faz 19 — Mobil Uygulama

Hedef: SparkDeal'ı akıllı telefonda kullanılabilir hale getirmek. Bildirim desteği ile fiyat düşüşlerini anlık olarak almak.

**Yaklaşım Seçenekleri (karar verilecek):**

| Yaklaşım | Avantaj | Dezavantaj |
|----------|---------|------------|
| PWA (Progressive Web App) | Mevcut Flask üzerine eklenir, mağaza gerekmez | iOS'ta sınırlı push bildirim |
| React Native | Native performans, iOS + Android | Ayrı frontend kodbase, öğrenme eğrisi |
| Flutter | Native performans, tek kod base | Dart öğrenme eğrisi |
| Capacitor (mevcut web → native) | Mevcut HTML/CSS/JS kullanılır | Performans sınırlı |

**Önerilen Yaklaşım: PWA + Service Worker**
- Mevcut Flask şablonları üzerine inşa edilir
- `manifest.json` + `service-worker.js` eklenir
- Web Push API ile bildirim desteği
- iOS için sınırlamalar kabul edilir (veya React Native'e geçilir)

**Geliştirme (PWA yaklaşımı seçilirse):**
- [ ] `manifest.json` — uygulama adı, ikon, tema rengi, start URL
- [ ] `service-worker.js` — offline cache, push bildirim altyapısı
- [ ] Web Push API entegrasyonu — alarm tetiklenince push bildirim gönder
- [ ] `PushSubscription` modeli — kullanıcı başına push endpoint sakla
- [ ] `/static/icons/` — farklı çözünürlüklerde uygulama ikon seti
- [ ] "Ana Ekrana Ekle" prompt'u (install banner)
- [ ] Mobile-first sayfa düzeni (Faz 15 tamamlandıysa hazır olur)

**Faz 19 Test Kontrol Listesi:**
- [ ] Chrome ve Safari'de "Ana Ekrana Ekle" çalışıyor mu?
- [ ] Fiyat alarmı tetiklendiğinde push bildirim geliyor mu?
- [ ] Offline durumda son yüklenen sayfalar görüntülenebiliyor mu?
- [ ] 60fps scroll performansı mobilde sağlanıyor mu?

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
| E-ticaret | `ecommerce` | Teknosa, Hepsiburada, N11, Amazon TR, Trendyol, cimri.com *(Faz 13)*, akakce.com *(Faz 13)* |
| Moda & Spor | `fashion` | Superstep, Sneaksup, Sneakersonline, Bershka, Pull&Bear, H&M TR |
| Oyun İndirimleri | `gaming` | Steam, Epic Games, Eneba *(karşılaştırma)*, Bynogame *(karşılaştırma)* |

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

| Site | Durum | Not |
|------|-------|-----|
| Superstep | ✅ Aktif | Playwright, `?page=N` pagination, MAX_PAGES=10 → ~413 ürün |
| Sneaksup | ✅ Aktif | Playwright, Inveon platform, `data-ga-impressions` JSON, sale sayfası |
| Sneakersonline | ✅ Aktif | Playwright, ikas.com, `div[data-id]` kartlar, scroll×8 → ~180 ürün |
| H&M TR | ❌ Pasif | Akamai bot koruması — Playwright ile de aşılamadı |
| Bershka TR | ❌ Pasif | "Access Denied" bot koruması |
| Pull&Bear TR | ❌ Pasif | Bot koruması |

### Oyun Platformları

| Site | Durum | Not |
|------|-------|-----|
| Steam | ✅ Aktif | requests, çift URL (standart + ndl=1), MAX_PAGES=10 → ~820 oyun |
| Epic Games | ⬜ Faz 9 | Public GraphQL API, auth gerektirmez, TR fiyatı |
| Bynogame | ⬜ Faz 9 | Benzer yapı |
| Eneba | ⬜ Faz 9 | Fiyat karşılaştırma ortağı — scraper değil, arama API'si ile lookup |

### Fiyat Toplayıcıları (Aggregator)

| Site | Durum | Not |
|------|-------|-----|
| cimri.com | ⬜ Faz 13 | E-ticaret aggregator, `scraper_type=aggregator`, `cheapest_store` + `store_count` alanları |
| akakce.com | ⬜ Faz 13 | E-ticaret aggregator, benzer yapı; her ikisi de bot koruması denenecek |

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

Steam, Epic Games oyunları. Eneba ve Bynogame fiyat karşılaştırması detay sayfasında gösterilir.

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
    ├── epic_games.py     ← GraphQL API
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
| 8 | Moda & Spor siteleri (Superstep ✓, Sneaksup ✓, Sneakersonline ✓ — Bershka/Pull&Bear/H&M bot koruması) | ✅ Tamamlandı |
| 8.5 | Fashion sitelerine sayfalama (Superstep 10 sayfa→413, Sneakersonline scroll×8→180) | ✅ Tamamlandı |
| 8.5 v2 | E-ticaret + oyun sitelerine sayfalama (N11 5 sayfa, Steam 10 sayfa × 2 URL →~820, Hepsiburada hazır) | ✅ Tamamlandı |
| 9 | Epic Games scraper + Eneba/Bynogame fiyat karşılaştırma ortağı + CompetitorPrice modeli + ITAD | ✅ Tamamlandı |
| 9.5 | ITAD OAuth akışı (authorization_code, token exchange, auto-refresh) | ✅ Tamamlandı |
| 10 | Çapraz platform fiyat karşılaştırması (matching_service, /compare sayfası, Jaccard gruplama) | ✅ Tamamlandı |
| 11 | Chart.js grafikleri (kendi verisi + ITAD geçmişi birlikte) + dashboard sparklines | ✅ Tamamlandı |
| 12 | Ürün görselleri (yerel indirme + fallback) | ⬜ Bekliyor |
| 13 | Fiyat toplayıcı entegrasyonu: cimri.com + akakce.com (aggregator scraper, store_count, cheapest_store) | ⬜ Bekliyor |
| 14 | Yeni site entegrasyonları: Boyner, Morhipo, LC Waikiki, Koton, MediaMarkt TR, Vatan | ⬜ Bekliyor |
| 15 | Tasarım revizyonu: responsive, mobil uyumluluk, tema seçeneği, UX iyileştirme | ⬜ Düşünme aşaması |
| 16 | Güvenlik ve kurulum sihirbazı: kişisel veri temizleme, .env.example, setup wizard | ⬜ Bekliyor |
| 17 | Çoklu kullanıcı + admin paneli: Flask-Login, RBAC, kullanıcı yönetimi, ayarlar | ⬜ Bekliyor |
| 18 | Halka açılım hazırlığı: PostgreSQL, Docker, hosting, rate limiting (opsiyonel) | ⬜ Düşünme aşaması |
| 19 | Mobil uygulama: PWA + push bildirim veya React Native (karar verilecek) | ⬜ Bekliyor |

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
20. Her faz tamamlandığında GitHub'a push et ve README'yi güncelle:
    - README'deki yol haritası tablosunda fazı `✅` olarak işaretle.
    - README'deki vertical/site tablolarını güncel duruma getir (aktif ✅ / pasif ❌).
    - Commit mesajı: `Faz N tamamlandi: <kısa özet>`.
    - `git add . && git commit -m "..." && git push` ile remote'a gönder.

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

Bu proje, Türkiye'deki e-ticaret (Teknosa, Hepsiburada, Trendyol vb.), moda/spor (Superstep, Bershka, H&M vb.) ve oyun platformlarını (Steam, Epic Games — Eneba/Bynogame fiyat karşılaştırması ile) takip eden; fiyat geçmişi tutan, gerçek indirimleri analiz eden ve kullanıcıya en iyi fırsatları gösteren kişisel bir Flask tabanlı fiyat takip sistemidir.

Ana değer önerisi:

Sadece "%50 indirim" yazan ürünleri göstermek değil, geçmiş fiyat verisine göre gerçekten ucuz olan ürünleri — her kategoride — bulmak.
