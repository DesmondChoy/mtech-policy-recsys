from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import sys
from pathlib import Path
import json
import logging

# Add the parent directory to sys.path to allow importing the EmbeddingRecommender
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.embedding.embedding_recommender import EmbeddingRecommender

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Insurance Policy Recommender API",
    description="API for recommending insurance policies based on user requirements",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize recommender on startup
recommender = None

@app.on_event("startup")
async def startup_event():
    global recommender
    policies_dir = os.environ.get("POLICIES_DIR", os.path.join("data", "processed_policies"))
    logger.info(f"Initializing recommender with policies from {policies_dir}")
    recommender = EmbeddingRecommender(policies_dir=policies_dir)
    recommender.generate_policy_embeddings()
    logger.info("Recommender initialized and ready")

# Input and output models
class RecommendationRequest(BaseModel):
    requirement: Dict[str, Any]
    top_n: Optional[int] = 1

class CoverageLimit(BaseModel):
    type: str
    limit: Any
    basis: Optional[str] = None

class Coverage(BaseModel):
    coverage_name: str
    limits: List[CoverageLimit]
    details: Optional[str] = None

class PolicySummary(BaseModel):
    policy_id: str
    provider_name: str
    policy_name: str
    tier_name: str
    similarity_score: float
    relevant_coverages: List[Coverage]

class RecommendationResponse(BaseModel):
    requirement_summary: str
    requested_coverage_types: List[str]
    recommendations: List[PolicySummary]

@app.post("/recommend", response_model=RecommendationResponse)
async def recommend(request: RecommendationRequest = Body(...)):
    global recommender
    
    if recommender is None:
        raise HTTPException(status_code=503, detail="Recommender is not initialized")
    
    # Get recommendations
    try:
        recommendations = recommender.recommend(request.requirement, top_n=request.top_n)
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")
    
    if not recommendations:
        return RecommendationResponse(
            requirement_summary=request.requirement.get("requirement_summary", ""),
            requested_coverage_types=request.requirement.get("insurance_coverage_type", []),
            recommendations=[]
        )
    
    # Format recommendations
    policy_summaries = []
    for policy_id, similarity in recommendations:
        policy = recommender.get_policy_details(policy_id)
        if not policy:
            continue
        
        # Find relevant coverages
        req_coverage_types = request.requirement.get("insurance_coverage_type", [])
        relevant_coverages = []
        
        for category in policy.get("coverage_categories", []):
            for coverage in category.get("coverages", []):
                coverage_name = coverage.get("coverage_name", "").lower()
                
                # Check if this coverage is relevant to the requirement
                if any(req_type.lower() in coverage_name for req_type in req_coverage_types):
                    # Format coverage limits
                    coverage_limits = []
                    for limit in coverage.get("limits", []):
                        coverage_limits.append(
                            CoverageLimit(
                                type=limit.get("type", "Unknown"),
                                limit=limit.get("limit", 0),
                                basis=limit.get("basis", None)
                            )
                        )
                    
                    # Add to relevant coverages
                    relevant_coverages.append(
                        Coverage(
                            coverage_name=coverage.get("coverage_name", ""),
                            limits=coverage_limits,
                            details=coverage.get("details", "")
                        )
                    )
        
        # Add policy summary
        policy_summaries.append(
            PolicySummary(
                policy_id=policy_id,
                provider_name=policy.get("provider_name", ""),
                policy_name=policy.get("policy_name", ""),
                tier_name=policy.get("tier_name", ""),
                similarity_score=similarity,
                relevant_coverages=relevant_coverages
            )
        )
    
    # Return response
    return RecommendationResponse(
        requirement_summary=request.requirement.get("requirement_summary", ""),
        requested_coverage_types=request.requirement.get("insurance_coverage_type", []),
        recommendations=policy_summaries
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "recommender_initialized": recommender is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 