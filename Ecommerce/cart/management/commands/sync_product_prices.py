import os

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction

from cart.models import Product, PriceHistory
from cart.pricing import (
    compute_old_price_from_history,
    compute_prices_from_row,
)


class Command(BaseCommand):
    help = (
        "Sync product prices from CSV datasets and fix old_price "
        "(no random markup)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--rebuild-history",
            action="store_true",
            help="Replace PriceHistory from CSV for matched products.",
        )

    def handle(self, *args, **options):
        base_dir = os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
        )

        lookup = self._build_csv_lookup(base_dir)
        updated = 0
        from_history = 0
        not_found = 0

        with transaction.atomic():
            for product in Product.objects.select_related("category").iterator():
                key = (product.name.strip(), product.platform)
                row = lookup.get(key)

                if row is not None:
                    current, old, history = compute_prices_from_row(row)
                    product.price = current
                    product.old_price = old
                    product.save(update_fields=["price", "old_price"])

                    if options["rebuild_history"]:
                        PriceHistory.objects.filter(product=product).delete()
                        for price in history:
                            PriceHistory.objects.create(
                                product=product,
                                price=price,
                            )
                    updated += 1
                else:
                    prices = list(
                        PriceHistory.objects.filter(product=product)
                        .order_by("date")
                        .values_list("price", flat=True)
                    )
                    if prices:
                        old = compute_old_price_from_history(
                            product.price, prices
                        )
                        if product.old_price != old:
                            product.old_price = old
                            product.save(update_fields=["old_price"])
                            from_history += 1
                    else:
                        not_found += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Updated from CSV: {updated}, "
                f"old_price fixed from DB history: {from_history}, "
                f"unchanged (no CSV/history): {not_found}"
            )
        )

    def _build_csv_lookup(self, base_dir):
        lookup = {}
        files = [
            ("Amazon", "datasets/fixed_amazon_dataset_new.csv"),
            ("Flipkart", "datasets/fixed_flipkart_dataset_new.csv"),
        ]
        for platform, rel_path in files:
            path = os.path.join(base_dir, rel_path)
            if not os.path.isfile(path):
                self.stdout.write(self.style.WARNING(f"Missing {path}"))
                continue
            df = pd.read_csv(path)
            for _, row in df.iterrows():
                name = str(row.get("product_name", "")).strip()
                if name and name != "nan":
                    lookup[(name, platform)] = row
        return lookup
