from datetime import datetime
from app import db


class DealSnapshot(db.Model):
    __tablename__ = 'deal_snapshots'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    deal_score             = db.Column(db.Float, nullable=False)
    deal_reason            = db.Column(db.String(500), nullable=True)
    current_price          = db.Column(db.Float, nullable=False)
    previous_average_price = db.Column(db.Float, nullable=True)
    discount_percent       = db.Column(db.Float, nullable=True)

    is_active        = db.Column(db.Boolean, default=True)
    first_detected_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_detected_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<DealSnapshot product={self.product_id} score={self.deal_score}>'
