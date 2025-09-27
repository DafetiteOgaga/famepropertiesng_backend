from products.models import Category

def create_or_update_categories(data, parent=None):
    """
    Recursively create or update categories and subcategories.
    Works for unlimited levels of nesting.
    """
    # print(f"Processing categories under parent: {parent.name if parent else 'None'}")
    for name, children in data.items():
        # If children is a list, convert it to dict form
        if isinstance(children, list):
            children = {child: {} for child in children}

        # Get or create the category
        category, created = Category.objects.get_or_create(
            name=name,
            defaults={
                "description": f"{name} category",
                "parent": parent
            }
        )

        # 🔑 If it already exists, update parent/description if changed
        updated = False
        if category.parent != parent:
            category.parent = parent
            updated = True
        if category.description != f"{name} category":
            category.description = f"{name} category"
            updated = True
        if updated:
            category.save()
            print(f"♻️ Updated: {category.name} (Parent: {parent.name if parent else 'None'})")
        elif created:
            print(f"✅ Created: {category.name} (Parent: {parent.name if parent else 'None'})")
        else:
            print(f"✔️ Exists: {category.name} (Parent: {parent.name if parent else 'None'})")

        # Recurse for subcategories
        create_or_update_categories(children, parent=category)


def run():
    """Entry point when running with exec() in Django shell."""
    print("Starting category creation/update...")
    create_or_update_categories(categories)


# Categories dictionary (nested, unlimited levels)
categories = {
    "Electronics": {
        "Phones & Accessories": {
            "Smartphones": ["Android Phones", "iPhones"],
            "Feature Phones": []
        },
        "Laptops & Computers": {
            "Windows Laptops": [],
            "MacBooks": [],
            "Desktops": []
        },
        "Audio & Headphones": [],
        "Cameras": [],
        "Wearables": [],
    },
    "Fashion": {
        "Men's Clothing": [],
        "Women's Clothing": [],
        "Shoes": [],
        "Watches & Jewelry": [],
        "Bags & Accessories": [],
    },
    "Home & Kitchen": {
        "Furniture": [],
        "Home Appliances": [],
        "Cookware & Dining": [],
        "Bedding": [],
        "Decor": [],
    },
    "Beauty & Personal Care": {
        "Skincare": [],
        "Makeup": [],
        "Fragrances": [],
        "Hair Care": [],
        "Grooming Tools": [],
    },
    "Sports & Outdoors": {
        "Fitness Equipment": [],
        "Outdoor Gear": [],
        "Sportswear": [],
        "Cycling": [],
        "Camping & Hiking": [],
    },
    "Toys & Games": {
        "Board Games": [],
        "Puzzles": [],
        "Educational Toys": [],
        "Dolls & Action Figures": [],
        "Video Games": [],
    },
    "Books": {
        "Fiction": [],
        "Non-Fiction": [],
        "Children's Books": [],
        "Comics & Manga": [],
        "Academic": [],
    },
    "Automotive": {
        "Car Accessories": [],
        "Motorbike Accessories": [],
        "Spare Parts": [],
        "Car Electronics": [],
        "Tires & Wheels": [],
    },
    "Groceries": {
        "Food Staples": [],
        "Snacks & Beverages": [],
        "Household Supplies": [],
        "Baby Products": [],
        "Pet Supplies": [],
    },
    "Health": {
        "Medical Supplies": [],
        "Vitamins & Supplements": [],
        "Wellness": [],
        "Personal Safety": [],
        "Fitness Nutrition": [],
    },
}

run() # Call run to execute when the script is run directly
