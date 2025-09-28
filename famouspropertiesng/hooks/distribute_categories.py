from products.models import Product, Category
import random


def distribute_categories():
    products = Product.objects.all()
    print("fetched all products")

    for product in products:
        print(f"Clearing categories for product: {product.name}")
        product.category.clear()  # clear existing categories
        print(f"Processing product: {product.name}")
        chosen = random.sample(dictofcat, 10)  # pick 5 unique categories
        print(f"Chosen categories for '{product.name}': {chosen}")
        categories = Category.objects.filter(name__in=chosen)  # fetch them at once
        # print(f"Fetched categories from DB: {[cat.name for cat in categories]}")
        product.category.add(*categories)  # add all 3 in one go
        print(f"Assigned categories to '{product.name}': {[cat.name for cat in categories]}")

dictofcat = [
	'android phones',
	'iphones', 'feature phones',
	'windows laptops', 'macbooks', 'desktops',
	'audio & headphones', 'cameras', 'wearables',
	"men's clothing", "women's clothing", 'shoes',
	'watches & jewelry', 'bags & accessories', 'furniture',
	'home appliances', 'cookware & dining', 'bedding',
	'decor', 'skincare', 'makeup', 'fragrances', 'hair care',
	'grooming tools', 'fitness equipment', 'outdoor gear',
	'sportswear', 'cycling', 'camping & hiking', 'board games',
	'puzzles', 'educational toys', 'dolls & action figures',
	'video games', 'fiction', 'non-fiction', "children's books",
	'comics & manga', 'academic', 'car accessories',
	'motorbike accessories', 'spare parts', 'car electronics',
	'tires & wheels', 'food staples', 'snacks & beverages',
	'household supplies', 'baby products', 'pet supplies',
	'medical supplies', 'vitamins & supplements', 'wellness',
	'personal safety', 'fitness nutrition'
]

distribute_categories()
