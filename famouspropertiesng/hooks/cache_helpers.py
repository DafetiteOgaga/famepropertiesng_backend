from django.core.cache import cache

def display_all_cache_keys(type="unspecified type", key=None, id=None):
	print(f"🔍 Displaying all cache keys (during {type}):")
	print(f"key: {key}, id: {id}")

	# Use global tracker to find keys starting with this prefix
	all_cached_keys = cache.get('all_cached_keys', set())

	# Safely collect matching keys for this prefix
	if key:
		matching_keys = {
			k for k in all_cached_keys
			if str(k).startswith(f"{key}_list") or str(k).startswith(f"{key}_")
		}
		all_cached_keys.update(matching_keys)
		cache.set('all_cached_keys', all_cached_keys, None)

	if not all_cached_keys:
		print("   🚫 No cache keys found.")

	print(f"🧩 Cache keys (during {type}):")
	for k in all_cached_keys:
		print(f"   • {k}")  # Show all cached keys
	return all_cached_keys

def clear_key_and_list_in_cache(key=None, id=None):
	if not key:
		cache.clear()
		print("🗑️ Cleared all cache.")
		return

	# ✅ Show all keys before clearing
	display_all_cache_keys(type=f"before clearing {key}", key=key, id=id)

	deleted_count = 0
	all_cached_keys = cache.get('all_cached_keys', set())

	if id:
		cache_key = f'{key}_{id}'
		# ✅ Actually delete and track removal
		if cache.delete(cache_key):
			deleted_count += 1
			all_cached_keys.discard(cache_key)
			print(f"🗑️ Cleared cache for key: {cache_key}")
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
					all_cached_keys.discard(item)
					print(f"🗑️ Also cleared related cache item: {item}_list")

		print(f"✅ Cleared {deleted_count} cache items related to key: {key}")

	matching_keys = {
		k for k in all_cached_keys
		if str(k).startswith(f"{key}_list") or (id and str(k).startswith(f"{key}_{id}"))
	}

	if not matching_keys:
		print(f"🚫 No cached items found starting with '{key}_list'.")
	else:
		for item in matching_keys:
			if cache.delete(item):
				deleted_count += 1
				all_cached_keys.discard(item)
				print(f"🗑️ Cleared related cache item: {item}")

	# ✅ Update and show all after clearing
	cache.set('all_cached_keys', all_cached_keys, None)
	display_all_cache_keys(type=f"after clearing {key}", key=key, id=id)


def get_cached_response(cache_name, request, key_suffix, page_size=0, no_page_size=False):
	if no_page_size:
		pages = ""
	else:
		page = request.GET.get("page", 1)
		page_size = request.GET.get("page_size", page_size)
		pages = f"_page_{page}_size_{page_size}"
	cache_key = f"{cache_name}_{key_suffix}{pages}"

	# ✅ Display all keys before lookup
	display_all_cache_keys(type="before cache lookup for " + cache_key, key=cache_name)

	cached_data = cache.get(cache_key)
	if cached_data:
		print(f"Cache hit for: {cache_key}")
		display_all_cache_keys(type="after cache lookup (hit) " + cache_key, key=cache_name)
		return cached_data, cache_key, None

	print("Cache missing, querying database...")
	tracked_keys = cache.get(f"{cache_name}_tracked_keys", set())
	display_all_cache_keys(type="after cache lookup (miss) " + cache_key, key=cache_name)
	return None, cache_key, tracked_keys


def set_cached_response(cache_name, cache_key, tracked_keys, data, timeout=None):
	cache.set(cache_key, data, timeout=timeout)

	# ✅ Track all cache keys globally
	all_cached_keys = cache.get('all_cached_keys', set())
	all_cached_keys.add(cache_key)
	cache.set('all_cached_keys', all_cached_keys, None)

	if not timeout:
		tracked_keys.add(cache_key)
		cache.set(f"{cache_name}_tracked_keys", tracked_keys, None)

	print(f"Cached result for {cache_key}{' and not tracked.' if timeout else ''}")

	# ✅ Show keys after set
	display_all_cache_keys(type="after setting " + cache_key, key=cache_name)


def get_cache(cache_name, pk):
	cache_key = f"{cache_name}_{pk}"

	# ✅ Display keys before and after lookup
	display_all_cache_keys(type="before cache lookup for " + cache_key, key=cache_name, id=pk)

	data = cache.get(cache_key)
	if data is not None:
		print(f"Cache hit for: {cache_key}")
	else:
		print(f"Cache missing for {cache_key}")

	display_all_cache_keys(type="after cache lookup for " + cache_key, key=cache_name, id=pk)
	return data


def set_cache(cache_name, pk, data, timeout=None):
	cache_key = f"{cache_name}_{pk}"
	cache.set(cache_key, data, timeout=timeout)
	print(f"Cached data as {cache_key}{' and expires in ' + str(timeout) + ' seconds' if timeout else ''}.")

	# ✅ Add to global tracker
	all_cached_keys = cache.get('all_cached_keys', set())
	all_cached_keys.add(cache_key)
	cache.set('all_cached_keys', all_cached_keys, None)

	# ✅ Show all cache keys after set
	display_all_cache_keys(type="after setting " + cache_key, key=cache_name, id=pk)