from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from cart.models import Product, Review
import random


class Command(BaseCommand):
    help = "Generate fake reviews"

    def handle(self, *args, **kwargs):

        user = User.objects.first()

        if not user:
            self.stdout.write(
                self.style.ERROR(
                    "No users found. Create a user first."
                )
            )
            return

        reviews_by_category = {

            "Electronics": [
                "Battery life is impressive.",
                "Display quality is excellent.",
                "Amazing performance.",
                "Fast and responsive.",
                "Good value for money.",
                "Build quality feels premium.",
                "Excellent product for daily use."
            ],

            "Fashion": [
                "Fabric quality is excellent.",
                "Fits perfectly.",
                "Very comfortable to wear.",
                "Looks stylish and premium.",
                "Color is exactly as shown.",
                "Worth the price.",
                "Good stitching quality."
            ],

            "Beauty & Personal Care": [
                "Works exactly as expected.",
                "Very gentle on skin.",
                "Pleasant fragrance.",
                "Packaging was excellent.",
                "Good quality product.",
                "Would buy again."
            ],

            "Books & Media": [
                "Very informative and engaging.",
                "Excellent read.",
                "Well written content.",
                "Highly recommended.",
                "Worth every penny.",
                "Interesting from start to finish."
            ],

            "Home & Furniture": [
                "Easy to assemble.",
                "Looks great at home.",
                "Very sturdy product.",
                "Good build quality.",
                "Value for money.",
                "Perfect for my room."
            ],

            "Sports & Fitness": [
                "Comfortable during workouts.",
                "Good durability.",
                "Lightweight and practical.",
                "Improved my training experience.",
                "Excellent quality.",
                "Highly recommended."
            ],

            "Automotive": [
                "Fits perfectly.",
                "Easy to install.",
                "Good build quality.",
                "Works as described.",
                "Improved vehicle performance.",
                "Worth buying."
            ],

            "Grocery & Food": [
                "Fresh and good quality.",
                "Taste is excellent.",
                "Packaging was secure.",
                "Would order again.",
                "Value for money.",
                "Very satisfied."
            ],

            "Toys & Kids": [
                "Kids loved it.",
                "Fun and engaging.",
                "Safe for children.",
                "Excellent gift option.",
                "Good quality materials.",
                "Worth buying."
            ],

            "Others": [
                "Excellent product, highly recommended.",
                "Worth the price.",
                "Very good build quality.",
                "Good value for money.",
                "Satisfied with the purchase.",
                "Would buy again."
            ]
        }

        # Optional: remove old reviews
        Review.objects.all().delete()

        products = Product.objects.all()

        count = 0

        for product in products:

            category_name = "Others"

            if product.category:
                category_name = product.category.name

            comments = reviews_by_category.get(
                category_name,
                reviews_by_category["Others"]
            )

            for platform in ["Amazon", "Flipkart"]:

                # Create 3 reviews per platform
                for _ in range(3):

                    Review.objects.create(
                        user=user,
                        product=product,
                        platform=platform,
                        rating=random.randint(3, 5),
                        comment=random.choice(comments)
                    )

                    count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{count} reviews created successfully."
            )
        )