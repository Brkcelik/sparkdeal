"""Alarm kontrol ve tetikleme servisi."""
import logging
from datetime import datetime, timezone, date

from app import db
from app.models import PriceAlert, Product

logger = logging.getLogger(__name__)


def check_alerts(products: list) -> int:
    """
    Verilen ürün listesi için aktif alarmları kontrol et.
    Tetiklenen alarmların last_triggered_at'ini güncelle.
    Returns: tetiklenen alarm sayısı
    """
    if not products:
        return 0

    today = datetime.now(timezone.utc).date()
    active_alerts = PriceAlert.query.filter_by(is_active=True).all()
    triggered_count = 0

    for alert in active_alerts:
        # Aynı gün zaten tetiklendiyse geç
        if alert.last_triggered_at:
            last_date = alert.last_triggered_at
            if hasattr(last_date, 'date'):
                last_date = last_date.date()
            if last_date == today:
                continue

        matched = _match_products(alert, products)
        for product in matched:
            if _should_trigger(alert, product):
                alert.last_triggered_at = datetime.now(timezone.utc)
                triggered_count += 1
                logger.info(
                    "Alarm tetiklendi: id=%d tip=%s ürün=%s",
                    alert.id, alert.alarm_type,
                    product.name[:40] if product else '—',
                )
                break

    if triggered_count:
        db.session.flush()

    return triggered_count


def check_all_alerts() -> int:
    """Tüm ürünleri tarayarak aktif alarmları kontrol et (manuel tetikleme için)."""
    products = Product.query.filter(
        Product.current_price.isnot(None)
    ).all()
    return check_alerts(products)


# ── Yardımcı fonksiyonlar ────────────────────────────────────────────────────

def _match_products(alert: PriceAlert, products: list) -> list:
    """Alert için eşleşen ürünleri döndür."""
    # Ürün bazlı alarm — sadece o ürünü kontrol et
    if alert.product_id:
        return [p for p in products if p.id == alert.product_id]

    matched = list(products)

    if alert.keyword:
        kw = alert.keyword.lower()
        matched = [p for p in matched if kw in p.name.lower()]

    if alert.category:
        cat = alert.category.lower()
        matched = [p for p in matched if p.category and cat in p.category.lower()]

    if alert.vertical:
        matched = [p for p in matched if p.vertical == alert.vertical]

    if alert.platform:
        matched = [p for p in matched if p.platform == alert.platform]

    return matched


def _should_trigger(alert: PriceAlert, product: Product) -> bool:
    """Alarm koşulunun karşılanıp karşılanmadığını kontrol et."""
    t = alert.alarm_type

    if t == 'price':
        return (
            product.current_price is not None
            and alert.target_price is not None
            and product.current_price <= alert.target_price
        )

    if t == 'atl':
        return product.badge_atl

    if t == 'keyword':
        # Kelime eşleşmesi _match_products'ta yapıldı; indirim eşiğini kontrol et
        min_pct = alert.min_discount_percent or 20.0
        return (
            product.discount_percent is not None
            and product.discount_percent >= min_pct
        )

    if t == 'category':
        min_pct = alert.min_discount_percent or 20.0
        return (
            product.discount_percent is not None
            and product.discount_percent >= min_pct
        )

    return False
