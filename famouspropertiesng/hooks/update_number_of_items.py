from products.models import Product
import random

def update_number_of_items_available():
    """
    Loops through the products and updates the number_of_items_available field randomly
    """
    products = Product.objects.all()
    for product in products:
        product.numberOfItemsAvailable = random.randint(20, 100)
        product.save()
        print(f"Updated {product.name}: numberOfItemsAvailable = {product.numberOfItemsAvailable}")

update_number_of_items_available() # Call run to execute when the script is run directly
