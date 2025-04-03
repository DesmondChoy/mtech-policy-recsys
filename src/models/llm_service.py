"""
LLM Service for Google Gemini.

This module provides a service for interacting with Google Gemini API,
offering methods for content generation, embeddings, and streaming responses.
"""

import time
import logging
from typing import Dict, List, Any, Optional, Union, Generator, Callable

import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from google.generativeai.types.safety_types import HarmCategory, HarmBlockThreshold
from google.generativeai.types.generation_types import GenerateContentResponse

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
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the Google Gemini client."""
        genai.configure(api_key=self.api_key)
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
    ) -> GenerateContentResponse:
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

        # Convert parameters to GenerationConfig
        generation_config = GenerationConfig(**parameters)

        # Convert safety settings to SafetySetting objects
        safety_settings_list = [
            {
                "category": getattr(HarmCategory, f"HARM_CATEGORY_{category.upper()}"),
                "threshold": getattr(HarmBlockThreshold, f"{threshold.upper()}"),
            }
            for category, threshold in safety_settings.items()
        ]

        # Get the model
        gemini_model = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config,
            safety_settings=safety_settings_list,
        )

        # Determine the content to send
        content_to_send = contents if contents is not None else prompt

        # Try to generate content with retries
        for attempt in range(retry_count):
            try:
                response = gemini_model.generate_content(content_to_send)
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

    def generate_structured_content(
        self,
        prompt: str,
        model: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        safety_settings: Optional[Dict[str, str]] = None,
        retry_count: int = 3,
        retry_delay: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Generate structured content (JSON) using Google Gemini.

        This method is optimized for generating structured data by using more deterministic
        parameters and adding instructions to format the response as JSON.

        Args:
            prompt: The prompt to generate content from.
            model: The model to use. If not provided, the default model will be used.
            parameters: The parameters to use. If not provided, deterministic parameters will be used.
            safety_settings: The safety settings to use. If not provided, the default safety settings will be used.
            retry_count: The number of times to retry if the API call fails.
            retry_delay: The delay between retries in seconds.

        Returns:
            The generated content as a dictionary.

        Raises:
            Exception: If the API call fails after all retries or if the response cannot be parsed as JSON.
        """
        # Use deterministic parameters by default for structured content
        parameters = parameters or GeminiConfig.get_parameters("deterministic")

        # Add instructions to format the response as JSON
        structured_prompt = f"{prompt}\n\nProvide your response as valid JSON."

        response = self.generate_content(
            prompt=structured_prompt,
            model=model,
            parameters=parameters,
            safety_settings=safety_settings,
            retry_count=retry_count,
            retry_delay=retry_delay,
        )

        try:
            # The response.text contains the generated text
            import json

            return json.loads(response.text)
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

        # Convert parameters to GenerationConfig
        generation_config = GenerationConfig(**parameters)

        # Convert safety settings to SafetySetting objects
        safety_settings_list = [
            {
                "category": getattr(HarmCategory, f"HARM_CATEGORY_{category.upper()}"),
                "threshold": getattr(HarmBlockThreshold, f"{threshold.upper()}"),
            }
            for category, threshold in safety_settings.items()
        ]

        # Get the model
        gemini_model = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config,
            safety_settings=safety_settings_list,
        )

        try:
            response = gemini_model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
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
    ) -> List[GenerateContentResponse]:
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
    ) -> GenerateContentResponse:
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
