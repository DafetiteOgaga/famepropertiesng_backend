from django.shortcuts import render
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import FeatureAdvert
from hooks.deleteImage import delete_image

# default_icon_dict = {
#     'quality product': 'fa fa-check',
#     'free shipping': 'fa fa-shipping-fast',
#     '7-days return': 'fas fa-exchange-alt',
#     '24/7 support': 'fa fa-phone-volume',
#     'friendly support': 'fa fa-user-friends',
#     'customer assistance': 'fa fa-headset',
#     'live chat': 'fa fa-comment-dots',
#     'fast delivery': 'fa fa-truck-loading',
#     'track your order': 'fa fa-map-marker-alt',
#     'best prices': 'fa fa-tag',
#     'special offers': 'fa fa-gift',
#     'discounts': 'fa fa-percentage',
#     'top rated products': 'fa fa-star',
#     'certified quality': 'fa fa-award',
#     'trusted by customers': 'fa fa-thumbs-up',
#     'secure payment': 'fa fa-lock',
#     'easy checkout': 'fa fa-shopping-cart',
#     'satisfaction guarantee': 'fa fa-smile',
#     'eco-friendly products': 'fa fa-leaf',
#     'locally sourced': 'fa fa-map-marked-alt',
#     'community support': 'fa fa-hands-helping',
#     'customizable options': 'fa fa-cogs',
#     'premium quality': 'fa fa-certificate',
#     'exclusive deals': 'fa fa-star-half-alt',
#     'limited time offers': 'fa fa-hourglass-half',
#     'new arrivals': 'fa fa-plus-circle',
#     'best sellers': 'fa fa-fire',
#     'customer reviews': 'fa fa-comments',
#     'user-friendly interface': 'fa fa-desktop',
#     'mobile-friendly': 'fa fa-mobile-alt',
#     'easy navigation': 'fa fa-compass',
#     'wide selection': 'fa fa-th-large',
#     'global shipping': 'fa fa-plane',
#     'hassle-free returns': 'fa fa-undo',
#     'no hidden fees': 'fa fa-info-circle',
#     'transparent pricing': 'fa fa-dollar-sign',
#     'loyalty rewards': 'fa fa-heart',
#     'refer a friend': 'fa fa-users',
#     'social media presence': 'fa fa-share-alt',
#     'blog and resources': 'fa fa-newspaper',
#     'newsletter subscription': 'fa fa-envelope',
#     'customer testimonials': 'fa fa-quote-left',
#     'expert advice': 'fa fa-lightbulb',
#     'industry expertise': 'fa fa-briefcase',
#     'sustainable practices': 'fa fa-recycle',
#     'charity contributions': 'fa fa-hand-holding-heart',
#     'local partnerships': 'fa fa-handshake',
# }
icon_dict = {
    'quality product': 'fa fa-check',
    'free shipping': 'fa fa-shipping-fast',
    '7-days return': 'fas fa-exchange-alt',
    '24/7 support': 'fa fa-phone-volume',
    'live chat': 'fa fa-comment-dots',
    'fast delivery': 'fa fa-truck-loading',
    'track your order': 'fa fa-map-marker-alt',
    'best prices': 'fa fa-tag',
    'special offers': 'fa fa-gift',
    'discounts': 'fa fa-percentage',
    'top rated products': 'fa fa-star',
    'secure payment': 'fa fa-lock',
    'easy checkout': 'fa fa-shopping-cart',
    'satisfaction guarantee': 'fa fa-smile',
    'locally sourced': 'fa fa-map-marked-alt',
    'premium quality': 'fa fa-certificate',
    'exclusive deals': 'fa fa-star-half-alt',
    'limited time offers': 'fa fa-hourglass-half',
    'new arrivals': 'fa fa-plus-circle',
    'best sellers': 'fa fa-fire',
    'customer reviews': 'fa fa-comments',
    'global shipping': 'fa fa-plane',
    'hassle-free returns': 'fa fa-undo',
    'no hidden fees': 'fa fa-info-circle',
    'transparent pricing': 'fa fa-dollar-sign',
    'loyalty rewards': 'fa fa-heart',
    'refer a friend': 'fa fa-users',
    'new product alert': 'fa fa-envelope',
    'local partnerships': 'fa fa-handshake',
}

# Create your views here..
@api_view(['POST', 'GET'])
@csrf_exempt
def featuresAdvert(request):
    if request.method == "POST":
        data = json.loads(request.body)
        print(f"Received featuresAdvert data: {data}")

        # data contains info from React, including the uploaded image URL
        featureAdvert = FeatureAdvert.objects.create(
            anchor=data.get("anchor"),
            paragraph=data.get("paragraph"),
            heading=data.get("heading"),
            # image_url=data.get("image_url")  # <--- this comes from ImageKit
        )

        return JsonResponse({
            "id": featureAdvert.id,
            "anchor": featureAdvert.anchor,
            "paragraph": featureAdvert.paragraph,
            "heading": featureAdvert.heading,  # Convert Decimal to string for JSON serialization
            # "image_url": featureAdvert.image_url,
        }, status=201)
    elif request.method == "GET":
        featuresAdvert = FeatureAdvert.objects.all()
        print(f"Fetched {featuresAdvert.count()} featureAdvert")
        featureAdvert_list = [{
            "id": featureAdvert.id,
            "anchor": featureAdvert.anchor,
            "paragraph": featureAdvert.paragraph,
            "heading": featureAdvert.heading,  # Convert Decimal to string for JSON serialization
            # "image_url": featureAdvert.image_url,
        } for featureAdvert in featuresAdvert]

        return JsonResponse(featureAdvert_list, safe=False, status=200)

@csrf_exempt
def deleteFeaturesAdverts(request):
    return delete_image(request, FeatureAdvert)
    # return JsonResponse({"message": "Feature Advert deleted successfully"}, status=200)