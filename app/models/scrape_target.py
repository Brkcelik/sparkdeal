from datetime import datetime
from app import db


class ScrapeTarget(db.Model):
    __tablename__ = 'scrape_targets'

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('sources.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(1000), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    min_discount_percent = db.Column(db.Float, default=0)
    scrape_interval_minutes = db.Column(db.Integer, default=60)
    last_scraped_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    scrape_runs = db.relationship(
        'ScrapeRun', backref='target', lazy='dynamic',
        order_by='ScrapeRun.created_at.desc()'
    )

    def __repr__(self):
        return f'<ScrapeTarget {self.title}>'
