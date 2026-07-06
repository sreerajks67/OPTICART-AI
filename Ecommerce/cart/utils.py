import ast
from urllib.parse import quote

from .models import Product, AgentLog, PriceHistory

_EXTERNAL_IMAGE_HOSTS = (
    "amazon.com",
    "media-amazon.com",
    "flipkart.com",
    "flixcart.com",
)

AGENT_LOG_MAX_ROWS = 5000
AGENT_BATCH_SIZE = 100


def _proxy_external_image(url):
    """Serve third-party images via a public proxy to avoid hotlink blocks."""
    if not url or "images.weserv.nl" in url:
        return url

    lower = url.lower()
    if not any(host in lower for host in _EXTERNAL_IMAGE_HOSTS):
        return url

    return f"https://images.weserv.nl/?url={quote(url, safe='')}"


def normalize_image_url(image_url, use_proxy=False):
    """Return a single image URL from plain strings or list-like CSV values."""
    if not image_url:
        return ""

    url = str(image_url).strip()
    if url.lower() in ("nan", "none"):
        return ""

    # Strip broken third-party proxy if stored in DB from older runs
    if "images.weserv.nl" in url:
        from urllib.parse import parse_qs, urlparse
        parsed_query = parse_qs(urlparse(url).query)
        if "url" in parsed_query:
            url = parsed_query["url"][0]

    try:
        parsed = ast.literal_eval(url)
        if isinstance(parsed, list) and parsed:
            url = str(parsed[0]).strip()
        elif isinstance(parsed, str):
            url = parsed.strip()
    except (ValueError, SyntaxError):
        pass

    if not url.startswith(("http://", "https://")):
        return ""

    # Prefer HTTPS for marketplace CDNs
    if url.startswith("http://") and (
        "flixcart.com" in url.lower() or "amazon.com" in url.lower()
    ):
        url = "https://" + url[7:]

    if use_proxy:
        return _proxy_external_image(url)
    return url


def normalize_product_images(products):
    for product in products:
        product.image_url = normalize_image_url(product.image_url)
    return products


def _trim_agent_logs():
    """Keep the log table from growing without bound."""
    total = AgentLog.objects.count()
    if total <= AGENT_LOG_MAX_ROWS:
        return

    excess = total - AGENT_LOG_MAX_ROWS
    old_ids = AgentLog.objects.order_by('created_at').values_list('id', flat=True)[:excess]
    AgentLog.objects.filter(id__in=list(old_ids)).delete()


def decide_for_product(product):
    """
    Rule-based buy/wait/skip using price, discount, rating, and history.
    Returns (decision, reason).
    """
    price = float(product.price or 0)
    old_price = float(getattr(product, 'old_price', price) or price)
    rating = float(product.rating or 0)

    if price <= 0:
        return "SKIP", "Invalid or missing price"

    # Derive 'old price' from price history max (product has no old_price field)
    history = list(
        PriceHistory.objects.filter(product=product)
        .order_by('-date')
        .values_list('price', flat=True)[:10]
    )

    old_price = max(history) if history else price

    discount_pct = 0.0
    if old_price > price:
        discount_pct = ((old_price - price) / old_price) * 100

    trend_down = False
    if len(history) >= 2:
        trend_down = history[0] < history[-1]

    if discount_pct >= 15 and rating >= 4.0:
        return "BUY", f"Strong deal: {discount_pct:.0f}% off, rating {rating}"

    if discount_pct >= 8 and rating >= 3.5:
        return "BUY", f"Good price drop ({discount_pct:.0f}%)"

    if trend_down and discount_pct >= 5:
        return "WAIT", "Price trending down - wait for a better deal"

    if rating < 3.0 and discount_pct < 5:
        return "SKIP", "Low rating and weak discount"

    if discount_pct < 3:
        return "WAIT", "Small discount - monitor for price drop"

    return "BUY", f"Fair value at Rs.{price:.0f} with rating {rating}"


def run_autonomous_agent():
    """Evaluate a batch of products and write agent logs."""
    products = list(
        Product.objects.exclude(price__isnull=True).exclude(price=0).order_by('?')[:AGENT_BATCH_SIZE]
    )

    for product in products:
        decision, reason = decide_for_product(product)
        AgentLog.objects.create(
            product=product,
            decision=decision,
            reason=reason,
        )
        # Only save fields that actually exist on the Product model
        product.ai_score = 80 if decision == "BUY" else 50 if decision == "WAIT" else 25
        product.save(update_fields=['ai_score'])

    _trim_agent_logs()
    print(f"AI agent updated {len(products)} products.")
