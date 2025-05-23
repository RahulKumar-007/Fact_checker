import hashlib
import os
import pickle
import time

class CacheManager:
    def __init__(self, cache_dir="./cache_data"): # Changed dir name slightly
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.search_cache_file = os.path.join(self.cache_dir, "search_cache.pkl")
        self.search_cache = self._load_cache(self.search_cache_file)
        
        self.verdict_cache_file = os.path.join(self.cache_dir, "verdict_cache.pkl")
        self.verdict_cache = self._load_cache(self.verdict_cache_file)
        
        self.expiration = 24 * 60 * 60  # 24 hours in seconds
    
    def _load_cache(self, cache_file):
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except (pickle.UnpicklingError, EOFError, AttributeError, ImportError, IndexError) as e:
                print(f"Warning: Could not load cache file {cache_file}. Error: {e}. Creating new cache.")
                return {}
        return {}
    
    def _save_cache(self, cache_data, cache_file):
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
        except Exception as e:
            print(f"Error saving cache to {cache_file}: {e}")

    def _get_hash(self, text):
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def get_search_result(self, query):
        query_hash = self._get_hash(query)
        if query_hash in self.search_cache:
            result, timestamp = self.search_cache[query_hash]
            if (time.time() - timestamp) < self.expiration:
                print(f"Cache hit for search query: {query[:50]}...")
                return result
            else:
                print(f"Cache expired for search query: {query[:50]}...")
                del self.search_cache[query_hash] # Remove expired entry
        return None
    
    def cache_search_result(self, query, result):
        query_hash = self._get_hash(query)
        self.search_cache[query_hash] = (result, time.time())
        self._save_cache(self.search_cache, self.search_cache_file)
        print(f"Cached search result for query: {query[:50]}...")
    
    def get_verdict(self, claim):
        claim_hash = self._get_hash(claim)
        if claim_hash in self.verdict_cache:
            result, timestamp = self.verdict_cache[claim_hash]
            if (time.time() - timestamp) < self.expiration:
                print(f"Cache hit for verdict: {claim[:50]}...")
                return result
            else:
                print(f"Cache expired for verdict: {claim[:50]}...")
                del self.verdict_cache[claim_hash] # Remove expired entry
        return None
    
    def cache_verdict(self, claim, result):
        claim_hash = self._get_hash(claim)
        self.verdict_cache[claim_hash] = (result, time.time())
        self._save_cache(self.verdict_cache, self.verdict_cache_file)
        print(f"Cached verdict for claim: {claim[:50]}...")