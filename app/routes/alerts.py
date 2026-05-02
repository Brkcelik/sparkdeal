from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models import PriceAlert, Product, Source

bp = Blueprint('alerts', __name__)


@bp.route('/alerts')
def list():
    active   = PriceAlert.query.filter_by(is_active=True).order_by(PriceAlert.created_at.desc()).all()
    inactive = PriceAlert.query.filter_by(is_active=False).order_by(PriceAlert.created_at.desc()).all()

    # Ürün bazlı alarm oluştururken ürün seçimi için
    prefill_product_id = request.args.get('product_id', type=int)
    prefill_product = Product.query.get(prefill_product_id) if prefill_product_id else None

    products_sample = (
        Product.query
        .filter(Product.current_price.isnot(None))
        .order_by(Product.name)
        .limit(200)
        .all()
    )
    sources = Source.query.order_by(Source.name).all()

    return render_template(
        'alerts/list.html',
        active=active,
        inactive=inactive,
        prefill_product=prefill_product,
        products_sample=products_sample,
        sources=sources,
    )


@bp.route('/alerts', methods=['POST'])
def create():
    alarm_type = request.form.get('alarm_type', 'price')

    alert = PriceAlert(alarm_type=alarm_type, is_active=True)

    if alarm_type == 'price':
        product_id = request.form.get('product_id', type=int)
        target_price = request.form.get('target_price', type=float)
        if not product_id or not target_price:
            flash('Hedef fiyat alarmı için ürün ve hedef fiyat gereklidir.', 'error')
            return redirect(url_for('alerts.list'))
        alert.product_id = product_id
        alert.target_price = target_price

    elif alarm_type == 'atl':
        product_id = request.form.get('product_id', type=int)
        if not product_id:
            flash('ATL alarmı için ürün seçimi gereklidir.', 'error')
            return redirect(url_for('alerts.list'))
        alert.product_id = product_id

    elif alarm_type == 'keyword':
        keyword = (request.form.get('keyword') or '').strip()
        if not keyword:
            flash('Anahtar kelime alarmı için kelime gereklidir.', 'error')
            return redirect(url_for('alerts.list'))
        alert.keyword = keyword
        alert.min_discount_percent = request.form.get('min_discount_percent', type=float) or 20.0
        alert.vertical = request.form.get('vertical') or None

    elif alarm_type == 'category':
        category = (request.form.get('category') or '').strip()
        if not category:
            flash('Kategori alarmı için kategori adı gereklidir.', 'error')
            return redirect(url_for('alerts.list'))
        alert.category = category
        alert.min_discount_percent = request.form.get('min_discount_percent', type=float) or 20.0
        alert.vertical = request.form.get('vertical') or None

    db.session.add(alert)
    db.session.commit()
    flash(f'Alarm oluşturuldu: {alert.description}', 'success')
    return redirect(url_for('alerts.list'))


@bp.route('/alerts/<int:alert_id>/toggle', methods=['POST'])
def toggle(alert_id):
    alert = PriceAlert.query.get_or_404(alert_id)
    alert.is_active = not alert.is_active
    db.session.commit()
    state = 'aktif' if alert.is_active else 'pasif'
    flash(f'Alarm {state} yapıldı.', 'success')
    return redirect(url_for('alerts.list'))


@bp.route('/alerts/<int:alert_id>/delete', methods=['POST'])
def delete(alert_id):
    alert = PriceAlert.query.get_or_404(alert_id)
    db.session.delete(alert)
    db.session.commit()
    flash('Alarm silindi.', 'success')
    return redirect(url_for('alerts.list'))


@bp.route('/alerts/check', methods=['POST'])
def check():
    """Tüm ürünleri tarayarak aktif alarmları manuel kontrol et."""
    from app.services.alert_service import check_all_alerts
    triggered = check_all_alerts()
    db.session.commit()
    if triggered:
        flash(f'{triggered} alarm tetiklendi.', 'success')
    else:
        flash('Tetiklenecek alarm bulunamadı.', 'warning')
    return redirect(url_for('alerts.list'))
