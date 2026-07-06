from django.core.management.base import BaseCommand

from cart.image_fetch import fetch_product_image_bytes, get_cached_image, save_to_cache
from cart.models import Product


class Command(BaseCommand):
    help = "Download product images to media/product_images/ (Amazon usually works)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=500)
        parser.add_argument("--platform", type=str, default="")

    def handle(self, *args, **options):
        qs = Product.objects.exclude(image_url="").order_by("id")
        if options["platform"]:
            qs = qs.filter(platform__iexact=options["platform"])

        cached = 0
        failed = 0
        limit = options["limit"]

        for product in qs[:limit]:
            if get_cached_image(product.pk)[0]:
                cached += 1
                continue

            content, ctype = fetch_product_image_bytes(product.image_url)
            if content and ctype:
                save_to_cache(product.pk, content, ctype)
                cached += 1
                self.stdout.write(f"OK {product.id} {product.name[:40]}")
            else:
                failed += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Cached/downloaded: {cached}, failed (use proxy fallback): {failed}"
            )
        )
