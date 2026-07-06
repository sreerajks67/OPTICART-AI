from django.core.management.base import BaseCommand
from django.db.models import Count

from cart.categories import (
    STANDARD_CATEGORIES,
    classify_product,
    ensure_standard_categories,
)
from cart.models import Category, Product


class Command(BaseCommand):
    help = "Reclassify all products into standard OptiCart categories."

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete-empty",
            action="store_true",
            help="Remove old category rows that have no products after reclassification.",
        )

    def handle(self, *args, **options):
        ensure_standard_categories()
        self.stdout.write("Standard categories ready.")

        updated = 0
        for product in Product.objects.select_related("category").iterator():
            raw = product.category.name if product.category else ""
            standard_name = classify_product(raw, product.name)
            category, _ = Category.objects.get_or_create(name=standard_name)
            if product.category_id != category.id:
                product.category = category
                product.save(update_fields=["category"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Updated {updated} products."))

        # Summary
        self.stdout.write("\nProduct counts by category:")
        stats = (
            Category.objects.annotate(n=Count("product"))
            .filter(n__gt=0)
            .order_by("-n")
        )
        for row in stats:
            self.stdout.write(f"  {row.name}: {row.n}")

        if options["delete_empty"]:
            deleted, _ = (
                Category.objects.annotate(n=Count("product"))
                .filter(n=0)
                .exclude(name__in=STANDARD_CATEGORIES)
                .delete()
            )
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} empty legacy categories."))
