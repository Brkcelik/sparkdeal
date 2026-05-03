from datetime import datetime
from app import db


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('sources.id'), nullable=False)
    external_id = db.Column(db.String(255), nullable=True)
    name = db.Column(db.String(500), nullable=False)
    normalized_name = db.Column(db.String(500), nullable=True)
    brand = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    vertical = db.Column(db.String(20), nullable=False, default='ecommerce')
    platform = db.Column(db.String(50), nullable=True)   # gaming: PC / PS5 / Xbox / Nintendo
    region = db.Column(db.String(20), nullable=True)     # gaming: TR / EU / Global
    edition = db.Column(db.String(100), nullable=True)   # gaming: Standard / Deluxe vb.
    gender = db.Column(db.String(20), nullable=True)     # fashion: Erkek / Kadın / Unisex / Çocuk
    product_url = db.Column(db.String(1000), nullable=True)
    image_url = db.Column(db.String(1000), nullable=True)
    current_price = db.Column(db.Float, nullable=True)
    old_price = db.Column(db.Float, nullable=True)
    discount_percent = db.Column(db.Float, nullable=True)
    stock_status = db.Column(db.String(20), default='unknown')  # in_stock / out_of_stock / unknown
    currency = db.Column(db.String(10), default='TRY')          # TRY / USD / EUR
    first_seen_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    price_history = db.relationship(
        'PriceHistory', backref='product', lazy='dynamic',
        order_by='PriceHistory.recorded_at.desc()'
    )
    stats = db.relationship(
        'ProductStats', backref='product', uselist=False, lazy='joined',
        cascade='all, delete-orphan'
    )
    deal_snapshots = db.relationship(
        'DealSnapshot', backref='product', lazy='dynamic',
        order_by='DealSnapshot.last_detected_at.desc()',
        cascade='all, delete-orphan'
    )
    alerts = db.relationship(
        'PriceAlert', foreign_keys='PriceAlert.product_id',
        backref='product', lazy='dynamic'
    )

    @property
    def deal_score(self):
        from app.services.stats_service import deal_score as _calc
        return _calc(self, self.stats)

    @property
    def analysis_lines(self):
        from app.services.stats_service import analysis_lines as _lines
        return _lines(self, self.stats)

    @property
    def badge_atl(self):
        return self.stats is not None and self.stats.is_all_time_low

    @property
    def badge_30d(self):
        return (
            self.stats is not None
            and self.stats.is_30d_low
            and not self.stats.is_all_time_low
        )

    @property
    def badge_90d(self):
        return (
            self.stats is not None
            and self.stats.is_90d_low
            and not self.stats.is_30d_low
            and not self.stats.is_all_time_low
        )

    @property
    def score_tier(self):
        s = self.deal_score
        if s >= 120:
            return 'excellent'
        elif s >= 80:
            return 'good'
        elif s >= 40:
            return 'fair'
        return 'weak'

    @property
    def score_label(self):
        s = self.deal_score
        if s >= 120:
            return 'Çok İyi Fırsat'
        elif s >= 80:
            return 'İyi Fırsat'
        elif s >= 40:
            return 'Dikkate Değer'
        return 'Zayıf İndirim'

    def __repr__(self):
        return f'<Product {self.name[:40]}>'
