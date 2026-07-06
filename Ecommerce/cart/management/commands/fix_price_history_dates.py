"""
fix_price_history_dates  — management command
==============================================
Spreads all existing PriceHistory records for every product across the
past N days so the graph shows realistic multi-day price variation.

Each product gets its 10 records assigned to evenly-spaced dates going
back from today, with a small random time-of-day jitter so the graph
looks natural.

Usage
-----
python manage.py fix_price_history_dates           # default: 30 days
python manage.py fix_price_history_dates --days 60
"""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from cart.models import PriceHistory, Product


class Command(BaseCommand):
    help = "Spread PriceHistory dates across the past N days so the graph shows multi-day variation."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days", type=int, default=30,
            help="How many days back to spread the history (default: 30).",
        )
        parser.add_argument(
            "--batch", type=int, default=500,
            help="DB update batch size (default: 500).",
        )

    def handle(self, *args, **options):
        span_days = options["days"]
        batch_size = options["batch"]
        now = timezone.now()

        self.stdout.write(
            f"Spreading price history across {span_days} days for all products..."
        )

        product_ids = list(
            PriceHistory.objects.values_list("product_id", flat=True).distinct()
        )
        total_products = len(product_ids)
        self.stdout.write(f"Found {total_products} products with price history.")

        to_update = []
        done = 0

        for product_id in product_ids:
            records = list(
                PriceHistory.objects.filter(product_id=product_id).order_by("date")
            )
            count = len(records)
            if count == 0:
                continue

            # Spread records evenly across [now - span_days, now]
            # Each step = span_days / count days apart
            step = span_days / count

            for i, record in enumerate(records):
                # Days back from now: oldest record gets furthest back date
                days_back = span_days - (i * step)
                # Add random hour/minute jitter (±4 hours) for realism
                jitter_minutes = random.randint(-240, 240)
                new_date = now - timedelta(days=days_back, minutes=jitter_minutes)
                record.date = new_date
                to_update.append(record)

            done += 1

            # Bulk update in batches
            if len(to_update) >= batch_size:
                with transaction.atomic():
                    PriceHistory.objects.bulk_update(to_update, ["date"])
                self.stdout.write(
                    f"  Updated {done}/{total_products} products..."
                )
                to_update = []

        # Final batch
        if to_update:
            with transaction.atomic():
                PriceHistory.objects.bulk_update(to_update, ["date"])

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! Spread price history for {done} products across {span_days} days."
            )
        )
