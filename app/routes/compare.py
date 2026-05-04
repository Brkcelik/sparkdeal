"""Faz 10 — Çapraz platform fiyat karşılaştırma sayfası."""
from flask import Blueprint, render_template, request

bp = Blueprint('compare', __name__)


@bp.route('/compare')
def index():
    query = request.args.get('q', '').strip()
    groups = []
    total_products = 0
    multi_platform_count = 0

    if len(query) >= 2:
        from app.services.matching_service import compare_products
        groups = compare_products(query)
        total_products = sum(len(g) for g in groups)
        multi_platform_count = sum(1 for g in groups if len(g) > 1)

    return render_template(
        'compare/index.html',
        query=query,
        groups=groups,
        total_products=total_products,
        multi_platform_count=multi_platform_count,
    )
