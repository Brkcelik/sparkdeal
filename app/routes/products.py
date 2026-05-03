from flask import Blueprint, render_template, request, abort
from app.models import Product, Source

bp = Blueprint('products', __name__)

PER_PAGE = 24

VERTICAL_TITLES = {
    'ecommerce': 'E-ticaret',
    'fashion': 'Moda & Spor',
    'gaming': 'Oyun İndirimleri',
}

SORT_OPTIONS = {
    'deal_score': 'Fırsat Skoruna Göre',
    'discount': 'İndirim Oranına Göre',
    'price_asc': 'En Ucuz Önce',
    'price_desc': 'En Pahalı Önce',
    'newest': 'En Yeni Önce',
}


@bp.route('/products')
def list():
    vertical = request.args.get('vertical')
    source_id = request.args.get('source_id', type=int)
    min_discount = request.args.get('min_discount', type=float)
    only_instock = request.args.get('instock') == '1'
    search = request.args.get('q', '').strip()
    sort = request.args.get('sort', 'deal_score')
    platform = request.args.get('platform')
    region = request.args.get('region')
    gender = request.args.get('gender')
    page = request.args.get('page', 1, type=int)

    query = Product.query

    if vertical:
        query = query.filter_by(vertical=vertical)
    if source_id:
        query = query.filter_by(source_id=source_id)
    if min_discount is not None:
        query = query.filter(Product.discount_percent >= min_discount)
    if only_instock:
        query = query.filter_by(stock_status='in_stock')
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    if platform:
        query = query.filter_by(platform=platform)
    if region:
        query = query.filter_by(region=region)
    if gender:
        query = query.filter_by(gender=gender)

    if sort == 'discount':
        query = query.order_by(Product.discount_percent.desc())
    elif sort == 'price_asc':
        query = query.order_by(Product.current_price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.current_price.desc())
    elif sort == 'newest':
        query = query.order_by(Product.first_seen_at.desc())
    else:
        query = query.order_by(Product.discount_percent.desc())

    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)
    products = pagination.items

    if sort == 'deal_score':
        products = sorted(products, key=lambda p: p.deal_score, reverse=True)

    sources = Source.query.filter_by(is_active=True)
    if vertical:
        sources = sources.filter_by(vertical=vertical)
    sources = sources.order_by(Source.name).all()

    page_title = VERTICAL_TITLES.get(vertical, 'Tüm Ürünler')

    return render_template(
        'products/list.html',
        products=products,
        pagination=pagination,
        sources=sources,
        page_title=page_title,
        vertical=vertical,
        current_source_id=source_id,
        min_discount=min_discount,
        only_instock=only_instock,
        search=search,
        sort=sort,
        sort_options=SORT_OPTIONS,
        platform=platform,
        region=region,
        gender=gender,
    )


@bp.route('/products/<int:product_id>')
def detail(product_id):
    product = Product.query.get_or_404(product_id)
    history = product.price_history.limit(60).all()

    # Fiyat değişim yönünü hesapla (desc sıralı: index 0 en yeni)
    for i, h in enumerate(history):
        if i < len(history) - 1:
            diff = h.price - history[i + 1].price
            h.price_change = round(diff, 2)
        else:
            h.price_change = 0

    prices = [h.price for h in history if h.price]
    stats = {}
    if prices:
        stats['min_price'] = min(prices)
        stats['max_price'] = max(prices)
        stats['avg_price'] = round(sum(prices) / len(prices), 2)
        stats['is_at_min'] = product.current_price and product.current_price <= stats['min_price'] + 0.01

    # Aynı normalized_name ile farklı kaynaklardaki ürünler
    cross_site = []
    if product.normalized_name:
        cross_site = (
            Product.query
            .filter(
                Product.normalized_name == product.normalized_name,
                Product.id != product.id,
                Product.current_price.isnot(None),
            )
            .order_by(Product.current_price.asc())
            .limit(10)
            .all()
        )

    return render_template(
        'products/detail.html',
        product=product,
        history=history,
        stats=stats,
        cross_site=cross_site,
    )
