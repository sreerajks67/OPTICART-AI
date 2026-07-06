"""
fetch_product_images management command
----------------------------------------
Searches DuckDuckGo Images for each product and downloads a clean,
relevant product photo.

Improvements over v1:
- Smart query builder: extracts brand + product_type only (no specs/OPT IDs)
- Adds "product image buy online" to queries for shopping-site results
- Filters to type_image="photo" only (no clipart/illustrations)
- Prioritises results from known shopping domains (amazon, flipkart, etc.)
- Falls back to category-level query if brand-specific search fails

Usage
-----
python manage.py fetch_product_images --limit 100
python manage.py fetch_product_images --limit 10000 --skip-cached --delay 1.0
"""

import re
import time
from pathlib import Path

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from cart.models import Product


_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
})

_CACHE_DIR = None

# Trusted product-image domains — prefer these in search results
_PREFERRED_DOMAINS = (
    "amazon.com", "amazon.in", "flipkart.com", "bestbuy.com",
    "apple.com", "samsung.com", "mi.com", "lg.com",
    "puma.com", "adidas.com", "nike.com", "myntra.com",
    "nykaa.com", "reliancedigital.in", "croma.com",
    "ikea.com", "pepperfry.com", "urbanladder.com",
    "snapdeal.com", "tatacliq.com",
)

# ─────────────────────────────────────────────────────────────────────────────
# Query builder
# ─────────────────────────────────────────────────────────────────────────────

# Map category → generic product keyword for fallback queries
_CAT_FALLBACK = {
    "Electronics": "electronics gadget",
    "Fashion": "fashion clothing apparel",
    "Home & Furniture": "home furniture",
    "Beauty & Personal Care": "beauty cosmetics",
    "Sports & Fitness": "sports fitness equipment",
    "Books & Media": "book novel",
    "Toys & Kids": "toy kids",
    "Grocery & Food": "grocery food",
    "Automotive": "automotive car accessory",
    "Others": "product",
}

# Keywords that identify the item type in a product name
_ITEM_KEYWORDS = [
    # Tech
    "iphone", "galaxy", "redmi", "oneplus", "realme", "vivo", "oppo", "motorola",
    "macbook", "thinkpad", "inspiron", "pavilion", "vivobook", "aspire", "rog", "zenbook",
    "ipad", "tablet",
    "headphones", "earphones", "airpods", "earbuds", "speaker", "soundbar",
    "smartwatch", "watch",
    "television", "tv unit", "tv",
    "monitor", "display",
    "keyboard", "mouse", "gamepad", "controller", "console", "playstation", "xbox",
    "refrigerator", "fridge", "washing machine", "microwave", "air conditioner",
    "water purifier", "printer",
    # Fashion
    "sneakers", "shoes", "sandals", "boots",
    "jeans", "jacket", "hoodie", "shirt", "t-shirt", "dress", "kurta", "saree",
    "backpack", "bag", "wallet", "handbag",
    # Beauty
    "face wash", "moisturizer", "lipstick", "sunscreen", "shampoo", "serum", "perfume",
    # Home
    "sofa", "couch", "chair", "dining table", "table", "bed", "mattress",
    "wardrobe", "cabinet", "bookshelf", "tv unit",
    # Books
    "atomic habits", "psychology of money", "ikigai", "alchemist",
    "sapiens", "deep work", "rich dad",
    # Food
    "atta", "rice", "tea", "coffee", "cooking oil", "ghee", "biscuits",
    # Sports
    "cricket bat", "football", "yoga mat", "dumbbell", "cycle", "bicycle",
]


def _build_query(product_name, category_name):
    """
    Build a clean, targeted image search query.
    Strategy: keep brand + most specific item keyword + 'product image'
    """
    name = product_name or ""
    # Remove OPT ID
    name = re.sub(r'\s*\(OPT\d+\)\s*', ' ', name, flags=re.IGNORECASE)
    # Remove memory/storage specs
    name = re.sub(r'\b\d+\s*GB/\d+\s*GB\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\b\d+\s*GB\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\b\d+\s*TB\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\b\d+\s*kg\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\b\d+\.\d+\s*"?\b', '', name)  # screen sizes like 15.6"
    name = re.sub(r'\b(i3|i5|i7|i9|ryzen\s*\d|m[123])\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\b(ssd|hdd|ram|amoled|ips|oled|fhd|4k|hdr)\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+', ' ', name).strip()

    name_lower = name.lower()

    # Find the most specific item keyword present in the name
    found_item = None
    for kw in _ITEM_KEYWORDS:
        if kw in name_lower:
            found_item = kw
            break

    # Take first 3 words of cleaned name as brand+model
    first_words = name.split()[:3]
    base = " ".join(first_words)

    if found_item:
        query = f"{base} {found_item} product image"
    else:
        fallback = _CAT_FALLBACK.get(category_name, "product")
        query = f"{base} {fallback} product image"

    return query.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Search + download
# ─────────────────────────────────────────────────────────────────────────────

def _get_cache_dir():
    global _CACHE_DIR
    if _CACHE_DIR is None:
        _CACHE_DIR = Path(settings.MEDIA_ROOT) / "product_images"
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR


def _cached_path(product_id):
    d = _get_cache_dir()
    for ext in ("jpg", "jpeg", "png", "webp", "svg"):
        p = d / f"{product_id}.{ext}"
        if p.is_file() and p.stat().st_size > 0:
            return p
    return None


def _search_image(query, log=None):
    """
    Search DuckDuckGo Images for a product-relevant photo URL.
    1st pass: prefer results from known shopping domains.
    2nd pass: take any photo result.
    """
    try:
        from ddgs import DDGS
        ddgs = DDGS()
        results = list(ddgs.images(
            query,
            region="in-en",
            safesearch="moderate",
            type_image="photo",
            max_results=15,
        ))
    except Exception as e:
        if log:
            log(f"  Search error: {type(e).__name__}: {e}")
        return None

    if not results:
        return None

    # Pass 1: prefer trusted shopping domains
    for r in results:
        url = r.get("image", "")
        src = r.get("source", "").lower()
        if url and url.startswith("http") and not url.lower().endswith(".svg"):
            if any(d in src for d in _PREFERRED_DOMAINS):
                return url

    # Pass 2: any photo result that isn't SVG
    for r in results:
        url = r.get("image", "")
        if url and url.startswith("http") and not url.lower().endswith(".svg"):
            return url

    return None


def _download_image(url, timeout=12):
    """Download image bytes. Returns (bytes, ext) or (None, None)."""
    try:
        resp = _SESSION.get(url, timeout=timeout, allow_redirects=True)
        if resp.status_code != 200 or not resp.content:
            return None, None
        ct = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if "jpeg" in ct or "jpg" in ct:
            ext = "jpg"
        elif "png" in ct:
            ext = "png"
        elif "webp" in ct:
            ext = "webp"
        elif resp.content[:3] == b"\xff\xd8\xff":
            ext = "jpg"
        elif resp.content[:8] == b"\x89PNG\r\n\x1a\n":
            ext = "png"
        else:
            return None, None
        if len(resp.content) < 5000:  # < 5 KB = likely an error page or icon
            return None, None
        return resp.content, ext
    except Exception:
        return None, None


def _save_image(product_id, data, ext):
    d = _get_cache_dir()
    for old_ext in ("jpg", "jpeg", "png", "webp", "svg"):
        old = d / f"{product_id}.{old_ext}"
        if old.exists():
            old.unlink()
    path = d / f"{product_id}.{ext}"
    path.write_bytes(data)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# Management command
# ─────────────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Fetch real product images from DuckDuckGo image search and cache locally."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=200,
                            help="Max products to process (default 200).")
        parser.add_argument("--category", type=str, default="",
                            help="Filter by category name (optional).")
        parser.add_argument("--skip-cached", action="store_true",
                            help="Skip products that already have a cached image.")
        parser.add_argument("--delay", type=float, default=1.0,
                            help="Seconds between requests (default 1.0).")

    def handle(self, *args, **options):
        qs = Product.objects.select_related("category").order_by("id")
        if options["category"]:
            qs = qs.filter(category__name__icontains=options["category"])

        limit = options["limit"]
        delay = options["delay"]
        skip_cached = options["skip_cached"]

        ok = 0
        skipped = 0
        failed = 0
        total = 0

        self.stdout.write(
            f"Fetching images for up to {limit} products (delay={delay}s, skip_cached={skip_cached})..."
        )

        for product in qs.iterator():
            if total >= limit:
                break

            if skip_cached and _cached_path(product.pk):
                skipped += 1
                continue

            total += 1
            cat_name = product.category.name if product.category else "Others"
            query = _build_query(product.name, cat_name)
            self.stdout.write(f"[{total}/{limit}] {query[:70]}")

            url = _search_image(query, log=self.stdout.write)
            if not url:
                self.stdout.write(f"  FAIL  no results for: {query[:60]}")
                failed += 1
                time.sleep(delay)
                continue

            data, ext = _download_image(url)
            if not data:
                self.stdout.write(f"  FAIL  download: {url[:60]}")
                failed += 1
                time.sleep(delay)
                continue

            saved = _save_image(product.pk, data, ext)
            self.stdout.write(
                self.style.SUCCESS(
                    f"  OK  {ext.upper()} {len(data)//1024}KB  {saved.name}"
                )
            )
            ok += 1
            time.sleep(delay)

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone!  Downloaded: {ok}  Failed: {failed}  Skipped: {skipped}"
            )
        )
