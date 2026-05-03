"""
Demo veri yükleyici — Faz 1-2 için.
Her çalıştırmada mevcut veriyi temizler ve yeniden oluşturur.
"""
import random
from datetime import datetime, timedelta, timezone
from app import create_app, db
from app.models import Source, Product, PriceHistory, ScrapeTarget
from app.services.scraper_service import normalize_product_name

app = create_app()


def random_price_history(product, days=60, entries=20):
    """Gerçekçi fiyat geçmişi oluştur: hafif dalgalanma + son dönemde düşüş."""
    base = product.old_price or product.current_price
    records = []
    now = datetime.now(timezone.utc)

    for i in range(entries, 0, -1):
        days_ago = int((i / entries) * days)
        recorded_at = now - timedelta(days=days_ago, hours=random.randint(0, 23))

        if i <= 4:
            price = product.current_price * random.uniform(0.97, 1.03)
        elif i <= 8:
            price = base * random.uniform(0.88, 0.96)
        else:
            price = base * random.uniform(0.95, 1.05)

        price = round(price, 2)
        disc = round((1 - price / base) * 100, 1) if base and base > price else 0

        records.append(PriceHistory(
            product=product,
            price=price,
            old_price=base,
            discount_percent=disc if disc > 0 else None,
            stock_status=product.stock_status,
            recorded_at=recorded_at,
        ))

    return records


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # ── Sources ──────────────────────────────────────
        sources = {
            'teknosa':       Source(name='Teknosa',      base_url='https://www.teknosa.com',    vertical='ecommerce', scraper_type='requests',  crawl_delay_seconds=2),
            'hepsiburada':   Source(name='Hepsiburada',  base_url='https://www.hepsiburada.com', vertical='ecommerce', scraper_type='playwright', crawl_delay_seconds=3),
            'n11':           Source(name='N11',           base_url='https://www.n11.com',        vertical='ecommerce', scraper_type='playwright', crawl_delay_seconds=2),
            'trendyol':      Source(name='Trendyol',     base_url='https://www.trendyol.com',   vertical='ecommerce', scraper_type='playwright', crawl_delay_seconds=4, is_active=False),
            'amazon_tr':     Source(name='Amazon TR',    base_url='https://www.amazon.com.tr',  vertical='ecommerce', scraper_type='requests',  crawl_delay_seconds=3, is_active=False),
            'superstep':     Source(name='Superstep',    base_url='https://www.superstep.com.tr', vertical='fashion', scraper_type='playwright', crawl_delay_seconds=2, is_active=False),
            'sneaksup':      Source(name='Sneaksup',     base_url='https://www.sneaksup.com',   vertical='fashion',   scraper_type='playwright', crawl_delay_seconds=2, is_active=False),
            'sneakersonline':Source(name='Sneakersonline',base_url='https://sneakersonline.com.tr', vertical='fashion', scraper_type='playwright', crawl_delay_seconds=2, is_active=False),
            'bershka':       Source(name='Bershka TR',   base_url='https://www.bershka.com/tr', vertical='fashion',   scraper_type='playwright', crawl_delay_seconds=3, is_active=False),
            'pullandbear':   Source(name='Pull&Bear TR', base_url='https://www.pullandbear.com/tr', vertical='fashion', scraper_type='playwright', crawl_delay_seconds=3, is_active=False),
            'hm':            Source(name='H&M TR',       base_url='https://www2.hm.com/tr_tr', vertical='fashion',    scraper_type='requests',  crawl_delay_seconds=2, is_active=False),
            'steam':         Source(name='Steam',        base_url='https://store.steampowered.com',  vertical='gaming', scraper_type='api',      crawl_delay_seconds=1, is_active=True),
            'epic_games':    Source(name='Epic Games',   base_url='https://store.epicgames.com',     vertical='gaming', scraper_type='api',      crawl_delay_seconds=1, is_active=True),
            'eneba':         Source(name='Eneba',        base_url='https://www.eneba.com',           vertical='gaming', scraper_type='requests',  crawl_delay_seconds=2, is_active=False),
            'bynogame':      Source(name='Bynogame',     base_url='https://www.bynogame.com',        vertical='gaming', scraper_type='requests',  crawl_delay_seconds=2, is_active=False),
        }

        for s in sources.values():
            db.session.add(s)
        db.session.flush()

        products = []

        # ── E-ticaret ─────────────────────────────────────
        ec_items = [
            dict(source=sources['teknosa'],     name='Samsung Galaxy A55 5G 256GB',          brand='Samsung',  category='Akilli Telefon', current_price=11999, old_price=14999, discount_percent=20, stock_status='in_stock'),
            dict(source=sources['teknosa'],     name='Logitech G502 X Plus Kablosuz Mouse',  brand='Logitech', category='Bilgisayar',     current_price=2199,  old_price=3499,  discount_percent=37, stock_status='in_stock'),
            dict(source=sources['teknosa'],     name='Samsung 55" QLED 4K Smart TV',         brand='Samsung',  category='Televizyon',     current_price=24999, old_price=34999, discount_percent=29, stock_status='in_stock'),
            dict(source=sources['hepsiburada'], name='Sony WH-1000XM5 Bluetooth Kulaklik',  brand='Sony',     category='Ses Sistemleri', current_price=5499,  old_price=8499,  discount_percent=35, stock_status='in_stock'),
            dict(source=sources['hepsiburada'], name='Apple iPad 10. Nesil 64GB Wi-Fi',     brand='Apple',    category='Tablet',         current_price=15999, old_price=18999, discount_percent=16, stock_status='in_stock'),
            dict(source=sources['hepsiburada'], name='Xiaomi Redmi Note 13 Pro 256GB',      brand='Xiaomi',   category='Akilli Telefon', current_price=7499,  old_price=9999,  discount_percent=25, stock_status='in_stock'),
            dict(source=sources['n11'],         name='Corsair K70 RGB PRO Mekanik Klavye',  brand='Corsair',  category='Bilgisayar',     current_price=2799,  old_price=4299,  discount_percent=35, stock_status='in_stock'),
            dict(source=sources['n11'],         name='Seagate Expansion 2TB Harici Disk',   brand='Seagate',  category='Depolama',       current_price=899,   old_price=1299,  discount_percent=31, stock_status='out_of_stock'),
            dict(source=sources['n11'],         name='MSI Vigor GK50 Elite Gaming Klavye',  brand='MSI',      category='Bilgisayar',     current_price=1199,  old_price=1799,  discount_percent=33, stock_status='in_stock'),
        ]

        for item in ec_items:
            p = Product(vertical='ecommerce', product_url='#', **item)
            db.session.add(p)
            products.append(p)

        # ── Fashion ───────────────────────────────────────
        fa_items = [
            dict(source=sources['superstep'], name='Nike Air Force 1 \'07 Erkek Sneaker',  brand='Nike',    category='Sneaker',  current_price=2799, old_price=3999, discount_percent=30, stock_status='in_stock'),
            dict(source=sources['superstep'], name='Adidas Superstar Unisex Spor Ayakkabi', brand='Adidas',  category='Sneaker',  current_price=1599, old_price=2499, discount_percent=36, stock_status='in_stock'),
            dict(source=sources['superstep'], name='New Balance 574 Erkek Yuruyus Ayakkabi',brand='New Balance', category='Sneaker', current_price=1999, old_price=2999, discount_percent=33, stock_status='in_stock'),
            dict(source=sources['sneaksup'],  name='Jordan 1 Retro Low OG Erkek Sneaker',  brand='Jordan',  category='Sneaker',  current_price=3299, old_price=4999, discount_percent=34, stock_status='out_of_stock'),
            dict(source=sources['hm'],        name='H&M Oversize Kapusonlu Sweatshirt',    brand='H&M',     category='Giyim',    current_price=399,  old_price=699,  discount_percent=43, stock_status='in_stock'),
            dict(source=sources['hm'],        name='H&M Slim Fit Chino Pantolon',          brand='H&M',     category='Giyim',    current_price=349,  old_price=599,  discount_percent=42, stock_status='in_stock'),
            dict(source=sources['bershka'],   name='Bershka Oversized Denim Ceket',        brand='Bershka', category='Giyim',    current_price=599,  old_price=999,  discount_percent=40, stock_status='in_stock'),
            dict(source=sources['pullandbear'],name='Pull&Bear Basic Pamuklu T-Shirt 3\'lu',brand='Pull&Bear',category='Giyim',   current_price=299,  old_price=499,  discount_percent=40, stock_status='in_stock'),
        ]

        for item in fa_items:
            p = Product(vertical='fashion', product_url='#', **item)
            db.session.add(p)
            products.append(p)

        # ── Gaming ────────────────────────────────────────
        ga_items = [
            dict(source=sources['steam'],   name='Red Dead Redemption 2',              brand='Rockstar', category='Aksiyon',     current_price=99,  old_price=329, discount_percent=70, stock_status='in_stock', platform='PC', region='TR', edition='Standard'),
            dict(source=sources['steam'],   name='Cyberpunk 2077 Complete Edition',    brand='CD Projekt',category='RPG',        current_price=139, old_price=429, discount_percent=68, stock_status='in_stock', platform='PC', region='TR', edition='Complete'),
            dict(source=sources['steam'],   name='Baldur\'s Gate 3',                   brand='Larian Studios',category='RPG',    current_price=249, old_price=499, discount_percent=50, stock_status='in_stock', platform='PC', region='TR', edition='Standard'),
            dict(source=sources['steam'],   name='Elden Ring',                         brand='FromSoftware',category='Aksiyon',  current_price=199, old_price=499, discount_percent=60, stock_status='in_stock', platform='PC', region='TR', edition='Standard'),
            dict(source=sources['epic_games'], name='God of War (2018) PC',           brand='Sony',     category='Aksiyon',     current_price=189, old_price=499, discount_percent=62, stock_status='in_stock', platform='PC', region='TR', edition='Standard'),
            dict(source=sources['epic_games'], name='Spider-Man Miles Morales PC',    brand='Sony',     category='Aksiyon',     current_price=249, old_price=699, discount_percent=64, stock_status='in_stock', platform='PC', region='EU', edition='Standard'),
            dict(source=sources['eneba'],   name='FIFA 24 PS5',                        brand='EA Sports',category='Spor',        current_price=449, old_price=899, discount_percent=50, stock_status='in_stock', platform='PS5', region='TR', edition='Standard'),
            dict(source=sources['bynogame'],name='Call of Duty Modern Warfare III PC', brand='Activision',category='FPS',        current_price=599, old_price=1299,discount_percent=54, stock_status='in_stock', platform='PC', region='TR', edition='Standard'),
        ]

        for item in ga_items:
            p = Product(vertical='gaming', product_url='#', **item)
            db.session.add(p)
            products.append(p)

        # normalized_name tüm ürünler için hesapla
        for p in products:
            p.normalized_name = normalize_product_name(p.name)

        db.session.flush()

        # ── Fiyat geçmişi ─────────────────────────────────
        for product in products:
            for h in random_price_history(product):
                db.session.add(h)

        # ── ScrapeTarget örnekleri ────────────────────────
        scrape_targets = [
            ScrapeTarget(source=sources['teknosa'],     title='Teknosa Kampanyalar',        url='https://www.teknosa.com/kampanyalar',             category='Genel',          scrape_interval_minutes=60),
            ScrapeTarget(source=sources['teknosa'],     title='Teknosa Bilgisayar',         url='https://www.teknosa.com/bilgisayar-c-5003',       category='Bilgisayar',     scrape_interval_minutes=120),
            ScrapeTarget(source=sources['hepsiburada'], title='Hepsiburada Fırsatlar',      url='https://www.hepsiburada.com/indirimli-urunler',   category='Genel',          scrape_interval_minutes=60),
            ScrapeTarget(source=sources['hepsiburada'], title='Hepsiburada Ses Sistemleri', url='https://www.hepsiburada.com/ses-sistemleri-c-375',category='Ses Sistemleri', scrape_interval_minutes=120),
            ScrapeTarget(source=sources['n11'],         title='N11 Kampanya',               url='https://www.n11.com/kampanya',                   category='Genel',          scrape_interval_minutes=60),
            ScrapeTarget(source=sources['superstep'],      title='Superstep İndirimler',          url='https://www.superstep.com.tr/indirimli-urunler',              category='Sneaker',  scrape_interval_minutes=180, is_active=False),
            ScrapeTarget(source=sources['hm'],             title='H&M Kadın İndirim',             url='https://www2.hm.com/tr_tr/kadin/indirim.html',                category='Giyim',    scrape_interval_minutes=240, is_active=False),
            ScrapeTarget(source=sources['hm'],             title='H&M Erkek İndirim',             url='https://www2.hm.com/tr_tr/erkek/indirim.html',                category='Giyim',    scrape_interval_minutes=240, is_active=False),
            ScrapeTarget(source=sources['sneaksup'],       title='Sneaksup Sezon Sonu',           url='https://www.sneaksup.com/sezon-sonu-indirimi',                category='Sneaker',  scrape_interval_minutes=180, is_active=False),
            ScrapeTarget(source=sources['sneaksup'],       title='Sneaksup Erkek',                url='https://www.sneaksup.com/erkek',                              category='Erkek Sneaker', scrape_interval_minutes=240, is_active=False),
            ScrapeTarget(source=sources['sneaksup'],       title='Sneaksup Kadın',                url='https://www.sneaksup.com/kadin',                              category='Kadın Sneaker', scrape_interval_minutes=240, is_active=False),
            ScrapeTarget(source=sources['sneakersonline'], title='Sneakersonline Tüm Ürünler',    url='https://sneakersonline.com.tr/tum-urunler',                   category='Sneaker',  scrape_interval_minutes=180, is_active=False),
            ScrapeTarget(source=sources['bershka'],        title='Bershka İndirim',               url='https://www.bershka.com/tr/indirim',                          category='Giyim',    scrape_interval_minutes=240, is_active=False),
            ScrapeTarget(source=sources['pullandbear'],    title='Pull&Bear İndirim',             url='https://www.pullandbear.com/tr/indirim',                      category='Giyim',    scrape_interval_minutes=240, is_active=False),
            ScrapeTarget(source=sources['steam'],      title='Steam Haftalık Fırsatlar',        url='https://store.steampowered.com/specials',                     category='Oyun', scrape_interval_minutes=120, is_active=True),
            ScrapeTarget(source=sources['epic_games'], title='Epic Games İndirimli Oyunlar',   url='https://store.epicgames.com/tr/browse?sortBy=releaseDate&onSale=true', category='Oyun', scrape_interval_minutes=180, is_active=True),
            ScrapeTarget(source=sources['trendyol'],    title='Trendyol İndirimli Ürünler', url='https://www.trendyol.com/sr?wc=103108&ob=MOST_DISCOUNTED', category='Genel', scrape_interval_minutes=60, is_active=False),
            ScrapeTarget(source=sources['amazon_tr'],   title='Amazon TR Elektronik',       url='https://www.amazon.com.tr/s?i=electronics&rh=p_n_pct-off-with-tax%3A25259774031', category='Elektronik', scrape_interval_minutes=120, is_active=False),
        ]
        for t in scrape_targets:
            db.session.add(t)

        db.session.commit()
        print(f"Seed tamamlandı: {len(products)} ürün, {len(sources)} kaynak, {len(scrape_targets)} tarama hedefi yüklendi.")


if __name__ == '__main__':
    seed()
