import json
import os
import pickle
import re
from functools import lru_cache
import numpy as np
from difflib import get_close_matches
from nltk.stem import PorterStemmer
import nltk
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
from dotenv import load_dotenv

# Download NLTK stopwords once
nltk.download("stopwords", quiet=True)
from nltk.corpus import stopwords


class EmbeddingMatcher:
    def __init__(
        self, json_path=None, model_name="text-embedding-3-small", use_cache=True
    ):
        """
        Initialize the EmbeddingMatcher with a JSON file containing ground truth data and OpenAI's embedding model.

        Args:
            json_path (str, optional): Path to the JSON file containing the ground truth data.
                                     If None, uses default path in data/ground_truth/ground_truth.json
            model_name (str, optional): Name of the OpenAI embedding model to use.
                                      Defaults to 'text-embedding-3-small'.
                                      Options: 'text-embedding-3-small', 'text-embedding-3-large', 'text-embedding-ada-002'
            use_cache (bool, optional): Whether to cache embeddings to a file. Defaults to True.
        """
        # Load environment variables from .env file
        # load_dotenv will search up the directory tree for .env
        load_dotenv()

        # Initialize OpenAI client
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. Please add it to .env file."
            )
        self.client = OpenAI(api_key=self.api_key)

        # Initialize stemmer and stopwords
        self.stemmer = PorterStemmer()
        try:
            self.stop_words = set(stopwords.words("english"))
        except LookupError:
            # Basic set of stop words if NLTK data is not available
            self.stop_words = {
                "a",
                "an",
                "the",
                "and",
                "or",
                "of",
                "to",
                "in",
                "for",
                "on",
                "by",
                "with",
                "about",
            }
            print("Warning: NLTK stopwords not available. Using basic stopwords list.")

        if json_path is None:
            # Get the project root directory (2 levels up from this file)
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            json_path = os.path.join(
                project_root, "data", "ground_truth", "ground_truth.json"
            )

        self.json_path = json_path
        self.model_name = model_name
        self.use_cache = use_cache
        self.ground_truth = self._load_json()
        self.keys = list(self.ground_truth.keys())

        # Create keyword mappings for better fuzzy matching
        self.preprocessed_keys = {self._preprocess_text(k): k for k in self.keys}
        self.keyword_to_keys = self._build_keyword_index()

        # Cache file path
        self.cache_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "cache"
        )
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_file = os.path.join(
            self.cache_dir,
            f"openai_embeddings_{os.path.basename(json_path)}_{model_name.replace('/', '_')}.pkl",
        )

        self.key_embeddings = self._generate_key_embeddings()

    def _load_json(self):
        """Load the JSON file containing the ground truth data."""
        with open(self.json_path, "r") as f:
            return json.load(f)

    def _preprocess_text(self, text):
        """
        Preprocess text by converting to lowercase, removing punctuation,
        removing stop words, and stemming.
        """
        # Convert to lowercase and remove punctuation
        text = re.sub(r"[^\w\s]", " ", text.lower())
        # Tokenize, remove stop words, and stem
        tokens = [
            self.stemmer.stem(word)
            for word in text.split()
            if word not in self.stop_words
        ]
        return " ".join(tokens)

    def _build_keyword_index(self):
        """
        Build an index mapping important keywords to the keys that contain them.
        This helps with fuzzy matching when only part of a query matches a key.
        """
        keyword_index = {}
        for key in self.keys:
            # Extract important words (nouns, verbs, adjectives) from the key
            # For simplicity, we'll just use all non-stopwords
            words = [
                word.lower()
                for word in re.findall(r"\b\w+\b", key)
                if word.lower() not in self.stop_words
            ]

            # Add each word to the index
            for word in words:
                if len(word) > 3:  # Only index words longer than 3 characters
                    stemmed = self.stemmer.stem(word)
                    if stemmed not in keyword_index:
                        keyword_index[stemmed] = []
                    keyword_index[stemmed].append(key)

        return keyword_index

    def _get_openai_embedding(self, text):
        """Get embedding from OpenAI API for a single text string."""
        response = self.client.embeddings.create(
            model=self.model_name, input=text, encoding_format="float"
        )
        return response.data[0].embedding

    def _get_openai_embeddings_batch(self, texts, batch_size=100):
        """Get embeddings from OpenAI API for a batch of texts."""
        all_embeddings = []

        # Process in batches to avoid rate limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            print(
                f"Processing batch {i // batch_size + 1}/{(len(texts) - 1) // batch_size + 1}..."
            )

            response = self.client.embeddings.create(
                model=self.model_name, input=batch, encoding_format="float"
            )

            # Extract embeddings from response
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def _generate_key_embeddings(self):
        """Generate embeddings for each key in the ground truth data. Uses cache if available."""
        if self.use_cache and os.path.exists(self.cache_file):
            print(f"Loading embeddings from cache: {self.cache_file}")
            with open(self.cache_file, "rb") as f:
                cached_data = pickle.load(f)
                # Verify that the cache is valid for the current keys and model
                if (
                    cached_data.get("keys") == self.keys
                    and cached_data.get("model") == self.model_name
                ):
                    return cached_data.get("embeddings")
                else:
                    print(
                        "Cache invalid: keys or model have changed. Regenerating embeddings."
                    )

        print(
            f"Generating OpenAI embeddings for {len(self.keys)} keys using model {self.model_name}..."
        )
        embeddings = self._get_openai_embeddings_batch(self.keys)

        if self.use_cache:
            with open(self.cache_file, "wb") as f:
                pickle.dump(
                    {
                        "keys": self.keys,
                        "embeddings": embeddings,
                        "model": self.model_name,
                    },
                    f,
                )
            print(f"Embeddings cached to: {self.cache_file}")

        return embeddings

    @lru_cache(maxsize=128)
    def _encode_query(self, query_key):
        """Encode a query string into an embedding vector. This method is cached for performance."""
        return self._get_openai_embedding(query_key)

    def _keyword_search(self, query):
        """
        Search for keys that contain keywords from the query.
        Returns a list of potential matching keys.
        """
        query_words = [
            self.stemmer.stem(word)
            for word in query.lower().split()
            if word not in self.stop_words and len(word) > 3
        ]

        matching_keys = {}
        for word in query_words:
            stemmed = self.stemmer.stem(word)
            if stemmed in self.keyword_to_keys:
                for key in self.keyword_to_keys[stemmed]:
                    matching_keys[key] = matching_keys.get(key, 0) + 1

        # Sort by the number of matching keywords
        return sorted(matching_keys.items(), key=lambda x: x[1], reverse=True)

    def debug_similarity(self, query_key, top_n=5):
        """
        Debug function to show similarity scores between query and ground truth keys.

        Args:
            query_key (str): The query to test
            top_n (int): Number of top matches to display

        Returns:
            list: The top N matches with their similarity scores
        """
        # Get query embedding
        query_embedding = self._encode_query(query_key)
        similarities = cosine_similarity([query_embedding], self.key_embeddings)[0]

        # Get indices of top N matches
        top_indices = np.argsort(similarities)[::-1][:top_n]

        # Collect results
        results = []
        print(f"\n{'=' * 20} SIMILARITY DEBUG FOR: '{query_key}' {'=' * 20}")
        print(f"{'Ground Truth Key':<50} | {'Similarity':<10} | {'Has Policy':<10}")
        print(f"{'-' * 50}-+-{'-' * 10}-+-{'-' * 10}")

        for idx in top_indices:
            key = self.keys[idx]
            score = similarities[idx]
            has_policy = "GELS - Platinum" in self.ground_truth[key]

            print(f"{key[:50]:<50} | {score:.4f}     | {'✓' if has_policy else '✗'}")
            results.append((key, score, has_policy))

        # Try to find preprocessed, keyword, and fuzzy matches as well
        print(f"\n{'=' * 20} OTHER MATCHING METHODS {'=' * 20}")

        # Preprocessed text match
        preprocessed_query = self._preprocess_text(query_key)
        if preprocessed_query in self.preprocessed_keys:
            original_key = self.preprocessed_keys[preprocessed_query]
            print(f"Preprocessed Match: {original_key} (Score: 0.95)")
        else:
            print("No preprocessed match found")

        # Keyword-based match
        keyword_matches = self._keyword_search(query_key)
        if keyword_matches:
            print(f"Keyword Matches: {keyword_matches[:3]}")
        else:
            print("No keyword matches found")

        # Fuzzy string match
        fuzzy_matches = get_close_matches(query_key, self.keys, n=3, cutoff=0.5)
        if fuzzy_matches:
            print(f"Fuzzy Matches: {fuzzy_matches}")
        else:
            print("No fuzzy matches found")

        print(f"{'=' * 70}\n")
        return results

    def find_best_match(self, query_key, threshold=0.7, use_fuzzy=True, debug=False):
        """
        Find the best matching key for a given query key using multiple strategies.

        Matching Strategy Levels (in order):
        1. Semantic matching via OpenAI embeddings (best for understanding meaning)
        2. Preprocessed text matching (stemming, stopword removal)
        3. Keyword-based matching (finding keys containing important words)
        4. Fuzzy string matching (last resort for typos and minor variations)

        Args:
            query_key (str): The query key to find a match for.
            threshold (float, optional): The minimum similarity score to consider a match. Defaults to 0.7.
            use_fuzzy (bool, optional): Whether to use fallback matching strategies. Defaults to True.
            debug (bool, optional): Whether to print debug information. Defaults to False.

        Returns:
            tuple: A tuple containing the best matching key and the similarity score.
                  If no match is found, returns (None, 0.0).
                  Also includes a string indicating which matching level was used.
        """
        match_info = {"key": None, "score": 0.0, "level": None}

        # Print debug info if requested
        if debug:
            self.debug_similarity(query_key)

        # Get query embedding once for reuse
        query_embedding = self._encode_query(query_key)
        similarities = cosine_similarity([query_embedding], self.key_embeddings)[0]

        # =============== LEVEL 1: Semantic Matching ===============
        best_match_idx = np.argmax(similarities)
        best_match_score = similarities[best_match_idx]

        if best_match_score >= threshold:
            return self.keys[best_match_idx], best_match_score, "semantic"

        # If we're not using fuzzy matching, stop here
        if not use_fuzzy:
            return None, 0.0, None

        # =============== LEVEL 2: Preprocessed Text Matching ===============
        preprocessed_query = self._preprocess_text(query_key)
        if preprocessed_query in self.preprocessed_keys:
            original_key = self.preprocessed_keys[preprocessed_query]
            return original_key, 0.95, "preprocessed"

        # =============== LEVEL 3: Keyword-based Matching ===============
        keyword_matches = self._keyword_search(query_key)
        if keyword_matches:
            top_key, match_count = keyword_matches[0]

            # Calculate a score based on how many keywords matched
            query_word_count = len([w for w in query_key.split() if len(w) > 3])
            key_word_count = len([w for w in top_key.split() if len(w) > 3])
            coverage = match_count / max(1, min(query_word_count, key_word_count))

            # Only return if we have a good keyword match
            if coverage >= 0.5:
                # Find the actual similarity for consistent scoring
                key_idx = self.keys.index(top_key)
                actual_score = similarities[key_idx]
                return top_key, max(0.75, actual_score), "keyword"

        # =============== LEVEL 4: Fuzzy String Matching ===============
        fuzzy_matches = get_close_matches(query_key, self.keys, n=3, cutoff=0.5)
        if fuzzy_matches:
            # Try all fuzzy matches to find the one with highest semantic similarity
            best_fuzzy_key = None
            best_fuzzy_score = 0

            for match in fuzzy_matches:
                idx = self.keys.index(match)
                sim_score = similarities[idx]
                if sim_score > best_fuzzy_score:
                    best_fuzzy_score = sim_score
                    best_fuzzy_key = match

            if best_fuzzy_score > 0.5:  # Minimum reasonable similarity
                return best_fuzzy_key, best_fuzzy_score, "fuzzy"

            # If all else fails, just return the top fuzzy match with a base score
            return fuzzy_matches[0], 0.6, "fuzzy_fallback"

        # No match found
        return None, 0.0, None

    def get_value(self, query_key, threshold=0.7, use_fuzzy=True, debug=False):
        """
        Get the value (list of policy files) for a given query key.

        Args:
            query_key (str): The query key to find a match for.
            threshold (float, optional): The minimum similarity score to consider a match. Defaults to 0.7.
            use_fuzzy (bool, optional): Whether to use fuzzy string matching as a fallback. Defaults to True.
            debug (bool, optional): Whether to print debug information. Defaults to False.

        Returns:
            tuple: A tuple containing:
                  - The list of policy files
                  - Match information (key, score, matching level)
                  If no match is found, returns ([], (None, 0.0, None)).
        """
        best_match, score, level = self.find_best_match(
            query_key, threshold, use_fuzzy, debug
        )
        if best_match:
            return self.ground_truth[best_match], (best_match, score, level)
        else:
            return [], (None, 0.0, None)

    def get_values_batch(self, queries, threshold=0.7, use_fuzzy=True, debug=False):
        """
        Process a batch of queries and return values in the required format.

        Args:
            queries (list): List of query strings to process
            threshold (float, optional): The minimum similarity score to consider a match. Defaults to 0.7.
            use_fuzzy (bool, optional): Whether to use fuzzy matching as a fallback. Defaults to True.
            debug (bool, optional): Whether to print debug information. Defaults to False.

        Returns:
            dict: A dictionary where keys are the original queries and values are either:
                 - A dictionary with 'values' (the list of policy files) and 'matched_key' (the actual matched key)
                 - "NOT_EXIST" if no match is found
        """
        results = {}

        for query in queries:
            best_match, score, level = self.find_best_match(
                query, threshold, use_fuzzy, debug
            )
            if best_match:
                results[query] = {
                    "values": self.ground_truth[best_match],
                    "matched_key": best_match,
                }
            else:
                results[query] = "NOT_EXIST"

        return results


# Example usage
if __name__ == "__main__":
    matcher = EmbeddingMatcher(use_cache=True)  # Uses default path with caching

    # print("\n=== Testing with OpenAI Semantic Matching ===")
    ## Try a few different queries
    # test_queries = [
    #    "Loss of baggage",
    #    "Medical expenses overseas",
    #    "Trip cancellation",
    #    "Baggage delay"
    # ]

    # for query in test_queries:
    #    value, (best_match, score, level) = matcher.get_value(query)
    #    print(f"\nQuery: {query}")
    #    print(f"Best Match: {best_match}")
    #    print(f"Similarity Score: {score:.4f}")
    #    print(f"Matching Level: {level}")
    #    if best_match:
    #        # Print first few items
    #        print(f"Value (first 3): {value[:3]}...")
    #    print("-" * 50)

    # print("\n=== Testing Passport and Document Queries with Enhanced Matching ===")
    ## Try a few queries with typos or variations
    # fuzzy_queries = [
    #    "Lost passport",
    #    "Passport theft",
    #    "Lost of passport",
    #    "Stolen money",
    #    "Document theft",
    #    "pet accommodation",
    #    "double indemnity",
    #    "Emergency treatment",
    # ]

    # for query in fuzzy_queries:
    #    value, (best_match, score, level) = matcher.get_value(query, use_fuzzy=True)
    #    print(f"\nQuery: {query}")
    #    print(f"Best Match: {best_match}")
    #    print(f"Similarity Score: {score:.4f}")
    #    print(f"Matching Level: {level}")
    #    if best_match:
    #        # Print first few items
    #        print(f"Value (first 3): {value[:3]}...")
    #    print("-" * 50)

    print("\n=== Testing Sport & Pet Queries ===")
    sport_queries = [
        # "Recreational skiing",
        # "Hot Air Ballooning",
        # "White Water Rafting",
        # "scuba diving",
        "Pet Accommodation Coverage"
    ]

    for query in sport_queries:
        value, (best_match, score, level) = matcher.get_value(
            query, use_fuzzy=True, debug=True
        )
        print(f"\nQuery: {query}")
        print(f"Best Match: {best_match}")
        print(f"Similarity Score: {score:.4f}")
        print(f"Matching Level: {level}")

    # print("\n=== Testing Batch Processing ===")
    # batch_queries = [
    #    "Loss of baggage",
    #    "Non-existent query that should return NOT_EXIST",
    #    "Medical expenses overseas",
    #    "Another fake query"
    # ]

    # batch_results = matcher.get_values_batch(batch_queries)
    # for query, result in batch_results.items():
    #    print(f"\nQuery: {query}")
    #    if result == "NOT_EXIST":
    #        print("Result: NOT_EXIST")
    #    else:
    #        print(f"Result: {result}")
    # print("-" * 50)
