from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from users.models import User
from store.models import Store
from hooks.cache_helpers import get_cache, set_cache
from hooks.prettyprint import pretty_print_json
from django.core.cache import cache
from django.db.models import Q
from checkouts.models import Checkout, InstallmentPayment, CheckoutProduct
from products.models import Product, Category
from store.models import Store
import re
from .serializers import SearchedUserSerializer, SearchedStoreSerializer
from .serializers import SearchedCheckoutSerializer, SeachedInstallmentPaymentSerializer
from search_app.serializers import SearchedCheckoutProductSerializer

cache_name = None
cache_key = None
cached_data = None
# paginatore_page_size = 8

def remove_duplicates_from_results(results):
    """
    Removes duplicate items from each list in a results dict.
    Prints duplicates found per item, per key, and total summary.
    
    Args:
        results (dict): A dictionary where each key maps to a list of dict-like or primitive items.
    
    Returns:
        dict: A cleaned version of `results` with duplicates removed.
    """
    total_duplicates_removed = 0  # Total across all keys

    for k, v in results.items():
        seen = set()
        unique_list = []
        duplicates_removed = 0

        print(f"\nChecking duplicates in '{k}':")

        for item in v:
            try:
                # Handle dict-like items
                if isinstance(item, dict):
                    item_tuple = tuple(sorted(item.items()))
                else:
                    item_tuple = tuple(sorted(str(item)))

                if item_tuple not in seen:
                    seen.add(item_tuple)
                    unique_list.append(item)
                else:
                    duplicates_removed += 1
                    total_duplicates_removed += 1
                    print(f"  Duplicate found in '{k}':")
                    pretty_print_json(item)
            except Exception:
                # Handle unexpected cases gracefully
                if item not in unique_list:
                    unique_list.append(item)
                else:
                    duplicates_removed += 1
                    total_duplicates_removed += 1
                    print(f"  Duplicate (fallback) found in '{k}':")
                    pretty_print_json(item)

        results[k] = unique_list
        print(f"Total duplicates removed from '{k}': {duplicates_removed}")

    print(f"\n=== Total duplicates removed across all keys: {total_duplicates_removed} ===\n")

    return results


# Create your views here.
@api_view(['GET'])
def check_email(request, email):

	cache_name = 'check_email'

	# checking for cached
	cached_data = get_cache(cache_name, pk=email)
	if cached_data:
		return Response(cached_data, status=status.HTTP_200_OK)

	print(f'Checking email: {email}')
	exist = {
		"boolValue": True,
		"color": "green",
	}
	msg = "available"
	user = User.objects.filter(email=email)
	if user:
		msg = "taken"
		exist["color"] = "#BC4B51"
	exist["message"] = f"{email} is {msg}."
	# pretty_print_json(exist)

	# set cache
	if user:
		set_cache(cache_name, email, exist)

	return Response(exist, status=status.HTTP_200_OK)

@api_view(['GET'])
def check_store_name(request, name):

	cache_name = 'check_store_name'

	# checking for cached
	cached_data = get_cache(cache_name, pk=name)
	if cached_data:
		return Response(cached_data, status=status.HTTP_200_OK)

	print(f'Checking store_name: {name}')
	exist = {
		"boolValue": True,
		"color": "green",
	}
	msg = "available"
	isStoreNameTaken = Store.objects.filter(store_name=name)
	if isStoreNameTaken:
		msg = "taken"
		exist["color"] = "#BC4B51"
	exist["message"] = f"{name} is {msg}."
	# pretty_print_json(exist)

	# set cache
	if isStoreNameTaken:
		set_cache(cache_name, name, exist)

	return Response(exist, status=status.HTTP_200_OK)

@api_view(['GET'])
def check_store_email(request, email):

	cache_name = 'check_store_email'

	# checking for cached
	cached_data = get_cache(cache_name, pk=email)
	if cached_data:
		return Response(cached_data, status=status.HTTP_200_OK)

	print(f'Checking store email: {email}')
	exist = {
		"boolValue": True,
		"color": "green",
	}
	msg = "available"
	# isStoreEmailTaken = Store.objects.filter(store_email=email)
	# switch back to Store model after testing
	isStoreEmailTaken = User.objects.filter(email=email)
	if isStoreEmailTaken:
		msg = "taken"
		exist["color"] = "#BC4B51"
	exist["message"] = f"{email} is {msg}."
	# pretty_print_json(exist)

	# set cache
	if isStoreEmailTaken:
		set_cache(cache_name, email, exist)

	return Response(exist, status=status.HTTP_200_OK)

@api_view(['GET'])
def search_data(request, pk=None, s_text=None):
	print(f"Searching for: pk={pk}, s_text={s_text}")

	# check if user exists and is active and a staff
	# --- Step 1: Verify user ---
	try:
		user = User.objects.get(pk=pk)
		print(f"Found user: {user.email}, is_active={user.is_active}, is_staff={user.is_staff}")
		if not user.is_active or not user.is_staff:
			print("User is not active or not staff")
			return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
	except User.DoesNotExist:
		print("User not found")
		return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

	# --- Step 2: Perform search ---
	search_text = (s_text or "").strip()
	if not search_text or len(search_text) == 0:
		return Response({"error": "Search text required"}, status=status.HTTP_400_BAD_REQUEST)

	string_value = search_text
	if isinstance(search_text, (int)): # , float, bool)):
		string_value = str(search_text)

	# Search by ID or name, depending on the model
	try:
		# --- 2. Initialize search containers ---
		results = {
			"checkout": [],
			"installment_payments": [],
			"products": [],
			"stores": [],
			"users": [],
		}

		# --- 3. ID / Reference / Alphanumeric search ---
		if re.fullmatch(r'[A-Za-z0-9]+', search_text):
			results["checkout"] = SearchedCheckoutSerializer(
									Checkout.objects.filter(checkoutID__icontains=search_text),
									many=True).data
			results["installment_payments"] = SeachedInstallmentPaymentSerializer(
												InstallmentPayment.objects.filter(reference__icontains=search_text),
												many=True).data

		# --- 3. ID search ---
		if re.fullmatch(r'[0-9]+', string_value):
			results["products"] = SearchedCheckoutProductSerializer(
									Product.objects.filter(id=string_value),
									many=True).data
			results["stores"] = SearchedStoreSerializer(
									Store.objects.filter(id=string_value),
									many=True).data

		# --- 4. Email search ---
		print("Performing email-based search with the search text:", search_text)
		results["users"] = SearchedUserSerializer(
							User.objects.filter(
								Q(email__icontains=search_text) |
								Q(first_name__icontains=search_text) |
								Q(id__iexact=search_text)
							).distinct(),
							many=True).data

		# --- 5. Name-based (partial) search ---
		results["products"] += SearchedCheckoutProductSerializer(
								Product.objects.filter(
									Q(name__icontains=search_text)),
								many=True).data

		results["stores"] += SearchedStoreSerializer(
								Store.objects.filter(
								Q(store_name__icontains=search_text)),
								many=True).data

		results = remove_duplicates_from_results(results)

		# --- 6. Response ---
		data = {
			"searched_for": search_text,
			"results": results
		}

		print("Search results:")
		pretty_print_json(data)

		return Response(data, status=status.HTTP_200_OK)

	except Exception as e:
		print("Search error:", str(e))
		return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


	return Response({"message": "search_data endpoint"}, status=status.HTTP_200_OK)
