"""Siteler arası ürün eşleştirme servisi — Faz 10."""
from collections import defaultdict
from typing import List

from app.models import Product
from app.services.scraper_service import normalize_product_name


_STOPWORDS = {'ve', 'ile', 'bir', 'bu', 'da', 'de', 'ta', 'te', 'mi', 'mu',
              'ic', 'in', 'the', 'for', 'and', 'with'}


def _word_set(normalized: str) -> set:
    """Anlamlı kelimeleri döndür (kısa/stop words hariç)."""
    return {w for w in normalized.split() if len(w) > 2 and w not in _STOPWORDS}


def jaccard_score(a: str, b: str) -> float:
    """İki normalleştirilmiş isim arasında Jaccard benzerlik skoru (0-1)."""
    sa, sb = _word_set(a), _word_set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def search_products(query: str) -> List[Product]:
    """
    Sorguyla eşleşen e-ticaret + moda ürünlerini döndür (gaming hariç).
    En az bir anlamlı kelime eşleşmeli; sonuçlar Jaccard >= 0.25 ile filtrele.
    """
    from app import db

    norm_q = normalize_product_name(query)
    words = _word_set(norm_q)
    if not words:
        return []

    # Her kelime için LIKE filtresi — OR ile birleştir
    like_filters = [Product.normalized_name.ilike(f'%{w}%') for w in words]

    candidates = (
        Product.query
        .filter(
            Product.vertical != 'gaming',
            Product.current_price.isnot(None),
            db.or_(*like_filters),
        )
        .order_by(Product.current_price.asc())
        .limit(300)
        .all()
    )

    scored = [
        (p, jaccard_score(norm_q, p.normalized_name or ''))
        for p in candidates
    ]
    scored = [(p, s) for p, s in scored if s >= 0.25]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [p for p, _ in scored[:80]]


def group_products(products: List[Product]) -> List[List[Product]]:
    """
    Ürünleri normalized_name'e göre tam eşleşmeyle grupla;
    ardından Jaccard >= 0.65 olan grupları birleştir.
    Her grup fiyata göre sıralanır; çok platformlu gruplar öne çıkar.
    """
    if not products:
        return []

    # 1. Tam eşleşme grupları
    exact: dict[str, list] = defaultdict(list)
    for p in products:
        key = p.normalized_name or f'__id_{p.id}'
        exact[key].append(p)

    # 2. Benzer grupları birleştir (Jaccard >= 0.65)
    keys = list(exact.keys())
    merged_into: dict[str, str] = {}  # child_key -> canonical_key

    for i, ka in enumerate(keys):
        canonical_a = merged_into.get(ka, ka)
        for j in range(i + 1, len(keys)):
            kb = keys[j]
            canonical_b = merged_into.get(kb, kb)
            if canonical_a == canonical_b:
                continue
            if jaccard_score(canonical_a, canonical_b) >= 0.65:
                # kb grubunu ka'ya birleştir
                merged_into[canonical_b] = canonical_a
                # Daha önce canonical_b'ye birleşmiş olanları da güncelle
                for k, v in list(merged_into.items()):
                    if v == canonical_b:
                        merged_into[k] = canonical_a

    # 3. Final grupları oluştur
    final: dict[str, list] = defaultdict(list)
    for key, prods in exact.items():
        canonical = merged_into.get(key, key)
        final[canonical].extend(prods)

    # 4. Her grup içinde fiyata göre sırala ve duplicate product_id temizle
    result = []
    for prods in final.values():
        seen_ids = set()
        unique = []
        for p in sorted(prods, key=lambda x: x.current_price or float('inf')):
            if p.id not in seen_ids:
                seen_ids.add(p.id)
                unique.append(p)
        result.append(unique)

    # 5. Çok platformlu gruplar önce, sonra en düşük fiyata göre
    result.sort(key=lambda g: (-len(g), g[0].current_price or float('inf')))
    return result


def compare_products(query: str) -> List[List[Product]]:
    """Sorgu için ürün karşılaştırma gruplarını döndür."""
    products = search_products(query)
    return group_products(products)
