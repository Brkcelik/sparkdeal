"""Fiyat istatistigi ve firsaat skoru hesaplama servisi."""
import logging
from datetime import datetime, timedelta, timezone

from app import db
from app.models import Product, PriceHistory, ProductStats, DealSnapshot

logger = logging.getLogger(__name__)

_TOLERANCE = 0.011  # float karsilastirma toleransi


# ---------------------------------------------------------------------------
# Ana giris noktasi
# ---------------------------------------------------------------------------

def compute_stats_for_source(source_id: int) -> int:
    """Bir kaynaga ait tum urunlerin istatistiklerini gunceller. Islenen urun sayisini dondurur."""
    products = Product.query.filter_by(source_id=source_id).all()
    count = 0
    for p in products:
        try:
            compute_product_stats(p)
            count += 1
        except Exception as exc:
            logger.error("Stats hesaplanamadi product_id=%s: %s", p.id, exc)
    db.session.flush()
    return count


def compute_all_stats() -> int:
    """Tum urunlerin istatistiklerini gunceller. Islenen urun sayisini dondurur."""
    products = Product.query.all()
    count = 0
    for p in products:
        try:
            compute_product_stats(p)
            count += 1
        except Exception as exc:
            logger.error("Stats hesaplanamadi product_id=%s: %s", p.id, exc)
    db.session.flush()
    return count


# ---------------------------------------------------------------------------
# Tekil urun stats hesabi
# ---------------------------------------------------------------------------

def compute_product_stats(product: Product) -> ProductStats | None:
    """Bir urun icin ProductStats hesaplar veya gunceller. Ayni zamanda DealSnapshot'i da gunceller."""
    now = datetime.now(timezone.utc)

    history = (
        PriceHistory.query
        .filter_by(product_id=product.id)
        .order_by(PriceHistory.recorded_at.asc())
        .all()
    )

    if not history or product.current_price is None:
        _deactivate_snapshot(product.id)
        return None

    # (datetime_utc, price) listeleri
    price_points = []
    for h in history:
        if h.price is None:
            continue
        dt = h.recorded_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        price_points.append((dt, h.price))

    if not price_points:
        _deactivate_snapshot(product.id)
        return None

    def prices_since(days: int) -> list[float]:
        cutoff = now - timedelta(days=days)
        return [p for dt, p in price_points if dt >= cutoff]

    all_prices = [p for _, p in price_points]
    p7   = prices_since(7)
    p30  = prices_since(30)
    p90  = prices_since(90)
    p180 = prices_since(180)

    def safe_min(lst): return round(min(lst), 2) if lst else None
    def safe_avg(lst): return round(sum(lst) / len(lst), 2) if lst else None

    lowest_all  = safe_min(all_prices)
    lowest_7d   = safe_min(p7)
    lowest_30d  = safe_min(p30)
    lowest_90d  = safe_min(p90)
    lowest_180d = safe_min(p180)

    avg_7d  = safe_avg(p7)
    avg_30d = safe_avg(p30)
    avg_90d = safe_avg(p90)

    cur = product.current_price

    is_atl  = lowest_all is not None and cur <= lowest_all + _TOLERANCE
    is_30d  = lowest_30d is not None and cur <= lowest_30d + _TOLERANCE
    is_90d  = lowest_90d is not None and cur <= lowest_90d + _TOLERANCE

    # Kac gundir bu fiyat seviyesinde: geriye dogru surekli eslesen pencere
    earliest_at_cur = price_points[-1][0]
    for dt, price in reversed(price_points):
        if abs(price - cur) <= _TOLERANCE:
            earliest_at_cur = dt
        else:
            break
    days_at_low = (now - earliest_at_cur).days

    # Kaydet / guncelle
    stats = ProductStats.query.filter_by(product_id=product.id).first()
    if stats is None:
        stats = ProductStats(product_id=product.id)
        db.session.add(stats)

    stats.lowest_price_all_time = lowest_all
    stats.lowest_price_7d       = lowest_7d
    stats.lowest_price_30d      = lowest_30d
    stats.lowest_price_90d      = lowest_90d
    stats.lowest_price_180d     = lowest_180d
    stats.average_price_7d      = avg_7d
    stats.average_price_30d     = avg_30d
    stats.average_price_90d     = avg_90d
    stats.is_all_time_low       = is_atl
    stats.is_30d_low            = is_30d
    stats.is_90d_low            = is_90d
    stats.days_at_current_low   = days_at_low
    stats.updated_at            = now

    # DealSnapshot guncelle
    _update_deal_snapshot(product, stats, now)

    return stats


# ---------------------------------------------------------------------------
# Firsat skoru (istatistik destekli)
# ---------------------------------------------------------------------------

def deal_score(product: Product, stats: ProductStats | None = None) -> float:
    """
    Tarihsel veriye dayali firsat skoru.
    stats yoksa basit indirim orani bazli skor doner.
    """
    if not product.discount_percent:
        return 0.0

    disc = product.discount_percent
    score = 0.0

    if product.vertical == 'gaming':
        if disc >= 50:
            score += disc * 1.2
        elif disc >= 30:
            score += disc * 1.0

        if stats:
            if stats.is_all_time_low:
                score += 60
            elif stats.is_90d_low:
                score += 40
            elif stats.is_30d_low:
                score += 25

        if product.region == 'TR':
            score += 15

    else:  # ecommerce / fashion
        if disc >= 20:
            score += disc * 1.5

        if stats:
            if stats.is_all_time_low:
                score += 50
            elif stats.is_90d_low:
                score += 35
            elif stats.is_30d_low:
                score += 20

            if stats.average_price_30d and product.current_price:
                if product.current_price < stats.average_price_30d:
                    pct_below = (
                        (stats.average_price_30d - product.current_price)
                        / stats.average_price_30d * 100
                    )
                    score += pct_below

        if product.stock_status == 'in_stock':
            score += 10

    return round(score, 1)


def analysis_lines(product: Product, stats: ProductStats | None) -> list[str]:
    """Kullaniciya gosterilecek analiz cumlelerini uretir."""
    if not stats or product.current_price is None:
        return []

    lines = []

    if stats.is_all_time_low:
        lines.append("Bu urun tum zamanlarin en dusuk fiyatinda.")
    elif stats.is_90d_low:
        lines.append("Bu urun son 90 gunun en dusuk fiyatinda.")
    elif stats.is_30d_low:
        lines.append("Bu urun son 30 gunun en dusuk fiyatinda.")

    if stats.days_at_current_low > 1:
        lines.append(f"Bu fiyat {stats.days_at_current_low} gundir gecerli.")

    if stats.average_price_30d and product.current_price < stats.average_price_30d:
        pct = round(
            (stats.average_price_30d - product.current_price)
            / stats.average_price_30d * 100
        )
        lines.append(f"30 gunluk ortalamanin %{pct} altinda.")

    if stats.lowest_price_all_time and not stats.is_all_time_low:
        diff = round(product.current_price - stats.lowest_price_all_time, 2)
        if diff > 0:
            cur_str = _fmt(product.current_price)
            atl_str = _fmt(stats.lowest_price_all_time)
            lines.append(
                f"Tum zamanlarin en dusugu {atl_str} — simdi {cur_str}."
            )

    return lines


def _fmt(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------------------
# DealSnapshot yardimcilari
# ---------------------------------------------------------------------------

def _deactivate_snapshot(product_id: int) -> None:
    DealSnapshot.query.filter_by(product_id=product_id, is_active=True).update(
        {'is_active': False}, synchronize_session=False
    )


def _update_deal_snapshot(product: Product, stats: ProductStats, now: datetime) -> None:
    if not product.current_price or not product.discount_percent:
        _deactivate_snapshot(product.id)
        return

    score = deal_score(product, stats)
    if score < 1:
        _deactivate_snapshot(product.id)
        return

    # Analiz metinlerinden neden cumlesi olustur
    parts = []
    if stats.is_all_time_low:
        parts.append("Tum zamanlarin en dusuğu")
    elif stats.is_90d_low:
        parts.append("Son 90 gunun en dusuğu")
    elif stats.is_30d_low:
        parts.append("Son 30 gunun en dusuğu")
    if stats.days_at_current_low > 1:
        parts.append(f"{stats.days_at_current_low} gundir bu fiyatta")
    if stats.average_price_30d and product.current_price < stats.average_price_30d:
        pct = round(
            (stats.average_price_30d - product.current_price)
            / stats.average_price_30d * 100
        )
        parts.append(f"30g ortalamanin %{pct} alti")
    if not parts:
        parts.append(f"%{int(product.discount_percent)} indirim")

    reason = " · ".join(parts)

    snap = DealSnapshot.query.filter_by(product_id=product.id, is_active=True).first()
    if snap:
        snap.deal_score = score
        snap.deal_reason = reason
        snap.current_price = product.current_price
        snap.previous_average_price = stats.average_price_30d
        snap.discount_percent = product.discount_percent
        snap.last_detected_at = now
    else:
        snap = DealSnapshot(
            product_id=product.id,
            deal_score=score,
            deal_reason=reason,
            current_price=product.current_price,
            previous_average_price=stats.average_price_30d,
            discount_percent=product.discount_percent,
            is_active=True,
            first_detected_at=now,
            last_detected_at=now,
        )
        db.session.add(snap)
