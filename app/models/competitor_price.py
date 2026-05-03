from datetime import datetime
from app import db


class CompetitorPrice(db.Model):
    __tablename__ = 'competitor_prices'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    source_name = db.Column(db.String(50), nullable=False)  # 'eneba', 'bynogame'
    price = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(10), default='TRY')
    url = db.Column(db.String(1000), nullable=True)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CompetitorPrice {self.source_name} {self.price}>'
