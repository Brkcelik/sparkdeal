from flask import Blueprint, render_template
from app.models import Product

bp = Blueprint('deals', __name__)


@bp.route('/deals')
def list():
    # Gerçek fırsat: indirim >= 30% ve stokta olan ürünler, skora göre sıralı
    products = (
        Product.query
        .filter(Product.discount_percent >= 30, Product.stock_status == 'in_stock')
        .all()
    )
    products.sort(key=lambda p: p.deal_score, reverse=True)

    gaming = [p for p in products if p.vertical == 'gaming']
    fashion = [p for p in products if p.vertical == 'fashion']
    ecommerce = [p for p in products if p.vertical == 'ecommerce']

    return render_template(
        'deals/list.html',
        all_deals=products,
        gaming=gaming,
        fashion=fashion,
        ecommerce=ecommerce,
    )
