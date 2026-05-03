"""Scraper kayıt defteri — kaynak adını scraper sınıfına eşler."""
from __future__ import annotations


def get_scraper_class(source_name: str):
    """
    Kaynak adına göre scraper sınıfını döndürür.
    Bilinmeyen kaynaklar için None döner.
    """
    key = source_name.lower().replace(' ', '_').replace('-', '_').replace('&', '_')

    from app.scrapers.ecommerce.teknosa import TeknosaScaper
    from app.scrapers.ecommerce.hepsiburada import HepsiburadaScraper
    from app.scrapers.ecommerce.n11 import N11Scraper
    from app.scrapers.ecommerce.trendyol import TrendyolScraper
    from app.scrapers.ecommerce.amazon_tr import AmazonTRScraper
    from app.scrapers.fashion.superstep import SuperstepScraper
    from app.scrapers.fashion.hm import HMScraper
    from app.scrapers.fashion.sneaksup import SneaksupScraper
    from app.scrapers.fashion.sneakersonline import SneakersonlineScraper
    from app.scrapers.fashion.bershka import BershkaScraper
    from app.scrapers.fashion.pullandbear import PullandbearScraper
    from app.scrapers.gaming.steam_api import SteamScraper
    from app.scrapers.gaming.epic_games import EpicGamesScraper

    registry: dict[str, type] = {
        # E-ticaret
        'teknosa':          TeknosaScaper,
        'hepsiburada':      HepsiburadaScraper,
        'n11':              N11Scraper,
        'trendyol':         TrendyolScraper,
        'amazon_tr':        AmazonTRScraper,
        # Moda & Spor
        'superstep':        SuperstepScraper,
        'h_m_tr':           HMScraper,
        'hm':               HMScraper,
        'sneaksup':         SneaksupScraper,
        'sneakersonline':   SneakersonlineScraper,
        'bershka_tr':       BershkaScraper,
        'bershka':          BershkaScraper,
        'pull_bear_tr':     PullandbearScraper,
        'pullandbear':      PullandbearScraper,
        # Oyun
        'steam':            SteamScraper,
        'epic_games':       EpicGamesScraper,
        'epic':             EpicGamesScraper,
    }

    return registry.get(key)


def list_scrapers() -> list[str]:
    """Kayıtlı tüm scraper adlarını döndürür."""
    return [
        'teknosa', 'hepsiburada', 'n11', 'trendyol', 'amazon_tr',
        'superstep', 'hm', 'sneaksup', 'sneakersonline', 'bershka', 'pullandbear',
        'steam', 'epic_games',
    ]
