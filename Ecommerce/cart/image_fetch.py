"""Serve product images — generates beautiful branded SVG cards for synthetic products."""

import re
import textwrap
from pathlib import Path

import requests
from django.conf import settings

from cart.utils import normalize_image_url

_SESSION = requests.Session()

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

_CACHE_DIR_NAME = "product_images"


def _fix_url(url):
    """HTTPS + fix double slashes after hostname."""
    if not url:
        return ""
    url = normalize_image_url(url, use_proxy=False)
    if not url:
        return ""
    if url.startswith("http://"):
        url = "https://" + url[7:]
    if "://" in url:
        scheme, rest = url.split("://", 1)
        slash_idx = rest.find("/")
        if slash_idx >= 0:
            host = rest[:slash_idx]
            path = rest[slash_idx:]
            while "//" in path:
                path = path.replace("//", "/")
            url = f"{scheme}://{host}{path}"
    return url


def _headers_for_url(url):
    lower = url.lower()
    headers = {
        "User-Agent": _USER_AGENT,
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
    }
    if "amazon.com" in lower or "media-amazon" in lower:
        headers["Referer"] = "https://www.amazon.in/"
    elif "flipkart.com" in lower or "flixcart.com" in lower:
        headers["Referer"] = "https://www.flipkart.com/"
        headers["Origin"] = "https://www.flipkart.com"
    return headers


def _cache_dir():
    path = Path(settings.MEDIA_ROOT) / _CACHE_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cache_path(product_id, ext="svg"):
    return _cache_dir() / f"{product_id}.{ext}"


def get_cached_image(product_id):
    """Return (bytes, content_type) from local cache if present."""
    for ext, ctype in (
        ("svg", "image/svg+xml"),
        ("jpg", "image/jpeg"),
        ("jpeg", "image/jpeg"),
        ("png", "image/png"),
        ("webp", "image/webp"),
    ):
        path = _cache_path(product_id, ext)
        if path.is_file() and path.stat().st_size > 0:
            return path.read_bytes(), ctype
    return None, None


def save_to_cache(product_id, content, content_type):
    ext = "svg"
    if "jpeg" in content_type or "jpg" in content_type:
        ext = "jpg"
    elif "png" in content_type:
        ext = "png"
    elif "webp" in content_type:
        ext = "webp"
    _cache_path(product_id, ext).write_bytes(content)


def fetch_product_image_bytes(image_url):
    """Download image bytes from a real URL. Returns (content, content_type) or (None, None)."""
    url = _fix_url(image_url)
    if not url:
        return None, None
    # Skip loremflickr, placeholder, and other synthetic URLs — they return random/wrong images
    skip_hosts = ("loremflickr.com", "placeholder.com", "placehold.co", "picsum.photos",
                  "via.placeholder", "dummyimage.com")
    if any(h in url for h in skip_hosts):
        return None, None

    try:
        response = _SESSION.get(
            url,
            headers=_headers_for_url(url),
            timeout=10,
            allow_redirects=True,
        )
    except requests.RequestException:
        return None, None

    if response.status_code != 200 or not response.content:
        return None, None

    content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
    if not content_type.startswith("image/"):
        if response.content[:3] == b"\xff\xd8\xff":
            content_type = "image/jpeg"
        elif response.content[:8] == b"\x89PNG\r\n\x1a\n":
            content_type = "image/png"
        else:
            return None, None

    return response.content, content_type


# ─────────────────────────────────────────────────────────────────────────────
#  CATEGORY CONFIG  (colour palette + emoji icon)
# ─────────────────────────────────────────────────────────────────────────────
_CAT_CONFIG = {
    "Electronics": {
        "bg": "#0f3460", "accent": "#e94560", "light": "#16213e",
        "icon": "💻", "icon_y": 170,
    },
    "Fashion": {
        "bg": "#1a1a2e", "accent": "#e91e8c", "light": "#16213e",
        "icon": "👗", "icon_y": 170,
    },
    "Home & Furniture": {
        "bg": "#1b4332", "accent": "#52b788", "light": "#081c15",
        "icon": "🛋️", "icon_y": 170,
    },
    "Beauty & Personal Care": {
        "bg": "#4a0e5e", "accent": "#ff6eb4", "light": "#2d0036",
        "icon": "💄", "icon_y": 170,
    },
    "Sports & Fitness": {
        "bg": "#003049", "accent": "#fcbf49", "light": "#001a2c",
        "icon": "🏋️", "icon_y": 170,
    },
    "Books & Media": {
        "bg": "#3d0c02", "accent": "#e07a5f", "light": "#220700",
        "icon": "📚", "icon_y": 170,
    },
    "Toys & Kids": {
        "bg": "#7b2d00", "accent": "#ffd166", "light": "#4a1a00",
        "icon": "🧸", "icon_y": 170,
    },
    "Grocery & Food": {
        "bg": "#1b4020", "accent": "#95d5b2", "light": "#0d2010",
        "icon": "🛒", "icon_y": 170,
    },
    "Automotive": {
        "bg": "#1c1c1c", "accent": "#e63946", "light": "#111111",
        "icon": "🚗", "icon_y": 170,
    },
    "Others": {
        "bg": "#2d3561", "accent": "#a8dadc", "light": "#1a2040",
        "icon": "📦", "icon_y": 170,
    },
}

_DEFAULT_CFG = {
    "bg": "#1c1c2e", "accent": "#7c83fd", "light": "#0d0d1a",
    "icon": "🏷️", "icon_y": 170,
}

# Per-product-type overrides based on name keywords
_NAME_ICONS = [
    (["iphone", "galaxy", "redmi", "oneplus", "realme", "vivo", "oppo", "motorola", "android", "smartphone"], "📱"),
    (["macbook", "laptop", "notebook", "thinkpad", "inspiron", "pavilion", "vivobook", "aspire"], "💻"),
    (["headphone", "earphone", "airpod", "earbud", "headset"], "🎧"),
    (["speaker", "soundbar", "bluetooth speaker"], "🔊"),
    (["smartwatch", "watch"], "⌚"),
    (["tv", "television", "smart tv", "oled", "qled"], "📺"),
    (["monitor", "display", "screen"], "🖥️"),
    (["tablet", "ipad"], "📱"),
    (["camera", "dslr", "mirrorless"], "📷"),
    (["refrigerator", "fridge"], "🧊"),
    (["washing machine", "washer"], "🫧"),
    (["microwave", "oven"], "📡"),
    (["air conditioner", "ac ", " ac ", "cooler"], "❄️"),
    (["sofa", "couch", "settee"], "🛋️"),
    (["chair", "seat", "stool"], "🪑"),
    (["bed", "mattress"], "🛏️"),
    (["wardrobe", "cabinet", "shelf", "cupboard"], "🗄️"),
    (["table", "desk"], "🪑"),
    (["shoe", "sneaker", "sandal", "boot", "footwear"], "👟"),
    (["jeans", "denim"], "👖"),
    (["jacket", "coat", "hoodie"], "🧥"),
    (["shirt", "tshirt", "t-shirt", "kurta", "dress", "saree"], "👕"),
    (["bag", "backpack", "handbag", "purse", "wallet"], "👜"),
    (["lipstick", "lip gloss"], "💄"),
    (["moisturizer", "cream", "lotion"], "🧴"),
    (["shampoo", "conditioner", "hair"], "🧴"),
    (["face wash", "facewash", "cleanser"], "🧼"),
    (["sunscreen", "sunblock", "spf"], "🌞"),
    (["perfume", "deodorant", "cologne"], "🧴"),
    (["controller", "gamepad", "joystick"], "🎮"),
    (["gaming console", "playstation", "xbox", "nintendo"], "🎮"),
    (["keyboard"], "⌨️"),
    (["mouse"], "🖱️"),
    (["book", "novel", "guide", "manual"], "📖"),
    (["atta", "flour"], "🌾"),
    (["rice"], "🍚"),
    (["tea"], "🍵"),
    (["coffee"], "☕"),
    (["oil", "ghee", "butter"], "🫙"),
    (["biscuit", "cookie", "snack"], "🍪"),
    (["bicycle", "cycle", "bike"], "🚲"),
    (["helmet"], "⛑️"),
    (["car", "tire", "tyre"], "🚗"),
    (["water purifier", "purifier"], "💧"),
    (["toner", "cartridge", "printer", "ink"], "🖨️"),
]


def _get_icon(name_lower, category_name):
    """Return the best emoji icon for this product."""
    for keywords, icon in _NAME_ICONS:
        if any(kw in name_lower for kw in keywords):
            return icon
    cfg = _CAT_CONFIG.get(category_name, _DEFAULT_CFG)
    return cfg["icon"]


def _clean_display_name(product_name):
    """Strip OPT IDs and long specs from display name."""
    n = product_name or "Product"
    # Remove (OPT000001) style suffixes
    n = re.sub(r'\s*\(OPT\d+\)\s*', '', n, flags=re.IGNORECASE)
    # Remove long RAM/storage specs
    n = re.sub(r'\b\d+GB/\d+GB\b', '', n, flags=re.IGNORECASE)
    n = re.sub(r'\b\d+GB\b', '', n, flags=re.IGNORECASE)
    n = re.sub(r'\b\d+TB\b', '', n, flags=re.IGNORECASE)
    return n.strip()


def _wrap_text(text, max_chars=22):
    """Wrap product name into up to 3 lines."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current = (current + " " + word).strip()
        else:
            if current:
                lines.append(current)
            current = word
        if len(lines) == 3:
            break
    if current and len(lines) < 3:
        lines.append(current)
    return lines[:3]


def generate_product_svg(product_name, category_name, platform=""):
    """
    Generate a beautiful, product-specific SVG card.
    Always shows the correct product name, category icon, and brand colours.
    """
    cfg = _CAT_CONFIG.get(category_name, _DEFAULT_CFG)
    bg = cfg["bg"]
    accent = cfg["accent"]
    light = cfg["light"]

    name_lower = (product_name or "").lower()
    icon = _get_icon(name_lower, category_name)
    display_name = _clean_display_name(product_name or "Product")
    cat_label = (category_name or "Product")[:28]
    platform_label = (platform or "").upper()

    # Wrap name into lines
    lines = _wrap_text(display_name, max_chars=20)
    name_svg = ""
    start_y = 310
    for i, line in enumerate(lines):
        name_svg += (
            f'<text x="300" y="{start_y + i * 32}" text-anchor="middle" '
            f'fill="#ffffff" font-family="Arial,Helvetica,sans-serif" '
            f'font-size="22" font-weight="700">{line}</text>\n'
        )

    # Platform badge
    platform_svg = ""
    if platform_label in ("AMAZON", "FLIPKART"):
        plat_color = "#ff9900" if platform_label == "AMAZON" else "#2874f0"
        platform_svg = (
            f'<rect x="220" y="20" width="120" height="32" rx="16" fill="{plat_color}" opacity="0.9"/>'
            f'<text x="280" y="41" text-anchor="middle" fill="#ffffff" '
            f'font-family="Arial,sans-serif" font-size="14" font-weight="bold">{platform_label}</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 600 600">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{bg};stop-opacity:1"/>
      <stop offset="100%" style="stop-color:{light};stop-opacity:1"/>
    </linearGradient>
    <linearGradient id="card" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:{accent};stop-opacity:0.15"/>
      <stop offset="100%" style="stop-color:{accent};stop-opacity:0.05"/>
    </linearGradient>
    <filter id="shadow">
      <feDropShadow dx="0" dy="4" stdDeviation="12" flood-color="{accent}" flood-opacity="0.3"/>
    </filter>
  </defs>

  <!-- Background -->
  <rect width="600" height="600" fill="url(#bg)"/>

  <!-- Decorative circles -->
  <circle cx="520" cy="80" r="120" fill="{accent}" opacity="0.07"/>
  <circle cx="80" cy="520" r="150" fill="{accent}" opacity="0.06"/>
  <circle cx="300" cy="300" r="200" fill="{accent}" opacity="0.03"/>

  <!-- Card -->
  <rect x="60" y="60" width="480" height="480" rx="32" fill="url(#card)"
        stroke="{accent}" stroke-width="1.5" stroke-opacity="0.3" filter="url(#shadow)"/>

  <!-- Icon circle -->
  <circle cx="300" cy="200" r="90" fill="{accent}" opacity="0.15"/>
  <circle cx="300" cy="200" r="72" fill="{accent}" opacity="0.1"/>
  <text x="300" y="230" text-anchor="middle" font-size="80">{icon}</text>

  <!-- Category label -->
  <text x="300" y="285" text-anchor="middle" fill="{accent}"
        font-family="Arial,Helvetica,sans-serif" font-size="16" font-weight="600"
        opacity="0.9">{cat_label}</text>

  <!-- Divider -->
  <line x1="120" y1="300" x2="480" y2="300" stroke="{accent}" stroke-width="1" opacity="0.25"/>

  <!-- Product name lines -->
  {name_svg}

  <!-- OptiCart brand -->
  <text x="300" y="520" text-anchor="middle" fill="{accent}"
        font-family="Arial,Helvetica,sans-serif" font-size="13" opacity="0.6">OptiCart</text>

  <!-- Platform badge -->
  {platform_svg}
</svg>"""

    return svg.encode("utf-8")


def serve_product_image(product):
    """
    Full pipeline: check cache → try real URL → generate beautiful SVG card.
    Returns (HttpResponse-ready bytes, content_type).
    """
    # 1. Check local cache
    cached, ctype = get_cached_image(product.pk)
    if cached:
        return cached, ctype

    # 2. Try downloading a real image (only for real CDN URLs, not placeholder services)
    content, ctype = fetch_product_image_bytes(product.image_url)
    if content and ctype:
        save_to_cache(product.pk, content, ctype)
        return content, ctype

    # 3. Generate a beautiful, accurate branded SVG card
    cat_name = product.category.name if product.category else "Others"
    platform = getattr(product, "platform", "")
    svg_bytes = generate_product_svg(product.name, cat_name, platform)
    save_to_cache(product.pk, svg_bytes, "image/svg+xml")
    return svg_bytes, "image/svg+xml"
