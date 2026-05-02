from datetime import datetime
from app import db


class PriceHistory(db.Model):
    __tablename__ = 'price_history'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    old_price = db.Column(db.Float, nullable=True)
    discount_percent = db.Column(db.Float, nullable=True)
    stock_status = db.Column(db.String(20), nullable=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PriceHistory product={self.product_id} price={self.price}>'
