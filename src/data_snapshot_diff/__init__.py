"""Data Snapshot Diff core package."""

from .comparator import ComparisonResult, compare_snapshots
from .validation import DataValidationError

__all__ = ["ComparisonResult", "DataValidationError", "compare_snapshots"]
