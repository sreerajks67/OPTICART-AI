from django.core.management.base import BaseCommand

from cart.image_fetch import _fix_url
from cart.models import Product


class Command(BaseCommand):
    help = "Fix malformed product image URLs (HTTPS, double slashes)."

    def handle(self, *args, **options):
        updated = 0
        for product in Product.objects.exclude(image_url="").iterator():
            fixed = _fix_url(product.image_url)
            if fixed and fixed != product.image_url:
                product.image_url = fixed
                product.save(update_fields=["image_url"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Fixed {updated} image URLs."))
