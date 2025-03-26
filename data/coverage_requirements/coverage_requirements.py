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
    "medical_expenses": {
        "name": "Medical Expenses",
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
    "emergency_evacuation": {
        "name": "Emergency Evacuation",
        "description": "Coverage for transportation to adequate medical facilities or back home in case of emergency",
        "key_features": [
            "Medical evacuation",
            "Repatriation",
            "Transportation to adequate facility",
        ],
        "typical_exclusions": ["Non-emergency situations", "Unauthorized evacuations"],
    },
    "baggage_loss_delay": {
        "name": "Baggage Loss/Delay",
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
    "travel_delay": {
        "name": "Travel Delay",
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
}


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
