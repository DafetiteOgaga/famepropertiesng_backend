from django.core.cache import cache

def clear_key_and_list_in_cache(key=None, id=None):
	if not key:
		cache.clear()
		print("🗑️ Cleared all cache.")
		return

	deleted_count = 0

	if id:
		cache_key = f'{key}_{id}'
		cache.delete(cache_key)
		deleted_count += 1
		print(f"🗑️ Cleared cache for key: {key}")
	else:
		print(f"🚫 Single item for: {key} not found.")

	tracked_keys = cache.get(f"{key}_tracked_keys", set())
	if not tracked_keys:
		print(f"🚫 No tracked cache keys found for '{key}'. Nothing to clear.")
	else:
		for item in tracked_keys:
			if str(item).startswith(f"{key}_list"):
				if cache.delete(item):
					deleted_count += 1
					print(f"🗑️ Also cleared related cache item: {item}_list")
		# cache.delete(f"{key}_tracked_keys")
		print(f"✅ Cleared {deleted_count} cache items related to key: {key}")

	# Use global tracker to find keys starting with this prefix
	all_cached_keys = cache.get('all_cached_keys', set())
	print(f"🧩 Cache keys:")
	for k in all_cached_keys:
		print(f"   • {k}")  # Show all cached keys

	matching_keys = {k for k in all_cached_keys if str(k).startswith(f"{key}_list")}

	if not matching_keys:
		print(f"🚫 No cached items found starting with '{key}_list'.")
	else:
		for item in matching_keys:
			if cache.delete(item):
				deleted_count += 1
				all_cached_keys.discard(item)
				print(f"🗑️ Cleared related cache item: {item}")
		cache.set('all_cached_keys', all_cached_keys, None)

def get_cached_response(cache_name, request, key_suffix, page_size=0, no_page_size=False):
	"""
	Check for cached data by combining cache_name and key_suffix.
	Returns (cached_data, cache_key, tracked_keys)
	"""
	if no_page_size:
		pages = ""
	else:
		page = request.GET.get("page", 1)
		page_size = request.GET.get("page_size", page_size)
		pages = f"_page_{page}_size_{page_size}"
	cache_key = f"{cache_name}_{key_suffix}{pages}"

	cached_data = cache.get(cache_key)
	if cached_data:
		print(f"Cache hit for: {cache_key}")
		return cached_data, cache_key, None

	print("Cache missing, querying database...")
	tracked_keys = cache.get(f"{cache_name}_tracked_keys", set())
	return None, cache_key, tracked_keys


def set_cached_response(cache_name, cache_key, tracked_keys, data, timeout=None):
	"""
	Set cache data and update tracked keys.
	"""
	cache.set(cache_key, data, timeout=timeout)
	# Track all cache keys globally so prefix lookups are possible
	all_cached_keys = cache.get('all_cached_keys', set())
	all_cached_keys.add(cache_key)
	cache.set('all_cached_keys', all_cached_keys, None)
	if not timeout:
		tracked_keys.add(cache_key)
		cache.set(f"{cache_name}_tracked_keys", tracked_keys, None)
	print(f"Cached result for {cache_key}{' and not tracked.' if timeout else ''}")

def get_cache(cache_name, pk):
	"""
	Retrieve data from cache by key.
	"""
	cache_key = f"{cache_name}_{pk}"
	data = cache.get(cache_key)
	if data is not None:
		print(f"Cache hit for: {cache_key}")
	else:
		print(f"Cache missing for {cache_key}")
	return data


def set_cache(cache_name, pk, data, timeout=None):
	"""
	Store data in cache under a given key.
	"""
	cache_key = f"{cache_name}_{pk}"
	cache.set(cache_key, data, timeout=timeout)
	print(f"Cached data as {cache_key}{' and expires in ' + str(timeout) + ' seconds' if timeout else ''}.")