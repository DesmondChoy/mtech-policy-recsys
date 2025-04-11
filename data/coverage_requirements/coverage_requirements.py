"""
Coverage Requirements Dictionary

This module defines the standard coverage requirements for travel insurance policies.
These requirements represent the most critical coverage types that customers look for
when selecting travel insurance.

This dictionary is used for:
1. Generating synthetic transcripts
2. Evaluating if transcripts were generated correctly
3. Providing a reference for policy analysis
"""

coverage_requirements = {
    "trip_cancellation": {
        "name": "Trip Cancellation",
        "description": "Coverage for expenses if you need to cancel your trip due to covered reasons",
        "key_features": [
            "Illness or injury",
            "Death of traveler or family member",
            "Natural disasters",
            "Travel provider bankruptcy",
        ],
        "typical_exclusions": [
            "Pre-existing conditions",
            "Change of mind",
            "Work-related reasons",
        ],
    },
    "medical_coverage": {  # Renamed from medical_expenses
        "name": "Medical Coverage",  # Renamed
        "description": "Coverage for medical treatment needed during your trip",
        "key_features": [
            "Emergency medical treatment",
            "Hospital stays",
            "Prescription medications",
            "Doctor visits",
        ],
        "typical_exclusions": [
            "Pre-existing conditions",
            "Routine check-ups",
            "Elective procedures",
        ],
    },
    "lost_damaged_luggage": {  # Renamed from baggage_loss_delay
        "name": "Lost/Damaged Luggage",  # Renamed
        "description": "Coverage for lost, damaged, or delayed baggage during your trip",
        "key_features": [
            "Reimbursement for lost items",
            "Essential purchases during delay",
            "Damaged luggage",
        ],
        "typical_exclusions": [
            "Certain valuable items",
            "Electronics",
            "Cash",
            "Delays under certain hours",
        ],
    },
    "travel_delays": {  # Renamed from travel_delay
        "name": "Travel Delays",  # Renamed
        "description": "Coverage for additional expenses due to a significant delay in your travel plans",
        "key_features": [
            "Accommodation expenses",
            "Meal expenses",
            "Alternative transportation",
            "Missed connections",
        ],
        "typical_exclusions": [
            "Delays less than specified hours",
            "Known events before departure",
            "Carrier-provided compensation",
        ],
    },
    "sports_adventure": {
        "name": "Sports and Adventure Activities",
        "description": "Coverage for medical expenses or evacuation related to participation in specified sports or adventure activities.",
        "key_features": [
            "Coverage for injuries during listed activities (e.g., skiing, scuba diving)",
            "Emergency assistance related to activity",
            "Equipment damage/loss (sometimes optional)",
        ],
        "typical_exclusions": [
            "Professional sports participation",
            "Unlisted high-risk activities (e.g., base jumping)",
            "Activities against local advice/laws",
            "Lack of proper certification/guidance",
        ],
    },
}

customer_context_options = {
    "age_group": {
        "options": ["18-25", "26-40", "41-55", "56-65", "65+"],
        "prompt_phrases": [  # Example ways to mention this in a transcript
            "The travelers are in the {value} age group.",
            "We're mostly around {value} years old.",
        ],
    },
    "travelers_count": {
        "options": [1, 2, 3, 4, 5],  # Could also be a range function
        "prompt_phrases": [
            "There will be {value} of us traveling.",
            "It's a trip for {value}.",
            "Just myself this time.",  # Special phrase for 1
        ],
    },
    "budget_range": {
        "options": ["$100-$200", "$200-$300", "around $400", "flexible"],
        "prompt_phrases": [
            "Our budget for insurance is about {value}.",
            "We're hoping to spend {value}.",
        ],
    },
    "pre_existing_conditions": {
        "options": [
            None,
            ["asthma"],
            ["diabetes"],
            ["high blood pressure"],
        ],
        "prompt_phrases": [
            "One traveler has {value}.",
            "Do we need to declare {value}?",
            "No, no pre-existing conditions.",
        ],
    },
    "travel_destination": {
        "options": ["Japan", "Europe", "USA", "Australia", "Thailand", "UK"],
        "prompt_phrases": [
            "The destination is {value}.",
            "We're planning a trip to {value}.",
        ],
    },
    "travel_duration": {
        "options": ["1 week", "10 days", "2 weeks", "3 weeks", "1 month"],
        "prompt_phrases": [
            "It will be a {value} trip.",
            "We'll be away for {value}.",
        ],
    },
    "travel_origin": {
        "options": ["Singapore"],
        "prompt_phrases": [
            "We'll be traveling from {value}.",
            "Our trip starts in {value}.",
            "We're based in {value}.",
        ],
    },
    "activities_to_cover": {
        "options": [
            None,
            # Water activities
            ["Scuba Diving"],
            ["Paddleboarding"],
            ["White Water Rafting"],
            ["Snorkeling"],
            ["Surfing"],
            ["Water Skiing"],
            # Winter activities
            ["Skiing"],
            ["Snowboarding"],
            ["Snowmobiling"],
            ["Ice Skating"],
            # Air activities
            ["Bungee Jumping"],
            ["Skydiving"],
            ["Paragliding"],
            ["Abseiling"],
            ["Hot Air Ballooning"],
            # Outdoor activities
            ["Hiking"],
            ["Trekking"],
            ["Motorcycling"],
            ["Rock Climbing"],
            ["Camping"],
        ],
        "prompt_phrases": [
            "We plan to do {value} during our trip.",
            "We'll be participating in {value}.",
            "We need coverage for {value}.",
            "We're interested in {value}.",
            "We want to try {value}.",
            "No special activities planned.",  # Phrase for None
        ],
    },
    "medical_needs": {
        "options": [
            None,
            ["Wheelchair"],
            ["Oxygen tank"],
            ["CPAP machine"],
            ["Insulin pump"],
        ],
        "prompt_phrases": [
            "We need to bring {value} with us.",
            "We require {value} for medical reasons.",
            "We have {value} that needs to be covered.",
            "No special medical equipment needed.",  # Phrase for None
        ],
    },
}


# Add a helper function to access this new dictionary
def get_customer_context_options():
    """Returns the customer context options dictionary."""
    return customer_context_options


# For easy importing
def get_coverage_requirements():
    """
    Returns the coverage requirements dictionary.

    Returns:
        dict: A dictionary containing standardized coverage requirements for travel insurance.
    """
    return coverage_requirements


# Get a list of all coverage types
def get_coverage_types():
    """
    Returns a list of all coverage type keys.

    Returns:
        list: A list of strings representing all coverage type keys.
    """
    return list(coverage_requirements.keys())


# Get a specific coverage requirement by key
def get_coverage(coverage_type):
    """
    Returns a specific coverage requirement by its key.

    Args:
        coverage_type (str): The key of the coverage type to retrieve.

    Returns:
        dict: The coverage requirement dictionary for the specified type.
        None: If the coverage type does not exist.
    """
    return coverage_requirements.get(coverage_type)
