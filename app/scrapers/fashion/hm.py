"""H&M TR scraper — JSON endpoint + HTML fallback.

H&M'in dahili JSON API'si (*.json endpoint) önce denenir;
başarısız olursa Playwright ile HTML parse edilir.
"""
import json
import logging
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = 'https://www2.hm.com'

# Bilinen JSON listing endpoint'leri — sırayla denenir
_JSON_PATHS = [
    '/tr_tr/sale.json',
    '/tr_tr/kadin/indirim.json',
    '/tr_tr/erkek/indirim.json',
    '/tr_tr/cocuk/indirim.json',
]

_JSON_PARAMS = {
    'offset': 0,
    'pagesize': 72,
    'sort': 'stock',
}


class HMScraper(BaseScraper):

    def scrape(self, target) -> list[dict]:
        # Target URL'den JSON path'i türet
        json_url = re.sub(r'\.html?$', '.json', target.url)
        if not json_url.endswith('.json'):
            json_url = target.url.rstrip('/') + '.json'

        session = self.make_session()
        session.headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        session.headers['X-Requested-With'] = 'XMLHttpRequest'
        self.warm_session(session, BASE_URL + '/tr_tr/')

        # JSON endpoint dene
        products = self._try_json(session, json_url, target)
        if products:
            return products

        # Playwright ile HTML fallback
        return self._scrape_playwright(target)

    def _try_json(self, session: requests.Session, url: str, target) -> list[dict]:
        try:
            r = session.get(url, params=_JSON_PARAMS, timeout=20)
        except Exception as exc:
            logger.debug("H&M JSON bağlantı hatası: %s", exc)
            return []

        if r.status_code != 200:
            logger.debug("H&M JSON HTTP %s: %s", r.status_code, url)
            return []

        try:
            data = r.json()
        except ValueError:
            return []

        # Olası yapılar: {"plpList": {"resultList": [...]}} veya {"products": [...]}
        result_list = (
            data.get('plpList', {}).get('resultList')
            or data.get('results')
            or data.get('products')
            or (data if isinstance(data, list) else [])
        )

        if not result_list:
            return []

        category = getattr(target, 'category', None)
        products = [p for item in result_list if (p := self._parse_json_item(item, category))]
        logger.info("H&M JSON: %d ürün (%s)", len(products), url)
        return products

    def _parse_json_item(self, item: dict, category) -> dict | None:
        name = item.get('name') or item.get('heading', '')
        if not name:
            return None

        default_article = item.get('defaultArticle', {})

        price_info = default_article.get('price') or item.get('price') or {}
        old_price_info = default_article.get('whitePrice') or item.get('whitePrice') or {}

        current_price = self._parse_price_obj(price_info)
        if current_price is None:
            current_price = self._parse_price_obj(old_price_info)

        sale_price = self._parse_price_obj(default_article.get('redPrice') or item.get('redPrice') or {})
        if sale_price:
            old_price = current_price
            current_price = sale_price
        else:
            old_price = self._parse_price_obj(old_price_info) if price_info != old_price_info else None

        if not current_price:
            return None

        discount = self.calc_discount(old_price, current_price)
        if discount is None and old_price:
            discount = self.calc_discount(old_price, current_price)

        product_url = item.get('url', '')
        if product_url and not product_url.startswith('http'):
            product_url = urljoin(BASE_URL, product_url)

        images = item.get('images') or default_article.get('images') or []
        image_url = ''
        if images:
            img = images[0] if isinstance(images[0], str) else images[0].get('url', '')
            image_url = 'https:' + img if img.startswith('//') else img

        article_id = default_article.get('code') or item.get('code') or item.get('id', '')

        stock = default_article.get('available', True)
        stock_status = 'in_stock' if stock else 'out_of_stock'

        return {
            'name': name,
            'current_price': current_price,
            'old_price': old_price,
            'discount_percent': discount,
            'product_url': product_url,
            'image_url': image_url,
            'brand': 'H&M',
            'category': category,
            'stock_status': stock_status,
            'external_id': str(article_id),
            'vertical': 'fashion',
            'gender': self.detect_gender(name, product_url),
            'platform': None,
            'region': None,
            'edition': None,
        }

    def _parse_price_obj(self, obj) -> float | None:
        if not obj:
            return None
        if isinstance(obj, (int, float)):
            return float(obj)
        val = obj.get('value') or obj.get('price') or obj.get('formattedValue', '')
        if val:
            return self.normalize_price(str(val))
        return None

    def _scrape_playwright(self, target) -> list[dict]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("H&M: Playwright kurulu değil, veri çekilemiyor")
            return []

        logger.info("H&M: Playwright fallback deneniyor (%s)", target.url)
        results = []
        try:
            from app.scrapers.playwright_base import _BROWSER_ARGS, _STEALTH_SCRIPT
            import time
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True, args=_BROWSER_ARGS)
                ctx = browser.new_context(
                    viewport={'width': 1366, 'height': 768},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36',
                    locale='tr-TR',
                )
                ctx.add_init_script(_STEALTH_SCRIPT)
                page = ctx.new_page()
                try:
                    page.goto(target.url, wait_until='domcontentloaded', timeout=30_000)
                    time.sleep(self.delay)
                    for _ in range(3):
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(1.5)
                    html = page.content()
                    results = self._parse_html(html, target)
                except Exception as exc:
                    logger.error("H&M Playwright hatası: %s", exc)
                finally:
                    ctx.close()
                    browser.close()
        except Exception as exc:
            logger.error("H&M Playwright başlatma hatası: %s", exc)
        return results

    def _parse_html(self, html: str, target) -> list[dict]:
        soup = BeautifulSoup(html, 'lxml')
        cards = (
            soup.select('article.hm-product-item')
            or soup.select('[data-articlecode]')
            or soup.select('[data-article-id]')
            or soup.select('[class*="product-item"]')
        )
        if not cards:
            logger.warning("H&M HTML: ürün kartı bulunamadı")
            return []

        category = getattr(target, 'category', None)
        products = [p for card in cards if (p := self._parse_html_card(card, category))]
        logger.info("H&M HTML: %d ürün", len(products))
        return products

    def _parse_html_card(self, card, category) -> dict | None:
        article_id = card.get('data-articlecode') or card.get('data-article-id', '')
        link = card.select_one('a[href]')
        if not link:
            return None
        product_url = urljoin(BASE_URL, link.get('href', ''))

        name_el = (
            card.select_one('[class*="product-item-heading"]')
            or card.select_one('h2')
            or card.select_one('h3')
        )
        name = name_el.get_text(strip=True) if name_el else ''
        if not name:
            return None

        price_el = card.select_one('[class*="sale"]') or card.select_one('[class*="price-value"]')
        old_el = card.select_one('s') or card.select_one('[class*="regular-price"]')

        current_price = self.normalize_price(price_el.get_text() if price_el else '')
        old_price = self.normalize_price(old_el.get_text() if old_el else '')
        if not current_price:
            return None

        img = card.select_one('img')
        image_url = ''
        if img:
            image_url = img.get('src') or img.get('data-src') or ''
            if image_url.startswith('//'):
                image_url = 'https:' + image_url

        return {
            'name': name,
            'current_price': current_price,
            'old_price': old_price,
            'discount_percent': self.calc_discount(old_price, current_price),
            'product_url': product_url,
            'image_url': image_url,
            'brand': 'H&M',
            'category': category,
            'stock_status': 'in_stock',
            'external_id': article_id or self._extract_id(product_url),
            'vertical': 'fashion',
            'gender': self.detect_gender(name, product_url),
            'platform': None,
            'region': None,
            'edition': None,
        }

    def _extract_id(self, url: str) -> str:
        m = re.search(r'/(\d{6,})(?:[?/.]|$)', url)
        return m.group(1) if m else url.split('?')[0].rstrip('/').split('/')[-1]
