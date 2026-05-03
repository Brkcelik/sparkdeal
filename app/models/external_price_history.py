"""ITAD (IsThereAnyDeal) kaynaklı tarihsel fiyat geçmişi."""
from app import db


class ExternalPriceHistory(db.Model):
    __tablename__ = 'external_price_history'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    source = db.Column(db.String(20), nullable=False, default='itad')
    shop = db.Column(db.String(50))
    price = db.Column(db.Float, nullable=False)
    regular_price = db.Column(db.Float)
    currency = db.Column(db.String(10), default='USD')
    cut = db.Column(db.Integer)
    url = db.Column(db.Text)
    recorded_at = db.Column(db.DateTime, nullable=False)

    product = db.relationship(
        'Product',
        backref=db.backref('external_price_history', lazy='dynamic'),
    )
