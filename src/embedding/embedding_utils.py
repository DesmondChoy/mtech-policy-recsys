import json
import os
import pickle
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from difflib import get_close_matches


class EmbeddingMatcher:
    def __init__(self, json_path=None, model_name='all-MiniLM-L6-v2', use_cache=True):
        """
        Initialize the EmbeddingMatcher with a JSON file containing ground truth data and a sentence embedding model.

        Args:
            json_path (str, optional): Path to the JSON file containing the ground truth data. 
                                     If None, uses default path in data/ground_truth/ground_truth.json
            model_name (str, optional): Name of the sentence transformer model to use. Defaults to 'all-MiniLM-L6-v2'.
            use_cache (bool, optional): Whether to cache embeddings to a file. Defaults to True.
        """
        if json_path is None:
            # Get the project root directory (2 levels up from this file)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            json_path = os.path.join(project_root, 'data', 'ground_truth', 'ground_truth.json')
        
        self.json_path = json_path
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.use_cache = use_cache
        self.ground_truth = self._load_json()
        self.keys = list(self.ground_truth.keys())
        
        # Cache file path
        self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_file = os.path.join(self.cache_dir, f"embeddings_{os.path.basename(json_path)}_{model_name.replace('/', '_')}.pkl")
        
        self.key_embeddings = self._generate_key_embeddings()

    def _load_json(self):
        """Load the JSON file containing the ground truth data."""
        with open(self.json_path, 'r') as f:
            return json.load(f)

    def _generate_key_embeddings(self):
        """Generate embeddings for each key in the ground truth data. Uses cache if available."""
        if self.use_cache and os.path.exists(self.cache_file):
            print(f"Loading embeddings from cache: {self.cache_file}")
            with open(self.cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                # Verify that the cache is valid for the current keys
                if cached_data.get('keys') == self.keys:
                    return cached_data.get('embeddings')
                else:
                    print("Cache invalid: keys have changed. Regenerating embeddings.")
        
        print("Generating embeddings for keys...")
        embeddings = self.model.encode(self.keys)
        
        if self.use_cache:
            with open(self.cache_file, 'wb') as f:
                pickle.dump({'keys': self.keys, 'embeddings': embeddings}, f)
            print(f"Embeddings cached to: {self.cache_file}")
        
        return embeddings

    @lru_cache(maxsize=128)
    def _encode_query(self, query_key):
        """Encode a query string into an embedding vector. This method is cached for performance."""
        return self.model.encode([query_key])[0]

    def find_best_match(self, query_key, threshold=0.7, use_fuzzy=False):
        """
        Find the best matching key for a given query key using cosine similarity.

        Args:
            query_key (str): The query key to find a match for.
            threshold (float, optional): The minimum similarity score to consider a match. Defaults to 0.7.
            use_fuzzy (bool, optional): Whether to use fuzzy string matching as a fallback. Defaults to False.

        Returns:
            tuple: A tuple containing the best matching key and the similarity score. If no match is found, returns (None, 0.0).
        """
        # First try with embeddings (semantic matching)
        query_embedding = self._encode_query(query_key)
        similarities = cosine_similarity([query_embedding], self.key_embeddings)[0]
        best_match_idx = np.argmax(similarities)
        best_match_score = similarities[best_match_idx]

        if best_match_score >= threshold:
            return self.keys[best_match_idx], best_match_score
        elif use_fuzzy:
            # Fallback to fuzzy string matching
            fuzzy_matches = get_close_matches(query_key, self.keys, n=1, cutoff=0.6)
            if fuzzy_matches:
                fuzzy_match = fuzzy_matches[0]
                # Calculate a normalized score (convert Levenshtein distance to a similarity score)
                fuzzy_score = max(0.6, 1.0 - (1.0 - 0.6) * 
                              (len(query_key) - len(fuzzy_match)) / max(len(query_key), len(fuzzy_match)))
                return fuzzy_match, fuzzy_score
        
        return None, 0.0

    def get_value(self, query_key, threshold=0.7, use_fuzzy=False):
        """
        Get the value (list of policy files) for a given query key.

        Args:
            query_key (str): The query key to find a match for.
            threshold (float, optional): The minimum similarity score to consider a match. Defaults to 0.7.
            use_fuzzy (bool, optional): Whether to use fuzzy string matching as a fallback. Defaults to False.

        Returns:
            tuple: A tuple containing the list of policy files and the match information (key, score).
                  If no match is found, returns ([], (None, 0.0)).
        """
        best_match, score = self.find_best_match(query_key, threshold, use_fuzzy)
        if best_match:
            return self.ground_truth[best_match], (best_match, score)
        else:
            return [], (None, 0.0)


# Example usage
if __name__ == "__main__":
    matcher = EmbeddingMatcher(use_cache=True)  # Uses default path with caching
    
    print("\n=== Testing with Semantic Matching ===")
    # Try a few different queries
    test_queries = [
        "Loss of baggage",
        "Medical expenses overseas",
        "Trip cancellation",
        "Baggage delay"
    ]
    
    for query in test_queries:
        value, (best_match, score) = matcher.get_value(query)
        print(f"\nQuery: {query}")
        print(f"Best Match: {best_match}")
        print(f"Similarity Score: {score:.4f}")
        if best_match:
            # Print first few items
            print(f"Value (first 3): {value[:3]}...")
        print("-" * 50)
    
    print("\n=== Testing with Fuzzy Matching ===")
    # Try a few queries with typos or variations
    fuzzy_queries = [
        "Bagage delayz",
        "Medical expnses overseas",
        "Trip cancelltion",
        "Lost of passport",
        "Emergency meical evacation"
    ]
    
    for query in fuzzy_queries:
        value, (best_match, score) = matcher.get_value(query, use_fuzzy=True)
        print(f"\nQuery: {query}")
        print(f"Best Match: {best_match}")
        print(f"Similarity Score: {score:.4f}")
        if best_match:
            # Print first few items
            print(f"Value (first 3): {value[:3]}...")
        print("-" * 50) 