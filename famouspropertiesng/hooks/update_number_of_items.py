from products.models import Product
import random

def update_number_of_items():
    """
    Loops through the products and updates the number_of_items field randomly
    """
    products = Product.objects.all()
    for product in products:
        product.numberOfItems = random.randint(20, 100)
        product.save()
        print(f"Updated {product.name}: numberOfItems = {product.numberOfItems}")

update_number_of_items() # Call run to execute when the script is run directly
