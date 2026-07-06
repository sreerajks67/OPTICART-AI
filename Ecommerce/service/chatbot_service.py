from django.db.models import Q

from cart.models import Product
from chatbot.query_to_sql import generate_response


def _matching_products(user_query, limit=25):
    """Return products relevant to the user's query."""
    query = (user_query or '').strip()
    qs = Product.objects.select_related('category').exclude(price__isnull=True)

    if query:
        # Split into keywords for broader matching
        keywords = query.split()
        q_filter = Q()
        for kw in keywords:
            q_filter |= (
                Q(name__icontains=kw)
                | Q(description__icontains=kw)
                | Q(category__name__icontains=kw)
                | Q(platform__icontains=kw)
            )
        qs = qs.filter(q_filter)

    return qs.order_by('-rating', 'price')[:limit]


def final_result(user_query):
    """
    Main chatbot pipeline:
    1. Find matching products from the database
    2. Pass them to Gemini for a natural language recommendation
    Returns a string response (or a friendly error message).
    """
    products = _matching_products(user_query)

    if not products.exists():
        # Fallback: top-rated products
        products = Product.objects.select_related('category').order_by('-rating')[:10]

    if not products.exists():
        return "Sorry, I could not find any products to recommend right now."

    product_text = ""
    for p in products:
        ai_score = getattr(p, 'ai_score', None)
        description = (getattr(p, 'description', '') or '')[:200]
        category_name = str(p.category) if p.category else 'Unknown'

        product_text += f"""
Product Name: {p.name}
Category: {category_name}
Price: Rs.{p.price}
Rating: {p.rating}/5
Platform: {p.platform}
Description: {description}
AI Score: {ai_score}
---"""

    try:
        return generate_response(
            user_query=user_query,
            product_text=product_text,
        )
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
            return (
                "The AI assistant is temporarily unavailable due to API rate limits. "
                "Please try again in a minute. "
                "In the meantime, here are some top-rated products matching your search:\n\n"
                + "\n".join(
                    f"- {p.name} | Rs.{p.price} | Rating: {p.rating}/5"
                    for p in list(products)[:5]
                )
            )
        # Generic error — still return something useful
        return (
            f"I ran into an issue: {err[:120]}. "
            "Please try again shortly."
        )
