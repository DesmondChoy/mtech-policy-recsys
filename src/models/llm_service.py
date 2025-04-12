"""
LLM Service for Google Gemini.

This module provides a service for interacting with Google Gemini API,
offering methods for content generation, embeddings, and streaming responses.
"""

import time
import logging
from typing import Dict, List, Any, Optional, Union, Generator, Callable

from google import genai
from google.genai import types

from src.models.gemini_config import GeminiConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Google Gemini API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM service.

        Args:
            api_key: The API key to use. If not provided, it will be loaded from environment variables.
        """
        self.api_key = api_key or GeminiConfig.get_api_key()
        self.GeminiConfig = (
            GeminiConfig  # Make GeminiConfig accessible as an instance attribute
        )
        self.client: Optional[genai.Client] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the Google Gemini client."""
        self.client = genai.Client(api_key=self.api_key)
        logger.info("Google Gemini client initialized")

    def generate_content(
        self,
        prompt: Optional[str] = None,  # Make prompt optional
        contents: Optional[List[Union[str, Dict]]] = None,  # Add contents parameter
        model: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        safety_settings: Optional[Dict[str, str]] = None,
        retry_count: int = 3,
        retry_delay: float = 1.0,
        max_output_tokens: Optional[int] = None,
    ) -> types.GenerateContentResponse:
        """
        Generate content using Google Gemini.

        Can accept either a simple text prompt or a list of contents for multi-modal input.

        Args:
            prompt: The text prompt to generate content from (used if contents is None).
            contents: A list of content parts (e.g., text, PDF data) for multi-modal input.
                      Example: [{"mime_type": "application/pdf", "data": pdf_bytes}, "prompt text"]
            model: The model to use. If not provided, the default model will be used.
            parameters: The parameters to use. If not provided, the default parameters will be used.
            safety_settings: The safety settings to use. If not provided, the default safety settings will be used.
            retry_count: The number of times to retry if the API call fails.
            retry_delay: The delay between retries in seconds.
            max_output_tokens: Optional maximum number of tokens to generate.

        Returns:
            The generated content response.

        Raises:
            ValueError: If neither prompt nor contents is provided.
            Exception: If the API call fails after all retries.
        """
        if prompt is None and contents is None:
            raise ValueError("Either 'prompt' or 'contents' must be provided.")
        if prompt is not None and contents is not None:
            logger.warning(
                "Both 'prompt' and 'contents' provided. 'contents' will be used."
            )

        model = model or self.GeminiConfig.DEFAULT_MODEL  # Use instance attribute
        parameters = (
            parameters or self.GeminiConfig.get_parameters()
        )  # Use instance attribute
        safety_settings = (
            safety_settings or self.GeminiConfig.SAFETY_SETTINGS
        )  # Use instance attribute

        # Add max_output_tokens to parameters if provided
        if max_output_tokens is not None:
            parameters["max_output_tokens"] = max_output_tokens

        # Convert safety settings to SafetySetting objects
        safety_settings_objects = [
            types.SafetySetting(
                category=getattr(
                    types.HarmCategory, f"HARM_CATEGORY_{category.upper()}", category
                ),
                threshold=getattr(
                    types.HarmBlockThreshold, f"{threshold.upper()}", threshold
                ),
            )
            for category, threshold in safety_settings.items()
        ]

        # Create configuration object by unpacking parameters and adding safety settings
        config_payload = types.GenerateContentConfig(
            **parameters,  # Unpack parameters dictionary directly
            safety_settings=safety_settings_objects,
        )

        # Determine the input content and ensure it's a list
        input_content = contents if contents is not None else [prompt]

        # Convert input content to a list of types.Part objects
        content_parts = []
        for item in input_content:
            if isinstance(item, str):
                content_parts.append(types.Part(text=item))
            elif isinstance(item, dict) and "mime_type" in item and "data" in item:
                # Create Blob for inline data like PDF
                inline_data = types.Blob(mime_type=item["mime_type"], data=item["data"])
                content_parts.append(types.Part(inline_data=inline_data))
            else:
                logger.warning(
                    f"Unsupported content type in 'contents' list: {type(item)}. Skipping."
                )
                # Or raise ValueError(f"Unsupported content type: {type(item)}")

        # Try to generate content with retries using the processed content_parts
        for attempt in range(retry_count):
            try:
                if self.client is None:
                    raise RuntimeError("Gemini client not initialized.")
                response = self.client.models.generate_content(
                    model=model,
                    contents=content_parts,  # Pass the list of Part objects
                    config=config_payload,
                )
                return response
            except Exception as e:
                if attempt < retry_count - 1:
                    logger.warning(
                        f"API call failed (attempt {attempt + 1}/{retry_count}): {str(e)}. Retrying in {retry_delay} seconds..."
                    )
                    time.sleep(retry_delay)
                    # Increase delay for next retry (exponential backoff)
                    retry_delay *= 2
                else:
                    logger.error(
                        f"API call failed after {retry_count} attempts: {str(e)}"
                    )
                    raise

    def _fix_json_format(self, json_str: str) -> str:
        """
        Fix common JSON formatting issues in LLM-generated JSON.

        Args:
            json_str (str): The JSON string to fix

        Returns:
            str: The fixed JSON string
        """
        import re

        # Add missing commas between key-value pairs
        # Pattern: "key": value\n  "key"
        fixed_json = re.sub(
            r'("[^"]+"\s*:\s*[^,{\[\n]+)(\s*^\s*")',
            r"\1,\2",
            json_str,
            flags=re.MULTILINE,
        )

        # Add missing commas between objects in arrays
        # Pattern: }\n  {
        fixed_json = re.sub(r"(})\s*^\s*({)", r"\1,\2", fixed_json, flags=re.MULTILINE)

        logger.debug(f"Original JSON:\n{json_str}")
        logger.debug(f"Fixed JSON:\n{fixed_json}")

        return fixed_json

    def generate_structured_content(
        self,
        prompt: Optional[str] = None,  # Make prompt optional
        contents: Optional[List[Union[str, Dict]]] = None,  # Add contents parameter
        model: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        safety_settings: Optional[Dict[str, str]] = None,
        retry_count: int = 3,
        retry_delay: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Generate structured content (JSON) using Google Gemini, supporting multi-modal input.

        This method is optimized for generating structured data by using more deterministic
        parameters and adding instructions to format the response as JSON. It accepts
        either a simple text prompt or a list of contents for multi-modal input.

        Args:
            prompt: The text prompt (used if contents is None).
            contents: A list of content parts (e.g., text, PDF data) for multi-modal input.
                      If provided, this overrides the prompt argument.
            model: The model to use. If not provided, the default model will be used.
            parameters: The parameters to use. If not provided, deterministic parameters will be used.
            safety_settings: The safety settings to use. If not provided, the default safety settings will be used.
            retry_count: The number of times to retry if the API call fails.
            retry_delay: The delay between retries in seconds.

        Returns:
            The generated content as a dictionary.

        Raises:
            ValueError: If neither prompt nor contents is provided.
            Exception: If the API call fails after all retries or if the response cannot be parsed as JSON.
        """
        if prompt is None and contents is None:
            raise ValueError("Either 'prompt' or 'contents' must be provided.")
        if prompt is not None and contents is not None:
            logger.warning(
                "Both 'prompt' and 'contents' provided for generate_structured_content. 'contents' will be used."
            )

        # Use deterministic parameters by default for structured content
        parameters = parameters or self.GeminiConfig.get_parameters(
            "deterministic"
        )  # Use instance attribute

        # Determine the input content list
        input_contents = contents if contents is not None else [prompt]

        # Find the last text part in the list to append JSON instructions
        last_text_index = -1
        for i in range(len(input_contents) - 1, -1, -1):
            if isinstance(input_contents[i], str):
                last_text_index = i
                break

        # Append JSON instructions to the last text part
        if last_text_index != -1:
            input_contents[last_text_index] = (
                f"{input_contents[last_text_index]}\n\nProvide your response as valid JSON."
            )
        else:
            # If no text part found (e.g., only file input), add instructions as a new text part
            input_contents.append("\n\nProvide your response as valid JSON.")

        # Call generate_content with the prepared contents list
        response = self.generate_content(
            contents=input_contents,  # Pass the list
            model=model,
            parameters=parameters,  # Pass potentially modified parameters
            safety_settings=safety_settings,
            retry_count=retry_count,
            retry_delay=retry_delay,
        )

        try:
            # The response.text contains the generated text
            import json

            # Get the raw text
            raw_text = response.text

            # Check if the response is wrapped in a markdown code block
            if "```json" in raw_text or "```" in raw_text:
                logger.info(
                    "Detected markdown code block in response. Extracting JSON content."
                )
                # Remove markdown code block indicators
                cleaned_text = (
                    raw_text.replace("```json", "").replace("```", "").strip()
                )
                raw_text = cleaned_text

            # Try to parse the JSON directly
            try:
                return json.loads(raw_text)
            except json.JSONDecodeError:
                # If direct parsing fails, try to fix common formatting issues
                logger.info(
                    "Initial JSON parsing failed. Attempting to fix JSON format."
                )
                fixed_json = self._fix_json_format(raw_text)
                return json.loads(fixed_json)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response as JSON: {str(e)}")
            logger.error(f"Response text: {response.text}")
            raise ValueError(f"Failed to parse response as JSON: {str(e)}")

    def stream_content(
        self,
        prompt: str,
        model: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        safety_settings: Optional[Dict[str, str]] = None,
    ) -> Generator[str, None, None]:
        """
        Stream content using Google Gemini.

        Args:
            prompt: The prompt to generate content from.
            model: The model to use. If not provided, the default model will be used.
            parameters: The parameters to use. If not provided, the default parameters will be used.
            safety_settings: The safety settings to use. If not provided, the default safety settings will be used.

        Yields:
            Chunks of generated content.

        Raises:
            Exception: If the API call fails.
        """
        model = model or GeminiConfig.DEFAULT_MODEL
        parameters = parameters or GeminiConfig.get_parameters()
        safety_settings = safety_settings or GeminiConfig.SAFETY_SETTINGS

        # Convert safety settings to SafetySetting objects
        safety_settings_objects = [
            types.SafetySetting(
                category=getattr(
                    types.HarmCategory, f"HARM_CATEGORY_{category.upper()}", category
                ),
                threshold=getattr(
                    types.HarmBlockThreshold, f"{threshold.upper()}", threshold
                ),
            )
            for category, threshold in safety_settings.items()
        ]

        # Create configuration object by unpacking parameters and adding safety settings
        config_payload = types.GenerateContentConfig(
            **parameters,  # Unpack parameters dictionary directly
            safety_settings=safety_settings_objects,
        )

        try:
            if self.client is None:
                raise RuntimeError("Gemini client not initialized.")
            stream = self.client.models.generate_content_stream(
                model=model, contents=prompt, config=config_payload
            )
            for chunk in stream:
                if hasattr(chunk, "text") and chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Streaming API call failed: {str(e)}")
            raise

    def batch_generate(
        self,
        prompts: List[str],
        model: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        safety_settings: Optional[Dict[str, str]] = None,
        retry_count: int = 3,
        retry_delay: float = 1.0,
    ) -> List[types.GenerateContentResponse]:
        """
        Generate content for multiple prompts.

        Args:
            prompts: The prompts to generate content from.
            model: The model to use. If not provided, the default model will be used.
            parameters: The parameters to use. If not provided, the default parameters will be used.
            safety_settings: The safety settings to use. If not provided, the default safety settings will be used.
            retry_count: The number of times to retry if an API call fails.
            retry_delay: The delay between retries in seconds.

        Returns:
            A list of generated content responses.

        Raises:
            Exception: If any API call fails after all retries.
        """
        results = []
        for prompt in prompts:
            response = self.generate_content(
                prompt=prompt,
                model=model,
                parameters=parameters,
                safety_settings=safety_settings,
                retry_count=retry_count,
                retry_delay=retry_delay,
            )
            results.append(response)
        return results

    def generate_with_retry(
        self,
        prompt: str,
        model: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        safety_settings: Optional[Dict[str, str]] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        validation_func: Optional[Callable[[str], bool]] = None,
    ) -> types.GenerateContentResponse:
        """
        Generate content with retry logic for validation failures.

        This method will retry the generation if the validation function returns False.

        Args:
            prompt: The prompt to generate content from.
            model: The model to use. If not provided, the default model will be used.
            parameters: The parameters to use. If not provided, the default parameters will be used.
            safety_settings: The safety settings to use. If not provided, the default safety settings will be used.
            max_retries: The maximum number of retries if validation fails.
            retry_delay: The delay between retries in seconds.
            validation_func: A function that takes the generated text and returns True if it's valid, False otherwise.

        Returns:
            The generated content response.

        Raises:
            ValueError: If validation fails after all retries.
        """
        for attempt in range(max_retries):
            response = self.generate_content(
                prompt=prompt,
                model=model,
                parameters=parameters,
                safety_settings=safety_settings,
            )

            # If no validation function or validation passes, return the response
            if validation_func is None or validation_func(response.text):
                return response

            # If validation fails and we have retries left, try again
            if attempt < max_retries - 1:
                logger.warning(
                    f"Validation failed (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay} seconds..."
                )
                time.sleep(retry_delay)
                # Increase delay for next retry (exponential backoff)
                retry_delay *= 2

        # If we get here, validation failed after all retries
        raise ValueError(f"Validation failed after {max_retries} attempts")
