"""Geçici site yapısı inceleme scripti — Faz 3 scraper geliştirme için."""
import time
import requests
from bs4 import BeautifulSoup
from collections import Counter

# Gerçekçi tarayıcı header'ları
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/125.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0',
}


def probe(name, url, card_selectors):
    print(f"\n=== {name} ===")
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        # Önce ana sayfayı ziyaret et (cookie al)
        base_url = '/'.join(url.split('/')[:3])
        session.get(base_url, timeout=10)
        time.sleep(1)

        r = session.get(url, timeout=14)
        print(f"HTTP {r.status_code}  ({len(r.text)} byte)")
        soup = BeautifulSoup(r.text, 'lxml')

        for sel in card_selectors:
            items = soup.select(sel)
            if items:
                print(f"  ÇALIŞAN: {repr(sel)}  →  {len(items)} kart")
                first = items[0]
                snippet = str(first)[:280].replace('\n', ' ')
                print(f"  Snippet: {snippet}")
                texts = [t.strip() for t in first.stripped_strings][:5]
                print(f"  Metinler: {texts}")
                return
        print("  Hiçbir selector çalışmadı")
        all_classes = []
        for tag in soup.find_all(True):
            all_classes.extend(tag.get('class', []))
        keywords = ['product', 'item', 'card', 'prd']
        top = [c for c, _ in Counter(all_classes).most_common(30)
               if any(k in c.lower() for k in keywords)]
        print(f"  İlgili class'lar: {top[:10]}")
    except Exception as e:
        print(f"  HATA: {e}")


def probe_steam():
    print("\n=== Steam API ===")
    try:
        r = requests.get(
            'https://store.steampowered.com/api/featuredcategories/?cc=tr&l=turkish',
            headers=HEADERS, timeout=14
        )
        data = r.json()
        specials = data.get('specials', {}).get('items', [])
        print(f"  HTTP {r.status_code}  specials: {len(specials)} oyun")
        for g in specials[:3]:
            price = g.get('final_price', 0) / 100
            print(f"    [{g.get('discount_percent')}%] {g.get('name')} — {price:.2f} TL")
        # JSON key'lerini de göster (ilk oyun)
        if specials:
            print(f"  Mevcut key'ler: {list(specials[0].keys())}")
    except Exception as e:
        print(f"  HATA: {e}")


if __name__ == '__main__':
    probe('Teknosa kampanyalı', 'https://www.teknosa.com/kampanyali-urunler', [
        'li.col.pr-item', 'li[data-id]', '[class*="product-item"]',
        '[class*="productCard"]', 'article[class*="product"]', 'li[class*="col"]',
        'div[class*="product"]',
    ])
    time.sleep(2)

    probe('Teknosa indirimli', 'https://www.teknosa.com/indirimli-urunler-c-10003', [
        'li.col.pr-item', 'li[data-id]', '[class*="product-item"]',
        '[class*="productCard"]', 'li[class*="col"]',
    ])
    time.sleep(2)

    probe('Hepsiburada indirimli', 'https://www.hepsiburada.com/indirimli-urunler', [
        'li[data-pid]', '[class*="productCard"]', '[class*="ProductCard"]',
        'li[class*="product"]', 'article',
    ])
    time.sleep(2)

    # N11 güncel URL'leri dene
    for n11_url in [
        'https://www.n11.com/indirimli-urunler',
        'https://www.n11.com/kampanya',
        'https://www.n11.com/indirim',
    ]:
        probe(f'N11 {n11_url.split("/")[-1]}', n11_url, [
            'li.column.p-box', '.p-box', '[class*="cardView"]',
            '[class*="productCard"]', 'li[class*="column"]',
        ])
        time.sleep(2)

    probe_steam()
