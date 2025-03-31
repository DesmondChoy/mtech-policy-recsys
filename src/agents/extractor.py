from crewai import Agent, Crew, Task
from src.utils.transcript_processing import TravelInsuranceRequirement

# Step 1: Requirement Extraction Agent - Processes Call Transcripts
transcript_analyst = Agent(
    role="Call Transcript Analyst",
    goal="Extract and structure travel insurance customer requirements from call transcripts into a validated JSON object.",
    backstory=(
        "A seasoned customer service analyst specializing in extracting travel insurance requirements from call transcripts. "
        "This agent listens to conversations between customers and service staff, identifies key requirements, and formats "
        "the insights into a structured JSON output that conforms to the TravelInsuranceRequirement model for accurate policy matching."
    ),
    allow_delegation=False,
    verbose=True
)

# Define the agent task
transcript_analyst_task = Task(
    description="""Analyze the travel insurance call transcript below and extract key customer requirements.
Step 1: Read the transcript carefully and extract all relevant details. For each field in the schema, provide a brief annotation or reference to the specific portion(s) of the transcript where the detail was found.
Step 2: Review your annotations to verify that every extracted detail directly matches the transcript. Resolve any discrepancies or conflicts in the data.
Step 3: Produce a final, validated JSON object that adheres exactly to the TravelInsuranceRequirement schema with the following fields:
- requirement_id (str): A unique identifier.
- requirement_summary (str): A concise summary of the customer's insurance needs.
- detailed_description (str): A detailed narrative extracted from the transcript.
- travel_destination (Optional[str]): The destination (country or region) mentioned.
- travel_duration (Optional[str]): Duration of the trip (e.g., "7 days", "1 month").
- travel_start_date (Optional[date]): The travel start date.
- travel_end_date (Optional[date]): The travel end date.
- insurance_coverage_type (Optional[List[str]]): The types of insurance coverage requested (e.g., ["Medical", "Trip Cancellation"]).
- pre_existing_conditions (Optional[List[str]]): Any pre-existing conditions mentioned.
- age_group (Optional[str]): Age bracket of the travelers (e.g., "26-40").
- travelers_count (Optional[int]): Number of travelers.
- budget_range (Optional[str]): Budget constraints (e.g., "$100-$200").
- preferred_insurance_provider (Optional[str]): Preferred insurance provider, if any.
- additional_requests (Optional[str]): Any special requests or concerns.
- keywords (Optional[List[str]]): Important keywords or terms for further analysis.

If a field is not mentioned in the transcript, use null.

Transcript:
{parsed_transcripts}
""",
    expected_output="A JSON object that matches the TravelInsuranceRequirement model.",
    agent=transcript_analyst,
    output_json=TravelInsuranceRequirement,
    output_file="insurance_requirement.json"
)

# Define the crew with agents and tasks
insurance_recommendation_crew = Crew(
    agents=[transcript_analyst],
    tasks=[transcript_analyst_task],
    verbose=True
)

def main():
    # Execute the crew to process transcripts
    # TODO: populate and make it work
    result = insurance_recommendation_crew.kickoff()
    return result

if __name__ == "__main__":
    main()

