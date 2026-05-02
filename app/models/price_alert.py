from datetime import datetime
from app import db


class PriceAlert(db.Model):
    __tablename__ = 'price_alerts'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    source_id  = db.Column(db.Integer, db.ForeignKey('sources.id'),  nullable=True)

    # price: hedef fiyat altı | atl: tüm zamanların en düşüğü
    # keyword: ürün adında kelime | category: kategori indirimi
    alarm_type   = db.Column(db.String(20), nullable=False, default='price')

    keyword              = db.Column(db.String(200), nullable=True)
    target_price         = db.Column(db.Float,       nullable=True)
    min_discount_percent = db.Column(db.Float,       nullable=True, default=20.0)
    category             = db.Column(db.String(100), nullable=True)
    vertical             = db.Column(db.String(20),  nullable=True)
    platform             = db.Column(db.String(50),  nullable=True)

    is_active         = db.Column(db.Boolean,  default=True)
    last_triggered_at = db.Column(db.DateTime, nullable=True)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

    ALARM_TYPE_LABELS = {
        'price':    'Hedef Fiyat',
        'atl':      'En Düşük Fiyat',
        'keyword':  'Anahtar Kelime',
        'category': 'Kategori İndirimi',
    }

    @property
    def type_label(self):
        return self.ALARM_TYPE_LABELS.get(self.alarm_type, self.alarm_type)

    @property
    def description(self):
        if self.alarm_type == 'price' and self.target_price:
            name = self.product.name[:40] if self.product else f'Ürün #{self.product_id}'
            return f'{name} → {self.target_price:,.0f} ₺ altına düşünce'
        if self.alarm_type == 'atl':
            name = self.product.name[:40] if self.product else f'Ürün #{self.product_id}'
            return f'{name} → tüm zamanların en düşüğüne ulaşınca'
        if self.alarm_type == 'keyword' and self.keyword:
            return f'"{self.keyword}" içeren ürün indirime girince'
        if self.alarm_type == 'category' and self.category:
            pct = f'%{self.min_discount_percent:.0f}+' if self.min_discount_percent else ''
            return f'{self.category} kategorisinde {pct} indirim olunca'
        return '—'

    def __repr__(self):
        return f'<PriceAlert type={self.alarm_type} product={self.product_id}>'
