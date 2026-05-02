from datetime import datetime
from app import db


class Source(db.Model):
    __tablename__ = 'sources'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    base_url = db.Column(db.String(255), nullable=False)
    vertical = db.Column(db.String(20), nullable=False, default='ecommerce')  # ecommerce / fashion / gaming
    is_active = db.Column(db.Boolean, default=True)
    scraper_type = db.Column(db.String(20), default='requests')  # requests / playwright / api
    crawl_delay_seconds = db.Column(db.Integer, default=2)
    last_scraped_at = db.Column(db.DateTime, nullable=True)
    error_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship('Product', backref='source', lazy='dynamic')
    scrape_targets = db.relationship(
        'ScrapeTarget', backref='source', lazy='dynamic'
    )
    scrape_runs = db.relationship(
        'ScrapeRun', backref='source', lazy='dynamic',
        order_by='ScrapeRun.created_at.desc()'
    )
    source_alerts = db.relationship(
        'PriceAlert', foreign_keys='PriceAlert.source_id',
        backref='alert_source', lazy='dynamic'
    )

    VERTICAL_LABELS = {
        'ecommerce': 'E-ticaret',
        'fashion': 'Moda & Spor',
        'gaming': 'Oyun',
    }

    @property
    def vertical_label(self):
        return self.VERTICAL_LABELS.get(self.vertical, self.vertical)

    def __repr__(self):
        return f'<Source {self.name}>'
