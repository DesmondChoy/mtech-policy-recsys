# LLM Service Module Guide

This guide explains how to use the reusable LLM service module in this repository, which provides a convenient interface to Google's Gemini API.

## Table of Contents

1. [Introduction](#introduction)
2. [Setup and Installation](#setup-and-installation)
3. [Basic Usage](#basic-usage)
4. [Advanced Features](#advanced-features)
5. [Integration Examples](#integration-examples)
6. [Best Practices](#best-practices)

## Introduction

The LLM service module (`src/models/llm_service.py`) is a reusable component that simplifies interactions with Google's Gemini API. It provides a unified interface for various LLM operations, including content generation, structured output, streaming responses, and more.

### Key Features

- **Simple Interface**: Easy-to-use methods for common LLM operations
- **Structured Output**: Generate and parse JSON responses
- **Streaming Support**: Stream responses for real-time applications
- **Error Handling**: Built-in retry logic and validation
- **Configurability**: Support for different models and parameter sets
- **Batch Processing**: Process multiple prompts efficiently

## Setup and Installation

### Prerequisites

1. Python 3.8 or higher
2. Google Gemini API key
3. Required dependencies (listed in `requirements.txt`)

### Installation

1. Clone the repository (if you haven't already)
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your Google Gemini API key:
   - Create a `.env` file in the project root
   - Add your API key:
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```
   - Alternatively, set it as an environment variable

## Basic Usage

### Initializing the Service

```python
from src.models.llm_service import LLMService

# Initialize with API key from environment variables or .env file
llm_service = LLMService()

# Or provide API key directly
llm_service = LLMService(api_key="your_api_key_here")
```

### Simple Content Generation

```python
# Generate content with default parameters
prompt = "Explain how travel insurance works in 3 sentences."
response = llm_service.generate_content(prompt)

# Access the generated text
print(response.text)
```

## Advanced Features

### Structured Output (JSON)

Generate structured data in JSON format:

```python
prompt = """
Create a list of 3 travel insurance policies with the following information:
- Name
- Provider
- Coverage types
- Price range
"""

# Get response as a Python dictionary
structured_response = llm_service.generate_structured_content(prompt)
print(structured_response)  # Python dict
```

### Streaming Responses

Stream responses for real-time applications:

```python
prompt = "Write a short story about a traveler who forgot to buy travel insurance."

# Stream the response
for chunk in llm_service.stream_content(prompt):
    print(chunk, end="", flush=True)
```

### Batch Processing

Process multiple prompts efficiently:

```python
prompts = [
    "What is trip cancellation insurance?",
    "What is medical evacuation coverage?",
    "What is baggage loss protection?",
]

# Generate responses for all prompts
responses = llm_service.batch_generate(prompts)

# Process each response
for i, response in enumerate(responses):
    print(f"Response {i+1}: {response.text[:100]}...")
```

### Error Handling and Validation

Use retry logic and validation for robust applications:

```python
def validate_number(text):
    """Validate that the text contains a number between 1 and 10."""
    import re
    numbers = re.findall(r"\b([1-9]|10)\b", text)
    return len(numbers) > 0

# Generate with validation and retry
response = llm_service.generate_with_retry(
    prompt="Generate a number between 1 and 10.",
    validation_func=validate_number,
    max_retries=3
)
```

### Using Different Models and Parameters

Customize the model and generation parameters:

```python
# Use a specific model
response = llm_service.generate_content(
    prompt="What are the benefits of travel insurance?",
    model="gemini-2.0-flash"
)

# Use deterministic parameters (lower temperature)
response = llm_service.generate_content(
    prompt="List the top 5 travel insurance providers.",
    parameters={"temperature": 0.2, "max_output_tokens": 1024}
)

# Or use predefined parameter sets
from src.models.gemini_config import GeminiConfig

# Get deterministic parameters
deterministic_params = GeminiConfig.get_parameters("deterministic")

# Get creative parameters
creative_params = GeminiConfig.get_parameters("creative")

# Use in content generation
response = llm_service.generate_content(
    prompt="Write a creative story about travel insurance.",
    parameters=creative_params
)
```

## Integration Examples

### Using with Agents

```python
from src.agents.analyzer import Analyzer

class CustomAnalyzer(Analyzer):
    def __init__(self):
        # Initialize with the LLM service
        self.llm_service = LLMService()
    
    def analyze_policy(self, policy_text, requirements):
        prompt = f"""
        Analyze this insurance policy:
        {policy_text}
        
        Based on these requirements:
        {requirements}
        
        Provide a detailed analysis.
        """
        
        response = self.llm_service.generate_content(prompt)
        return response.text
```

### Processing Structured Data

```python
def extract_requirements(transcript):
    prompt = f"""
    Extract travel insurance requirements from this conversation:
    {transcript}
    
    Return a JSON object with the following structure:
    {{
        "destination": "country or region",
        "duration": "trip duration in days",
        "activities": ["list", "of", "planned", "activities"],
        "medical_conditions": ["list", "of", "pre-existing", "conditions"],
        "coverage_priorities": ["list", "in", "order", "of", "importance"]
    }}
    """
    
    # Use structured content generation
    requirements = llm_service.generate_structured_content(prompt)
    return requirements
```

## Best Practices

### Performance Optimization

1. **Use the Right Model**: Choose the appropriate model for your task:
   - `gemini-2.0-flash` for faster, more efficient responses
   - `gemini-2.0-pro` for more complex reasoning tasks

2. **Parameter Tuning**:
   - Lower temperature (0.1-0.3) for deterministic, factual responses
   - Higher temperature (0.7-1.0) for creative, diverse outputs
   - Adjust max_output_tokens based on expected response length

3. **Batch Processing**: Use batch_generate for multiple similar prompts

### Error Handling

1. **Always Use Try/Except**: Wrap API calls in try/except blocks
2. **Implement Retries**: Use generate_with_retry for critical operations
3. **Validate Responses**: Use validation functions to ensure response quality

### Prompt Engineering

1. **Be Specific**: Provide clear, detailed instructions
2. **Structure Matters**: Format prompts with clear sections and examples
3. **For JSON Responses**: Explicitly request JSON format and provide the expected structure

### Security Considerations

1. **API Key Management**: Never hardcode API keys; use environment variables
2. **Content Filtering**: Be aware of safety settings for user-facing applications
3. **Input Validation**: Sanitize user inputs before sending to the API

## Further Resources

- [Google Gemini API Documentation](https://ai.google.dev/docs)
- [Example Tutorial Script](./llm_service_tutorial.py)
- [LLM Service Source Code](../src/models/llm_service.py)
- [Gemini Configuration](../src/models/gemini_config.py)
