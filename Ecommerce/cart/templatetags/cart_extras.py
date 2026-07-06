from django import template
from django.urls import reverse

from cart.image_fetch import _fix_url

register = template.Library()


@register.simple_tag
def product_image_direct(product):
    """Primary src: direct browser URL (more reliable than server-side proxy)."""
    if not product:
        return ""
    return _fix_url(getattr(product, "image_url", None)) or ""


@register.simple_tag
def product_image_proxy_url(product):
    """Fallback src: Django proxy (cache + Amazon download + category placeholder)."""
    if not product or not getattr(product, "pk", None):
        return ""
    return reverse("product_image_proxy", kwargs={"product_id": product.pk})


# Backward compatibility
@register.simple_tag
def product_image_url(product):
    return product_image_direct(product) or product_image_proxy_url(product)


@register.simple_tag(takes_context=True)
def preserve_query(context, page_number):
    """Build query string for pagination while keeping filters (category, q, sort)."""
    request = context.get("request")
    if not request:
        return f"page={page_number}"

    params = request.GET.copy()
    params["page"] = str(page_number)
    return params.urlencode()
