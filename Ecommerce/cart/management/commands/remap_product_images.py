from django.core.management.base import BaseCommand

from cart.image_mapping import image_url_for_product
from cart.models import Product


class Command(BaseCommand):
    help = "Remap product images to category-aware URLs."

    def handle(self, *args, **options):
        updated = 0
        for p in Product.objects.select_related("category").iterator():
            category_name = p.category.name if p.category else ""
            new_url = image_url_for_product(p.id, p.name, category_name)
            if p.image_url != new_url:
                p.image_url = new_url
                p.save(update_fields=["image_url"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Updated image_url for {updated} products."))

