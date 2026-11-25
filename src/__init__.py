"""
Study Abroad Analytics Engine

Processes and analyzes exported Study Abroad reports
independently of the institutional reporting system.
"""

__version__ = "1.0.0"

__author__ = "Study Abroad Analytics Project"

__description__ = (
    "A Python tool for organizing and analyzing "
    "study abroad data."
)

from .data_engine import StudyAbroadDataEngine
from .analytics_engine import StudyAbroadAnalyticsEngine

__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "StudyAbroadDataEngine",
    "StudyAbroadAnalyticsEngine",
]
