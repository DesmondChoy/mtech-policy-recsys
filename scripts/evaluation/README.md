# Transcript Evaluation

This directory contains scripts and modules for evaluating conversation transcripts to determine if a customer service agent successfully gathered all required travel insurance coverage information from a customer.

## Directory Structure

```
scripts/evaluation/
├── README.md                         # This file
├── eval_transcript_main.py           # Main entry point for transcript evaluation
├── prompts/                          # Prompt templates
│   ├── __init__.py
│   └── eval_transcript_prompts.py    # Prompt construction and formatting
├── processors/                       # Data processors
│   ├── __init__.py
│   ├── eval_transcript_parser.py     # Transcript parsing
│   └── eval_transcript_results.py    # Results formatting and saving
├── evaluators/                       # LLM-based evaluators
│   ├── __init__.py
│   └── eval_transcript_gemini.py     # Google Gemini evaluator
└── utils/                            # Utility functions
    ├── __init__.py
    └── eval_transcript_utils.py      # Helper functions
```

## Usage

### Evaluate a Single Transcript

```bash
python scripts/evaluation/eval_transcript_main.py --transcript data/transcripts/synthetic/transcript_01.txt
```

### Evaluate All Transcripts in a Directory

```bash
python scripts/evaluation/eval_transcript_main.py --directory data/transcripts/synthetic/
```

### Specify Output Format and Location

```bash
python scripts/evaluation/eval_transcript_main.py --transcript transcript_01.txt --output-dir custom/output/path --format json,txt
```

## Module Descriptions

### `eval_transcript_main.py`

The main entry point for transcript evaluation. It orchestrates the evaluation process by:
1. Parsing command-line arguments
2. Loading environment variables
3. Processing transcripts (single or directory)
4. Generating evaluations using Google Gemini
5. Saving results in specified formats

### `prompts/eval_transcript_prompts.py`

Contains functions for constructing and formatting prompts for LLM-based evaluation:
- `format_transcript_for_prompt()`: Formats a transcript for inclusion in a prompt
- `format_coverage_requirements_for_prompt()`: Formats coverage requirements for inclusion in a prompt
- `construct_evaluation_prompt()`: Constructs a complete evaluation prompt

### `processors/eval_transcript_parser.py`

Contains functions for parsing and processing transcripts:
- `parse_transcript()`: Parses a transcript file into a list of speaker-dialogue pairs
- `validate_transcript()`: Validates a parsed transcript
- `find_transcript_files()`: Finds all transcript files in a directory

### `processors/eval_transcript_results.py`

Contains functions for formatting and saving evaluation results:
- `format_evaluation_results()`: Formats evaluation results for display
- `save_evaluation_results()`: Saves evaluation results to specified formats
- `create_summary_csv()`: Creates a CSV summary of multiple transcript evaluations
- `save_prompt_for_manual_evaluation()`: Saves a prompt for manual evaluation

### `evaluators/eval_transcript_gemini.py`

Contains functions for evaluating transcripts using Google Gemini:
- `check_gemini_availability()`: Checks if the Google Gemini API is available
- `initialize_gemini_client()`: Initializes the Google Gemini client
- `generate_gemini_evaluation()`: Generates an evaluation using Google Gemini with schema-based JSON response

Also includes Pydantic models for structured evaluation responses:
- `CoverageEvaluation`: Model for individual coverage evaluations
- `EvaluationSummary`: Model for the evaluation summary
- `TranscriptEvaluation`: Top-level model for the complete evaluation

### `utils/eval_transcript_utils.py`

Contains utility functions:
- `ensure_output_directory()`: Ensures that the output directory exists
- `get_transcript_name()`: Gets the transcript name from the file path
- `setup_logging()`: Sets up logging configuration
- `load_environment_variables()`: Loads environment variables from .env file
- `print_evaluation_instructions()`: Prints instructions for manual evaluation

## Schema-Based JSON Responses

The evaluation system uses a schema-based approach for generating structured JSON responses from the Google Gemini API. This approach has several advantages:

1. **Consistent Structure**: By defining Pydantic models for the expected response structure, we ensure that the LLM generates responses with a consistent format.

2. **Type Validation**: The schema enforces type validation, ensuring that fields like `total_requirements` are numbers and not strings.

3. **Error Reduction**: The schema-based approach significantly reduces parsing errors that can occur when relying on text-based instructions for JSON formatting.

4. **Direct Object Access**: The response can be accessed as a Python object with proper typing, making it easier to work with in code.

The schema is defined in `evaluators/eval_transcript_gemini.py` using Pydantic models:

```python
class CoverageEvaluation(BaseModel):
    coverage_type: str
    name: str
    result: str
    justification: str
    customer_quote: str
    agent_performance: str
    agent_performance_justification: str
    agent_quote: str

class EvaluationSummary(BaseModel):
    total_requirements: int
    requirements_met: int
    overall_assessment: str

class TranscriptEvaluation(BaseModel):
    evaluations: List[CoverageEvaluation]
    summary: EvaluationSummary
```

When calling the Gemini API, we specify this schema using the `response_schema` parameter:

```python
response = client.models.generate_content(
    model=model,
    contents=[prompt],
    config={
        "temperature": 0.2,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 2048,
        "response_mime_type": "application/json",
        "response_schema": TranscriptEvaluation,
    },
)
```
