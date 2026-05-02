"""Scraper kayıt defteri — kaynak adını scraper sınıfına eşler."""
from __future__ import annotations


def get_scraper_class(source_name: str):
    """
    Kaynak adına göre scraper sınıfını döndürür.
    Bilinmeyen kaynaklar için None döner.
    """
    key = source_name.lower().replace(' ', '_').replace('-', '_')

    from app.scrapers.ecommerce.teknosa import TeknosaScaper
    from app.scrapers.ecommerce.hepsiburada import HepsiburadaScraper
    from app.scrapers.ecommerce.n11 import N11Scraper
    from app.scrapers.ecommerce.trendyol import TrendyolScraper
    from app.scrapers.ecommerce.amazon_tr import AmazonTRScraper
    from app.scrapers.fashion.superstep import SuperstepScraper
    from app.scrapers.gaming.steam_api import SteamScraper

    registry: dict[str, type] = {
        'teknosa':      TeknosaScaper,
        'hepsiburada':  HepsiburadaScraper,
        'n11':          N11Scraper,
        'trendyol':     TrendyolScraper,
        'amazon_tr':    AmazonTRScraper,
        'superstep':    SuperstepScraper,
        'steam':        SteamScraper,
    }

    return registry.get(key)


def list_scrapers() -> list[str]:
    """Kayıtlı tüm scraper adlarını döndürür."""
    return ['teknosa', 'hepsiburada', 'n11', 'trendyol', 'amazon_tr', 'superstep', 'steam']
