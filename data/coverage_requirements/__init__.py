"""
Coverage Requirements Package

This package contains definitions of standard coverage requirements for travel insurance policies.
"""

from .coverage_requirements import (
    coverage_requirements,
    get_coverage_requirements,
    get_coverage_types,
    get_coverage,
)

__all__ = [
    "coverage_requirements",
    "get_coverage_requirements",
    "get_coverage_types",
    "get_coverage",
]
