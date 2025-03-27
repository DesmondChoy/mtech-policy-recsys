"""
Prompt templates for transcript evaluation.

This module contains prompt templates and formatting functions for evaluating
conversation transcripts using LLMs.
"""

from typing import Dict, List, Any


def format_transcript_for_prompt(transcript):
    """
    Format a transcript for inclusion in a prompt.

    Args:
        transcript (list): List of dictionaries containing speaker and dialogue

    Returns:
        str: Formatted transcript text
    """
    formatted_lines = []
    for i, entry in enumerate(transcript):
        line_number = i + 1
        formatted_lines.append(
            f"[{line_number}] {entry['speaker']}: {entry['dialogue']}"
        )

    return "\n".join(formatted_lines)


def format_coverage_requirements_for_prompt(coverage_requirements):
    """
    Format coverage requirements for inclusion in a prompt.

    Args:
        coverage_requirements (dict): Dictionary of coverage requirements

    Returns:
        str: Formatted coverage requirements text
    """
    formatted_lines = []

    for coverage_type, details in coverage_requirements.items():
        formatted_lines.append(f"Coverage Type: {details['name']}")
        formatted_lines.append(f"Description: {details['description']}")
        formatted_lines.append("Key Features:")
        for feature in details["key_features"]:
            formatted_lines.append(f"- {feature}")
        formatted_lines.append("Typical Exclusions:")
        for exclusion in details["typical_exclusions"]:
            formatted_lines.append(f"- {exclusion}")
        formatted_lines.append("")

    return "\n".join(formatted_lines)


def construct_evaluation_prompt(transcript, coverage_requirements):
    """
    Construct a detailed prompt for Gemini to evaluate coverage requirements.

    Args:
        transcript (list): List of dictionaries containing speaker and dialogue
        coverage_requirements (dict): Dictionary of coverage requirements

    Returns:
        str: Complete evaluation prompt
    """
    formatted_transcript = format_transcript_for_prompt(transcript)
    formatted_requirements = format_coverage_requirements_for_prompt(
        coverage_requirements
    )

    prompt = f"""You are an expert judge evaluating if a customer service agent gathered all required travel insurance coverage information from a customer.

COVERAGE REQUIREMENTS:
{formatted_requirements}

TRANSCRIPT:
{formatted_transcript}

EVALUATION TASK:
For each coverage type, determine:
1. If the customer mentioned the coverage type
2. If specific details about the coverage were provided
3. If the agent appropriately probed for more information when needed

EVALUATION CRITERIA:
- PASS: The coverage type was mentioned AND specific details were provided (either volunteered by the customer or elicited by the agent)
- FAIL: The coverage type was not mentioned OR was mentioned without specific details

FORMAT YOUR RESPONSE AS JSON:
{{
  "evaluations": [
    {{
      "coverage_type": "trip_cancellation",
      "name": "Trip Cancellation",
      "result": "PASS",
      "justification": "The customer mentioned needing trip cancellation coverage and specified they were concerned about illness and natural disasters.",
      "customer_quote": "I need trip cancellation coverage in case I get sick or there's a hurricane.",
      "agent_performance": "PASS",
      "agent_performance_justification": "The agent confirmed the requirement and asked appropriate follow-up questions.",
      "agent_quote": "I understand you need trip cancellation. Are there any specific scenarios you're concerned about?"
    }},
    ... include evaluations for all coverage types ...
  ],
  "summary": {{
    "total_requirements": 5,
    "requirements_met": 4,
    "overall_assessment": "Brief overall assessment of both coverage gathering and agent performance"
  }}
}}

IMPORTANT: 
1. Include evaluations for ALL coverage types in the requirements.
2. Always include direct quotes from the transcript to support your evaluations.
3. Be objective and thorough in your assessment.
4. Ensure your response is valid JSON.
"""

    return prompt
