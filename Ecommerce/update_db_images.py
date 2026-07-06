import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Ecommerce.settings")
django.setup()

from cart.models import Product
from cart.image_mapping import image_url_for_product

def update_images():
    products = Product.objects.all()
    total = products.count()
    print(f"Updating image URLs for {total} products in the database...")
    
    updated_count = 0
    for idx, product in enumerate(products):
        cat_name = product.category.name if product.category else "Others"
        new_url = image_url_for_product(product.id, product.name, cat_name)
        if product.image_url != new_url:
            product.image_url = new_url
            product.save(update_fields=['image_url'])
            updated_count += 1
        
        if (idx + 1) % 500 == 0:
            print(f"  Processed {idx + 1}/{total} products...")
            
    print(f"Successfully updated {updated_count} product image URLs in the database.")

if __name__ == "__main__":
    update_images()
