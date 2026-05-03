from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models import Source

bp = Blueprint('sources', __name__)


@bp.route('/sources')
def list():
    ecommerce = Source.query.filter_by(vertical='ecommerce').order_by(Source.name).all()
    fashion = Source.query.filter_by(vertical='fashion').order_by(Source.name).all()
    gaming = Source.query.filter_by(vertical='gaming').order_by(Source.name).all()

    return render_template(
        'sources/list.html',
        ecommerce=ecommerce,
        fashion=fashion,
        gaming=gaming,
    )


@bp.route('/sources/<int:source_id>/toggle', methods=['POST'])
def toggle(source_id):
    source = Source.query.get_or_404(source_id)
    source.is_active = not source.is_active
    db.session.commit()
    status = 'aktif' if source.is_active else 'pasif'
    flash(f'{source.name} {status} yapıldı.', 'success')
    return redirect(request.referrer or url_for('sources.list'))
