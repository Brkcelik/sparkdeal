"""Scraper servis katmanı — ürün upsert, fiyat geçmişi ve tarama logu."""
import logging
import re
from datetime import datetime, timezone

from app import db
from app.models import Source, Product, PriceHistory, ScrapeRun, ScrapeTarget

logger = logging.getLogger(__name__)

_TR_MAP = str.maketrans('şçğüöıİŞÇĞÜÖ', 'scguoiiscguo')


def normalize_product_name(name: str) -> str:
    """Siteler arası ürün eşleştirmesi için isim normalleştirme."""
    name = name.lower().translate(_TR_MAP)
    name = re.sub(r'[^\w\s]', ' ', name)
    return re.sub(r'\s+', ' ', name).strip()


def upsert_product(source: Source, data: dict) -> tuple[Product, bool]:
    """
    Ürünü kaydet veya güncelle.
    Returns: (product, created) — created=True ise yeni kayıt.
    """
    external_id = str(data.get('external_id') or '')
    name = (data.get('name') or '').strip()

    if not name:
        raise ValueError("Ürün adı boş olamaz")

    product = None
    created = False

    # external_id varsa önce bununla eşleştir
    if external_id:
        product = Product.query.filter_by(
            source_id=source.id,
            external_id=external_id,
        ).first()

    # Yoksa isim + kaynak ile eşleştirmeyi dene
    if not product:
        product = Product.query.filter_by(
            source_id=source.id,
            name=name,
        ).first()

    now = datetime.now(timezone.utc)

    if product is None:
        product = Product(
            source=source,
            external_id=external_id or None,
            name=name,
            vertical=data.get('vertical', source.vertical),
            first_seen_at=now,
        )
        db.session.add(product)
        created = True

    # Her durumda güncel alanları yaz
    product.normalized_name = normalize_product_name(name)
    product.current_price = data.get('current_price')
    product.old_price = data.get('old_price')
    product.discount_percent = data.get('discount_percent')
    product.product_url = data.get('product_url') or product.product_url or '#'
    product.image_url = data.get('image_url') or product.image_url
    product.brand = data.get('brand') or product.brand
    product.category = data.get('category') or product.category
    product.stock_status = data.get('stock_status', 'unknown')
    product.currency = data.get('currency', 'TRY')
    product.platform = data.get('platform') or product.platform
    product.region = data.get('region') or product.region
    product.edition = data.get('edition') or product.edition
    product.gender = data.get('gender') or product.gender
    product.last_seen_at = now
    product.updated_at = now

    return product, created


def record_price(product: Product, data: dict) -> PriceHistory:
    """Her taramada yeni fiyat geçmişi satırı ekle."""
    h = PriceHistory(
        product=product,
        price=data.get('current_price'),
        old_price=data.get('old_price'),
        discount_percent=data.get('discount_percent'),
        stock_status=data.get('stock_status', 'unknown'),
        recorded_at=datetime.now(timezone.utc),
    )
    db.session.add(h)
    return h


def run_scrape(source_name: str) -> ScrapeRun:
    """
    Verilen kaynak için tüm aktif tarama hedeflerini çalıştır.
    ScrapeRun kaydı oluşturur ve döndürür.
    """
    from app.scrapers.registry import get_scraper_class

    # İsim eşleştirmesi: önce tam eşleşme, sonra büyük/küçük harf duyarsız
    source = Source.query.filter_by(name=source_name).first()
    if not source:
        source = Source.query.filter(
            db.func.lower(Source.name) == source_name.lower()
        ).first()
    if not source:
        raise ValueError(f"Kaynak bulunamadı: {source_name!r}")

    if not source.is_active:
        logger.info("%s kaynağı pasif, atlanıyor", source_name)
        run = ScrapeRun(
            source=source,
            status='skipped',
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        db.session.add(run)
        db.session.commit()
        return run

    scraper_cls = get_scraper_class(source_name)
    if not scraper_cls:
        raise ValueError(f"Scraper sınıfı bulunamadı: {source_name!r}")

    scraper = scraper_cls(source)

    targets = ScrapeTarget.query.filter_by(
        source_id=source.id, is_active=True
    ).all()

    # Hedef yoksa kaynak URL'sini sahte target gibi kullan
    if not targets:
        targets = [_DummyTarget(source)]

    run = ScrapeRun(
        source=source,
        status='running',
        started_at=datetime.now(timezone.utc),
    )
    db.session.add(run)
    db.session.flush()

    total_found = 0
    total_new = 0
    total_updated = 0
    error_messages = []
    updated_products = []

    for target in targets:
        try:
            items = scraper.scrape(target)
        except Exception as exc:
            msg = f"{getattr(target, 'title', str(target))}: {exc}"
            logger.error("Scrape hatası: %s", msg)
            error_messages.append(msg)
            continue

        total_found += len(items)

        for data in items:
            try:
                product, created = upsert_product(source, data)
                # Fiyat None ise geçmişe ekleme — NOT NULL kısıtı
                if data.get('current_price') is not None:
                    record_price(product, data)
                if created:
                    total_new += 1
                else:
                    total_updated += 1
                updated_products.append(product)
                db.session.flush()
            except Exception as exc:
                logger.error("Ürün kaydedilemedi: %s | %s", data.get('name'), exc)
                db.session.rollback()

    # ScrapeRun'ı tamamla
    run.status = 'error' if (error_messages and total_found == 0) else 'success'
    run.found_count = total_found
    run.new_product_count = total_new
    run.updated_product_count = total_updated
    run.error_message = '; '.join(error_messages) if error_messages else None
    run.finished_at = datetime.now(timezone.utc)

    source.last_scraped_at = run.finished_at
    if error_messages and total_found == 0:
        source.error_count = (source.error_count or 0) + 1

    db.session.commit()

    # Stats hesapla (yeni/güncellenen ürünler için)
    if total_found > 0:
        try:
            from app.services.stats_service import compute_stats_for_source
            computed = compute_stats_for_source(source.id)
            db.session.commit()
            logger.info("%s: %d ürün için istatistik hesaplandı", source_name, computed)
        except Exception as exc:
            logger.error("Stats hesaplama hatası (%s): %s", source_name, exc)

        # Alarm kontrolü
        try:
            from app.services.alert_service import check_alerts
            triggered = check_alerts(updated_products)
            if triggered:
                db.session.commit()
                logger.info("%s: %d alarm tetiklendi", source_name, triggered)
        except Exception as exc:
            logger.error("Alarm kontrol hatası (%s): %s", source_name, exc)

    logger.info(
        "%s taraması tamamlandı: %d bulundu, %d yeni, %d güncellendi",
        source_name, total_found, total_new, total_updated,
    )
    return run


class _DummyTarget:
    """ScrapeTarget kaydı olmayan kaynaklar için geçici hedef."""

    def __init__(self, source: Source):
        self.source_id = source.id
        self.title = source.name
        self.url = source.base_url
        self.category = None
        self.min_discount_percent = None
