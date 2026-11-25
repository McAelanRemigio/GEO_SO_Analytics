"""
Tests for the Study Abroad Analytics Engine.

Run with:

    pytest tests/test_analytics_engine.py
"""

import pandas as pd
import pytest

from study_abroad_analytics import StudyAbroadAnalyticsEngine


# 1. Sample Study Abroad Data

@pytest.fixture
def sample_dataframe():

    return pd.DataFrame({

        "application_id": [
            1001, 1002, 1003, 1004, 1005, 1006
        ],

        "user_id": [
            101, 102, 101, 103, 104, 105
        ],

        "program_id": [
            501, 502, 503, 501, 504, 505
        ],

        "college": [
            "Business",
            "Engineering",
            "Business",
            "Arts",
            "Engineering",
            "Business"
        ],

        "first_major": [
            "Finance",
            "Engineering",
            "Marketing",
            "Art",
            "Engineering",
            "Finance"
        ],

        "outbound_class_level": [
            "Junior",
            "Senior",
            "Junior",
            "Sophomore",
            "Senior",
            "Junior"
        ],

        "program_country": [
            "France",
            "Spain",
            "Italy",
            "France",
            "Spain",
            "Italy"
        ],

        "program_region": [
            "Europe",
            "Europe",
            "Europe",
            "Europe",
            "Europe",
            "Europe"
        ],

        "program_year": [
            2022,
            2023,
            2023,
            2025,
            2025,
            2025
        ],

        "application_status": [
            "Approved",
            "Approved",
            "Pending",
            "Approved",
            "Withdrawn",
            "Approved"
        ],

        "program_type": [
            "Exchange",
            "Faculty-Led",
            "Exchange",
            "Faculty-Led",
            "Exchange",
            "Faculty-Led"
        ],

        "program_category": [
            "Semester",
            "Short-Term",
            "Semester",
            "Short-Term",
            "Semester",
            "Short-Term"
        ],

        "mode_of_participation": [
            "In-Person",
            "In-Person",
            "In-Person",
            "In-Person",
            "In-Person",
            "In-Person"
        ],

        "sdsu_gpa": [
            3.5,
            3.8,
            3.3,
            3.9,
            3.6,
            3.4
        ]
    })


@pytest.fixture
def analytics(sample_dataframe):

    return StudyAbroadAnalyticsEngine(
        dataframe=sample_dataframe
    )


# 2. Initialization Tests

def test_requires_filepath_or_dataframe():

    with pytest.raises(ValueError):
        StudyAbroadAnalyticsEngine()


def test_load_dataframe(analytics):

    assert analytics.get_record_count() == 6


def test_get_data_returns_copy(analytics):

    result = analytics.get_data()

    result["sdsu_gpa"] = 0

    assert analytics.data["sdsu_gpa"].iloc[0] == 3.5


# 3. Column Validation Tests

def test_validate_existing_columns(analytics):

    assert analytics.validate_columns([
        "user_id",
        "college",
        "program_country"
    ])


def test_validate_missing_columns(analytics):

    with pytest.raises(ValueError):
        analytics.validate_columns([
            "unknown_column"
        ])


# 4. Participation Summary Tests

def test_participation_summary(analytics):

    result = analytics.participation_summary()

    assert result["total_records"] == 6

    assert result["total_applications"] == 6

    assert result["unique_students"] == 5

    assert result["unique_programs"] == 5

    assert result["countries"] == 3

    assert result["academic_colleges"] == 3


def test_participation_summary_without_program_id(
    sample_dataframe
):

    df = sample_dataframe.drop(
        columns=["program_id"]
    )

    analytics = StudyAbroadAnalyticsEngine(
        dataframe=df
    )

    result = analytics.participation_summary()

    assert result["unique_programs"] is None


# 5. Reusable Group Analysis Tests

def test_group_analysis_by_college(analytics):

    result = analytics.group_analysis(
        "college"
    )

    assert "college" in result.columns

    assert "students" in result.columns

    assert result["students"].sum() == 5


def test_group_analysis_with_applications(analytics):

    result = analytics.group_analysis(
        "college",
        include_applications=True
    )

    assert "applications" in result.columns

    assert result["applications"].sum() == 6


# 6. Demographic Analysis Tests

def test_participation_by_college(analytics):

    result = analytics.participation_by_college()

    assert "college" in result.columns

    assert "students" in result.columns

    assert "applications" in result.columns

    business = result[
        result["college"] == "Business"
    ]

    assert business.iloc[0]["students"] == 1


def test_participation_by_major(analytics):

    result = analytics.participation_by_major()

    assert "first_major" in result.columns

    assert "students" in result.columns


def test_participation_by_class_level(analytics):

    result = analytics.participation_by_class_level()

    assert "outbound_class_level" in result.columns


# 7. Geographic Analysis Tests

def test_participation_by_country(analytics):

    result = analytics.participation_by_country()

    assert len(result) == 3

    assert "program_country" in result.columns

    assert "students" in result.columns

    assert "applications" in result.columns


def test_participation_by_region(analytics):

    result = analytics.participation_by_region()

    assert len(result) == 1

    assert result.iloc[0]["students"] == 5


# 8. Program Analysis Tests

def test_participation_by_program_type(analytics):

    result = analytics.participation_by_program_type()

    assert "program_type" in result.columns

    assert len(result) == 2


def test_participation_by_category(analytics):

    result = analytics.participation_by_category()

    assert "program_category" in result.columns


def test_participation_by_mode(analytics):

    result = analytics.participation_by_mode()

    assert len(result) == 1

    assert result.iloc[0]["students"] == 5


# 9. Application Analysis Tests

def test_applications_by_status(analytics):

    result = analytics.applications_by_status()

    assert "application_status" in result.columns

    assert "applications" in result.columns

    assert result["applications"].sum() == 6

    approved = result[
        result["application_status"] == "Approved"
    ]

    assert approved.iloc[0]["applications"] == 4


# 10. YoY Analysis Tests

def test_participation_by_year(analytics):

    result = analytics.participation_by_year()

    assert "program_year" in result.columns

    assert "students" in result.columns

    assert "student_change" in result.columns

    assert "student_growth_percent" in result.columns

    assert result["program_year"].tolist() == [
        2022, 2023, 2025
    ]


def test_year_over_year_growth(analytics):

    result = analytics.participation_by_year()

    year_2023 = result[
        result["program_year"] == 2023
    ].iloc[0]

    assert year_2023["students"] == 2

    assert year_2023["student_change"] == 1

    assert year_2023["student_growth_percent"] == 100.0


def test_missing_year_is_not_treated_as_consecutive(
    analytics
):

    result = analytics.participation_by_year()

    year_2025 = result[
        result["program_year"] == 2025
    ].iloc[0]

    assert pd.isna(year_2025["student_change"])

    assert pd.isna(year_2025["student_growth_percent"])


# 11. Academic Analysis Tests

def test_average_gpa_by_college(analytics):

    result = analytics.average_gpa_by_college()

    assert "average_gpa" in result.columns

    assert "students" in result.columns

    assert len(result) == 3


def test_average_gpa_calculation(analytics):

    result = analytics.average_gpa_by_college()

    business = result[
        result["college"] == "Business"
    ].iloc[0]

    expected_gpa = (3.5 + 3.3 + 3.4) / 3

    assert business["average_gpa"] == pytest.approx(
        expected_gpa
    )

    assert business["students"] == 1


def test_gpa_text_conversion(sample_dataframe):

    df = sample_dataframe.copy()

    df["sdsu_gpa"] = df["sdsu_gpa"].astype(str)

    analytics = StudyAbroadAnalyticsEngine(
        dataframe=df
    )

    result = analytics.average_gpa_by_college()

    assert pd.api.types.is_numeric_dtype(
        result["average_gpa"]
    )


# 12. Engine Synchronization Tests

def test_filter_refreshes_analytics_engine(analytics):

    analytics.filter(
        program_year=2025
    )

    assert analytics.get_record_count() == 3

    assert len(analytics.engine.data) == 3


def test_transform_refreshes_analytics_engine(
    analytics
):

    analytics.transform(
        convert_numeric=["sdsu_gpa"]
    )

    assert analytics.data["sdsu_gpa"].dtype.kind in "fi"


def test_reset_restores_original_dataset(analytics):

    analytics.filter(
        college="Business"
    )

    analytics.reset()

    assert analytics.get_record_count() == 6


def test_method_chaining(analytics):

    result = (
        analytics
        .filter(program_year=2025)
        .sort("sdsu_gpa")
    )

    assert result is analytics

    assert analytics.get_record_count() == 3


# 13. Metrics & History Tests

def test_get_metrics(analytics):

    result = analytics.get_metrics()

    assert result["original_records"] == 6


def test_get_history(analytics):

    analytics.filter(
        college="Business"
    )

    history = analytics.get_history()

    assert len(history) == 1

    assert history.iloc[0]["operation"] == "filter"
