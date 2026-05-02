from datetime import datetime
from app import db


class ScrapeRun(db.Model):
    __tablename__ = 'scrape_runs'

    id        = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('sources.id'),        nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('scrape_targets.id'), nullable=True)

    status                = db.Column(db.String(20), default='pending')  # pending / running / success / error
    found_count           = db.Column(db.Integer, default=0)
    new_product_count     = db.Column(db.Integer, default=0)
    updated_product_count = db.Column(db.Integer, default=0)
    error_message         = db.Column(db.Text, nullable=True)

    started_at  = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def duration_seconds(self):
        if self.started_at and self.finished_at:
            return round((self.finished_at - self.started_at).total_seconds(), 1)
        return None

    def __repr__(self):
        return f'<ScrapeRun source={self.source_id} status={self.status}>'
