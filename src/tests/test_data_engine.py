"""
Tests for the Study Abroad Data Engine.

Run with:

    pytest tests/test_data_engine.py
"""

import pandas as pd
import pytest

from study_abroad_analytics import StudyAbroadDataEngine


# 1. Sample Data

@pytest.fixture
def sample_dataframe():

    return pd.DataFrame({
        "Student ID": [101, 102, 103, 104, 105],
        "College": [
            "Business",
            "Engineering",
            "Business",
            "Arts",
            "Engineering"
        ],
        "GPA": [3.5, 3.8, 3.2, 3.9, 3.6],
        "Country": [
            "France",
            "Spain",
            "Italy",
            "France",
            "Spain"
        ],
        "Program Year": [2023, 2024, 2024, 2025, 2025]
    })


@pytest.fixture
def engine(sample_dataframe):

    return StudyAbroadDataEngine(
        dataframe=sample_dataframe
    )


# 2. Initiatlization Tests

def test_requires_filepath_or_dataframe():

    with pytest.raises(ValueError):
        StudyAbroadDataEngine()


def test_load_dataframe(engine):

    assert engine.get_record_count() == 5


def test_rejects_invalid_dataframe():

    with pytest.raises(TypeError):
        StudyAbroadDataEngine(
            dataframe=[1, 2, 3]
        )


def test_preserves_original_data(engine):

    assert len(engine.original_data) == 5
    assert len(engine.data) == 5


# 3. File Loading Tests

def test_load_csv(tmp_path, sample_dataframe):

    filepath = tmp_path / "report.csv"

    sample_dataframe.to_csv(
        filepath,
        index=False
    )

    engine = StudyAbroadDataEngine(
        filepath=filepath
    )

    assert engine.get_record_count() == 5
    assert engine.filepath == filepath


def test_load_excel(tmp_path, sample_dataframe):

    filepath = tmp_path / "report.xlsx"

    sample_dataframe.to_excel(
        filepath,
        index=False
    )

    engine = StudyAbroadDataEngine(
        filepath=filepath
    )

    assert engine.get_record_count() == 5


def test_missing_file():

    with pytest.raises(FileNotFoundError):
        StudyAbroadDataEngine(
            filepath="missing_report.csv"
        )


def test_unsupported_file(tmp_path):

    filepath = tmp_path / "report.txt"

    filepath.write_text("sample data")

    with pytest.raises(ValueError):
        StudyAbroadDataEngine(
            filepath=filepath
        )


# 4. Data Inspection Tests

def test_inspect(engine):

    result = engine.inspect()

    assert result["records"] == 5
    assert "Student ID" in result["columns"]
    assert result["duplicates"] == 0
    assert "memory_mb" in result


def test_validate_existing_columns(engine):

    assert engine.validate_columns(
        ["College", "GPA"]
    )


def test_validate_missing_columns(engine):

    with pytest.raises(ValueError):
        engine.validate_columns(
            ["Unknown Column"]
        )


# 5. Transformation Tests

def test_normalize_columns(engine):

    engine.transform(
        normalize_columns=True
    )

    assert "student_id" in engine.data.columns
    assert "program_year" in engine.data.columns


def test_detect_duplicate_normalized_columns():

    df = pd.DataFrame(
        [[1, 2]],
        columns=["Program Country", "program_country"]
    )

    engine = StudyAbroadDataEngine(
        dataframe=df
    )

    with pytest.raises(ValueError):
        engine.transform(
            normalize_columns=True
        )


def test_strip_text(engine):

    df = pd.DataFrame({
        "College": [" Business ", " Engineering "]
    })

    engine = StudyAbroadDataEngine(
        dataframe=df
    )

    engine.transform()

    assert engine.data["College"].iloc[0] == "Business"


def test_convert_numeric(engine):

    df = pd.DataFrame({
        "GPA": ["3.5", "3.8", "invalid"]
    })

    engine = StudyAbroadDataEngine(
        dataframe=df
    )

    engine.transform(
        convert_numeric=["GPA"]
    )

    assert pd.api.types.is_numeric_dtype(
        engine.data["GPA"]
    )

    assert pd.isna(
        engine.data["GPA"].iloc[2]
    )


def test_convert_dates():

    df = pd.DataFrame({
        "Application Date": [
            "2024-01-15",
            "2024-02-20"
        ]
    })

    engine = StudyAbroadDataEngine(
        dataframe=df
    )

    engine.transform(
        convert_dates=["Application Date"]
    )

    assert pd.api.types.is_datetime64_any_dtype(
        engine.data["Application Date"]
    )


# 6. Filtering Tests

def test_filter_exact_value(engine):

    engine.filter(College="Business")

    assert engine.get_record_count() == 2


def test_filter_multiple_values(engine):

    engine.filter(
        Country=["France", "Spain"]
    )

    assert engine.get_record_count() == 4


def test_filter_numeric_range(engine):

    engine.transform(
        convert_numeric=["GPA"]
    )

    engine.filter(
        GPA={"min": 3.5, "max": 3.8}
    )

    assert engine.get_record_count() == 3


def test_filter_missing_values():

    df = pd.DataFrame({
        "College": ["Business", None, "Arts"]
    })

    engine = StudyAbroadDataEngine(
        dataframe=df
    )

    engine.filter(
        College={"isnull": True}
    )

    assert engine.get_record_count() == 1


def test_filter_nonmissing_values():

    df = pd.DataFrame({
        "College": ["Business", None, "Arts"]
    })

    engine = StudyAbroadDataEngine(
        dataframe=df
    )

    engine.filter(
        College={"isnull": False}
    )

    assert engine.get_record_count() == 2


def test_filter_none():

    df = pd.DataFrame({
        "College": ["Business", None, "Arts"]
    })

    engine = StudyAbroadDataEngine(
        dataframe=df
    )

    engine.filter(
        College=None
    )

    assert engine.get_record_count() == 1


def test_filter_chaining(engine):

    engine.filter(
        College="Business"
    ).filter(
        GPA={"min": 3.3}
    )

    assert engine.get_record_count() == 1


# 7. Search Tests

def test_search(engine):

    engine.search(
        column="Country",
        keyword="France"
    )

    assert engine.get_record_count() == 2


def test_search_case_insensitive(engine):

    engine.search(
        column="Country",
        keyword="france"
    )

    assert engine.get_record_count() == 2


# 8. Sorting Tests

def test_sort_ascending(engine):

    engine.sort(
        by="GPA"
    )

    assert engine.data["GPA"].is_monotonic_increasing


def test_sort_descending(engine):

    engine.sort(
        by="GPA",
        ascending=False
    )

    assert engine.data["GPA"].is_monotonic_decreasing


def test_sort_without_modifying_data(engine):

    original = engine.get_data()

    result = engine.sort(
        by="GPA",
        inplace=False
    )

    pd.testing.assert_frame_equal(
        engine.get_data(),
        original
    )

    assert result["GPA"].is_monotonic_increasing


# 9. Grouping Tests

def test_group_by(engine):

    result = engine.group_by(
        "College",
        aggregations={
            "students": ("Student ID", "nunique")
        }
    )

    assert "students" in result.columns
    assert len(result) == 3


def test_group_by_default(engine):

    result = engine.group_by("College")

    assert "records" in result.columns


# 10. Reset and Data Management Tests

def test_reset(engine):

    engine.filter(
        College="Business"
    )

    engine.reset()

    assert engine.get_record_count() == 5


def test_get_data_returns_copy(engine):

    result = engine.get_data()

    result["GPA"] = 0

    assert engine.data["GPA"].iloc[0] == 3.5


def test_original_data_is_preserved(engine):

    engine.filter(
        College="Business"
    )

    assert len(engine.get_original_data()) == 5


# 11. Metrics & History Tests

def test_metrics(engine):

    metrics = engine.get_metrics()

    assert metrics["original_records"] == 5
    assert metrics["original_columns"] == 5


def test_history(engine):

    engine.filter(
        College="Business"
    )

    history = engine.get_history()

    assert len(history) == 1
    assert history.iloc[0]["operation"] == "filter"


def test_method_chaining(engine):

    result = (
        engine
        .filter(College="Business")
        .sort("GPA")
        .reset()
    )

    assert result is engine
    assert engine.get_record_count() == 5
