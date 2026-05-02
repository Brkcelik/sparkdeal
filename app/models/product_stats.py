from datetime import datetime
from app import db


class ProductStats(db.Model):
    __tablename__ = 'product_stats'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, unique=True)

    lowest_price_all_time = db.Column(db.Float, nullable=True)
    lowest_price_7d       = db.Column(db.Float, nullable=True)
    lowest_price_30d      = db.Column(db.Float, nullable=True)
    lowest_price_90d      = db.Column(db.Float, nullable=True)
    lowest_price_180d     = db.Column(db.Float, nullable=True)

    average_price_7d  = db.Column(db.Float, nullable=True)
    average_price_30d = db.Column(db.Float, nullable=True)
    average_price_90d = db.Column(db.Float, nullable=True)

    days_at_current_low = db.Column(db.Integer, default=0)
    is_all_time_low     = db.Column(db.Boolean, default=False)
    is_30d_low          = db.Column(db.Boolean, default=False)
    is_90d_low          = db.Column(db.Boolean, default=False)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ProductStats product={self.product_id}>'
