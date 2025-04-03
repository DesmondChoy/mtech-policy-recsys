"""
Configuration settings for Google Gemini API.

This module provides configuration settings and utilities for working with
the Google Gemini API, including environment variable loading and default
parameters for different use cases.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class GeminiConfig:
    """Configuration settings for Google Gemini API."""

    # API key from environment variable
    API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    # Default models
    DEFAULT_MODEL: str = "gemini-2.5-pro-exp-03-25"  # Updated default model

    # Default parameters for different use cases
    DEFAULT_PARAMETERS: Dict[str, Any] = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 60000,  # Increased default max tokens
    }

    # Parameters for more deterministic responses (e.g., for structured data extraction)
    DETERMINISTIC_PARAMETERS: Dict[str, Any] = {
        "temperature": 0.2,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 2048,
    }

    # Parameters for more creative responses (e.g., for CS agent)
    CREATIVE_PARAMETERS: Dict[str, Any] = {
        "temperature": 1.0,
        "top_p": 0.99,
        "top_k": 40,
        "max_output_tokens": 4096,
    }

    # Safety settings
    SAFETY_SETTINGS: Dict[str, str] = {
        "harassment": "BLOCK_NONE",
        "hate_speech": "BLOCK_NONE",
        "sexually_explicit": "BLOCK_NONE",
        "dangerous_content": "BLOCK_NONE",
    }

    @classmethod
    def get_api_key(cls) -> str:
        """
        Get the API key from environment variables.

        Returns:
            str: The API key.

        Raises:
            ValueError: If the API key is not set.
        """
        if not cls.API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is not set. "
                "Please set it in your .env file or environment variables."
            )
        return cls.API_KEY

    @classmethod
    def get_parameters(cls, parameter_set: str = "default") -> Dict[str, Any]:
        """
        Get parameters for a specific use case.

        Args:
            parameter_set: The parameter set to use. One of "default", "deterministic", or "creative".

        Returns:
            Dict[str, Any]: The parameters.
        """
        parameter_sets = {
            "default": cls.DEFAULT_PARAMETERS,
            "deterministic": cls.DETERMINISTIC_PARAMETERS,
            "creative": cls.CREATIVE_PARAMETERS,
        }

        return parameter_sets.get(parameter_set.lower(), cls.DEFAULT_PARAMETERS)
