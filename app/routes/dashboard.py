from flask import Blueprint, render_template
from app import db
from app.models import Product, Source, ProductStats, ScrapeRun, PriceHistory

bp = Blueprint('dashboard', __name__)


@bp.route('/')
def index():
    total_products = Product.query.count()
    on_sale = Product.query.filter(Product.discount_percent >= 20).count()
    sources_active = Source.query.filter_by(is_active=True).count()

    atl_count = (
        db.session.query(ProductStats)
        .filter_by(is_all_time_low=True)
        .count()
    )

    # En iyi fırsat skoru — stats hesaplanmış ürünler önce gösterilir
    top_deals = (
        Product.query
        .filter(Product.discount_percent >= 20, Product.stock_status == 'in_stock')
        .order_by(Product.discount_percent.desc())
        .limit(24)
        .all()
    )
    top_deals.sort(key=lambda p: p.deal_score, reverse=True)
    top_deals = top_deals[:6]

    # En yüksek indirim oranına sahip 6 ürün
    biggest_discounts = (
        Product.query
        .filter(Product.discount_percent.isnot(None))
        .order_by(Product.discount_percent.desc())
        .limit(6)
        .all()
    )

    # Vertical bazlı ürün sayıları
    ecommerce_count = Product.query.filter_by(vertical='ecommerce').count()
    fashion_count = Product.query.filter_by(vertical='fashion').count()
    gaming_count = Product.query.filter_by(vertical='gaming').count()

    # Son tarama zamanları
    sources = (
        Source.query
        .filter_by(is_active=True)
        .order_by(Source.last_scraped_at.desc().nullslast())
        .all()
    )

    # Hata veren kaynaklar
    errored_sources = (
        Source.query
        .filter(Source.error_count > 0)
        .order_by(Source.error_count.desc())
        .all()
    )

    # Son başarısız tarama logları
    recent_errors = (
        ScrapeRun.query
        .filter_by(status='error')
        .order_by(ScrapeRun.created_at.desc())
        .limit(5)
        .all()
    )

    # Dashboard sparkline: top deals + biggest discounts için son fiyat noktaları
    sparkline_data = {}
    all_dash_products = {p.id: p for p in top_deals + biggest_discounts}
    for pid in all_dash_products:
        pts = (
            PriceHistory.query
            .filter_by(product_id=pid)
            .order_by(PriceHistory.recorded_at.asc())
            .limit(20)
            .all()
        )
        prices = [round(h.price, 2) for h in pts if h.price]
        if len(prices) >= 2:
            sparkline_data[pid] = prices

    stats = {
        'total_products': total_products,
        'on_sale': on_sale,
        'sources_active': sources_active,
        'ecommerce_count': ecommerce_count,
        'fashion_count': fashion_count,
        'gaming_count': gaming_count,
        'atl_count': atl_count,
    }

    return render_template(
        'dashboard.html',
        stats=stats,
        top_deals=top_deals,
        biggest_discounts=biggest_discounts,
        sources=sources,
        errored_sources=errored_sources,
        recent_errors=recent_errors,
        sparkline_data=sparkline_data,
    )
