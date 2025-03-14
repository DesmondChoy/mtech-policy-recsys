from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class TravelInsuranceRequirement(BaseModel):
    requirement_id: str  # Unique identifier for tracking
    call_id: str  # Unique identifier for the call
    
    requirement_summary: str  # Summary of the customer’s insurance needs
    detailed_description: str  # More detailed requirement extracted from transcript

    travel_destination: Optional[str]  # Country or region the user is traveling to
    travel_duration: Optional[str]  # e.g., "7 days", "1 month", "6 months"
    travel_start_date: Optional[date]  # Date when the travel begins
    travel_end_date: Optional[date]  # Date when the travel ends
    
    insurance_coverage_type: Optional[List[str]]  # e.g., ["Medical", "Trip Cancellation", "Baggage Loss"]
    pre_existing_conditions: Optional[List[str]]  # Any health conditions to be covered
    age_group: Optional[str]  # e.g., "18-25", "26-40", "41-60", "Senior"
    travelers_count: Optional[int]  # Number of travelers to be insured
    
    budget_range: Optional[str]  # e.g., "$50-$100", "$100-$200"
    preferred_insurance_provider: Optional[str]  # If the user has a preference
    
    pain_points: Optional[List[str]]  # Customer’s concerns (e.g., "high cost", "slow claims process")
    additional_requests: Optional[str]  # Any special requests, like "Coverage for adventure sports"
    
    keywords: Optional[List[str]]  # Important keywords for analytics
    transcript_snippet: Optional[str]  # Relevant excerpt from transcript for context