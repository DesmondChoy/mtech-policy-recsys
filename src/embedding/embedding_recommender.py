import os
import json
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import logging
from sklearn.metrics.pairwise import cosine_similarity
from flatten_json import flatten
import tqdm
import pickle
from dotenv import load_dotenv
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmbeddingRecommender:
    """
    A recommendation system that uses embeddings to match user requirements 
    with insurance policies.
    """
    
    def __init__(self, 
                 policies_dir: str = None,
                 embedding_cache_path: str = None,
                 embedding_model_name: str = "text-embedding-3-small"):
        """
        Initialize the recommender system.
        
        Args:
            policies_dir: Directory containing processed policy JSON files
            embedding_cache_path: Path to save/load embeddings cache
            embedding_model_name: Name of the OpenAI embedding model to use
        """
        self.policies_dir = policies_dir or os.path.join("data", "processed_policies")
        self.embedding_cache_path = embedding_cache_path or os.path.join("data", "embeddings_cache.pkl")
        self.embedding_model_name = embedding_model_name
        self.policy_embeddings = {}
        self.policies = {}
    
    def load_policies(self) -> None:
        """
        Load all policy JSON files from the policies directory.
        """
        logger.info(f"Loading policies from {self.policies_dir}")
        policy_files = [f for f in os.listdir(self.policies_dir) 
                       if f.endswith(".json") or (os.path.isfile(os.path.join(self.policies_dir, f)) 
                                                and not f.startswith("."))]
        
        for filename in policy_files:
            filepath = os.path.join(self.policies_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    policy_data = json.load(f)
                    policy_id = f"{policy_data.get('provider_name', 'Unknown')}-{policy_data.get('tier_name', 'Unknown')}"
                    self.policies[policy_id] = policy_data
                    logger.info(f"Loaded policy: {policy_id}")
            except json.JSONDecodeError:
                logger.error(f"Error decoding JSON from {filepath}")
            except Exception as e:
                logger.error(f"Error loading policy file {filepath}: {str(e)}")
        
        logger.info(f"Loaded {len(self.policies)} policies")
    
    def flatten_policy(self, policy_json: Dict) -> str:
        """
        Flatten a nested policy JSON into a single string for embedding.
        """
        flat_policy = flatten(policy_json)
        # Convert the flattened dictionary into a string with key-value pairs
        text_chunks = [f"{key}: {value}" for key, value in flat_policy.items()]
        return "\n".join(text_chunks)
    
    def flatten_requirement(self, req_json: Dict) -> str:
        """
        Flatten a nested requirement JSON into a single string for embedding.
        """
        # Extract key information for embedding
        chunks = [
            f"Summary: {req_json.get('requirement_summary', '')}",
            f"Description: {req_json.get('detailed_description', '')}",
            f"Destination: {req_json.get('travel_destination', '')}",
            f"Duration: {req_json.get('travel_duration', '')}",
            f"Coverage Types: {', '.join(req_json.get('insurance_coverage_type', []))}",
            f"Age Group: {req_json.get('age_group', '')}",
            f"Travelers Count: {req_json.get('travelers_count', '')}",
            f"Additional Requests: {req_json.get('additional_requests', '')}",
            f"Keywords: {', '.join(req_json.get('keywords', []))}"
        ]
        return "\n".join(chunks)
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embeddings for text using OpenAI's API.
        
        Args:
            text: The text to generate embeddings for
            
        Returns:
            numpy.ndarray: The embedding vector
            
        Raises:
            Exception: If there's an error generating the embedding
        """
        try:
            # Load environment variables
            load_dotenv()
            
            # Initialize OpenAI client
            client = OpenAI()
            
            # Generate embedding
            response = client.embeddings.create(
                model=self.embedding_model_name,  # "text-embedding-3-small"
                input=text,
                encoding_format="float"  # Ensure we get float values
            )
            
            # Convert to numpy array
            return np.array(response.data[0].embedding)
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            # Return zero vector as fallback
            return np.zeros(1536)  # OpenAI text-embedding-3-small dimension
    
    def generate_policy_embeddings(self, force_refresh: bool = False) -> None:
        """
        Generate embeddings for all policies and cache them.
        
        Args:
            force_refresh: If True, regenerate all embeddings even if cache exists
        """
        # Check if we need to load policies first
        if not self.policies:
            self.load_policies()
        
        # Try to load from cache if it exists and we're not forcing refresh
        if os.path.exists(self.embedding_cache_path) and not force_refresh:
            try:
                with open(self.embedding_cache_path, 'rb') as f:
                    self.policy_embeddings = pickle.load(f)
                logger.info(f"Loaded {len(self.policy_embeddings)} policy embeddings from cache")
                return
            except Exception as e:
                logger.error(f"Error loading embeddings cache: {str(e)}")
        
        # Generate embeddings for each policy
        logger.info("Generating policy embeddings")
        for policy_id, policy_data in tqdm.tqdm(self.policies.items()):
            flattened_policy = self.flatten_policy(policy_data)
            self.policy_embeddings[policy_id] = self.embed_text(flattened_policy)
        
        # Cache the embeddings
        try:
            os.makedirs(os.path.dirname(self.embedding_cache_path), exist_ok=True)
            with open(self.embedding_cache_path, 'wb') as f:
                pickle.dump(self.policy_embeddings, f)
            logger.info(f"Cached {len(self.policy_embeddings)} policy embeddings")
        except Exception as e:
            logger.error(f"Error caching embeddings: {str(e)}")
    
    def recommend(self, requirement: Dict, top_n: int = 1) -> List[Tuple[str, float]]:
        """
        Recommend policies based on the user's requirements.
        
        Args:
            requirement: User requirement JSON
            top_n: Number of top recommendations to return
            
        Returns:
            List of tuples (policy_id, similarity_score) sorted by similarity
        """
        # Ensure policies and embeddings are loaded
        if not self.policies:
            self.load_policies()
        
        if not self.policy_embeddings:
            self.generate_policy_embeddings()
        
        # Generate embedding for requirement
        requirement_text = self.flatten_requirement(requirement)
        requirement_embedding = self.embed_text(requirement_text)
        
        # Calculate similarity scores
        similarities = []
        for policy_id, policy_embedding in self.policy_embeddings.items():
            similarity = cosine_similarity([requirement_embedding], [policy_embedding])[0][0]
            similarities.append((policy_id, similarity))
        
        # Sort by similarity score (descending)
        sorted_similarities = sorted(similarities, key=lambda x: x[1], reverse=True)
        
        return sorted_similarities[:top_n]
    
    def get_policy_details(self, policy_id: str) -> Optional[Dict]:
        """
        Get the full details of a policy by its ID.
        
        Args:
            policy_id: The ID of the policy to retrieve
            
        Returns:
            The policy data dictionary or None if not found
        """
        return self.policies.get(policy_id)


if __name__ == "__main__":
    # Example usage
    recommender = EmbeddingRecommender()
    
    # Load sample requirement
    requirement_path = os.path.join("data", "extracted_requirements", "insurance_requirement.json")
    with open(requirement_path, 'r') as f:
        requirement = json.load(f)
    
    # Get recommendations
    recommendations = recommender.recommend(requirement, top_n=3)
    
    print(f"Top recommendations for requirement {requirement['requirement_id']}:")
    for policy_id, similarity in recommendations:
        policy = recommender.get_policy_details(policy_id)
        if policy:
            print(f"- {policy_id} (Score: {similarity:.4f})")
            print(f"  Provider: {policy.get('provider_name')}")
            print(f"  Policy: {policy.get('policy_name')}, Tier: {policy.get('tier_name')}")
            
            # Find coverage types that match requirement
            req_coverage_types = requirement.get('insurance_coverage_type', [])
            for category in policy.get('coverage_categories', []):
                for coverage in category.get('coverages', []):
                    coverage_name = coverage.get('coverage_name', '').lower()
                    if any(req_type.lower() in coverage_name for req_type in req_coverage_types):
                        limit_info = []
                        for limit in coverage.get('limits', []):
                            if 'type' in limit and 'limit' in limit:
                                limit_info.append(f"{limit['type']}: {limit['limit']} {policy.get('currency', 'SGD')}")
                        
                        print(f"  - {coverage.get('coverage_name')}: {', '.join(limit_info)}")
            print() 