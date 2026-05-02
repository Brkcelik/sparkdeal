from flask import Blueprint, render_template
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
