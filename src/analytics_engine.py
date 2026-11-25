
"""
Study Abroad Analytics Engine

Analyzes Study Abroad participation, student demographics,
academic characteristics, and program trends.
"""

__version__ = "1.0.0"

import pandas as pd
from .data_engine import StudyAbroadDataEngine


class StudyAbroadAnalyticsEngine:

    def __init__(self, filepath=None, dataframe=None):

        if filepath is None and dataframe is None:
            raise ValueError("Provide a filepath or dataframe.")

        self.engine = StudyAbroadDataEngine(
            filepath=filepath,
            dataframe=dataframe
        )

        self.data = self.engine.get_data()
        self.metrics = {}
        self.history = []

    # 1. Data Preparation

    def refresh(self):
        self.data = self.engine.get_data()
        return self

    def validate_columns(self, columns):

        missing = [col for col in columns if col not in self.data.columns]

        if missing:
            raise ValueError(f"Missing columns: {missing}")

        return True

    def get_data(self):
        return self.data.copy(deep=True)

    def get_history(self):
        return pd.DataFrame(self.history)

    # 2. Reusable Analysis Method

    def group_analysis(self, group_column, include_applications=False):

        columns = [group_column, "user_id"]

        if include_applications:
            columns.append("application_id")

        self.validate_columns(columns)

        aggregations = {
            "students": ("user_id", "nunique")
        }

        if include_applications:
            aggregations["applications"] = (
                "application_id", "nunique"
            )

        return (
            self.data
            .groupby(group_column, dropna=False)
            .agg(**aggregations)
            .reset_index()
            .sort_values("students", ascending=False)
        )

    # 3. Participation Metrics

    def participation_summary(self):

        required = [
            "application_id", "user_id", "college",
            "program_country", "program_year",
            "application_status", "program_type",
            "program_category", "mode_of_participation"
        ]

        self.validate_columns(required)

        result = {
            "total_records": len(self.data),
            "total_applications": self.data["application_id"].nunique(),
            "unique_students": self.data["user_id"].nunique(),
            "unique_programs": (
                self.data["program_id"].nunique()
                if "program_id" in self.data.columns else None
            ),
            "countries": self.data["program_country"].nunique(),
            "academic_colleges": self.data["college"].nunique()
        }

        return pd.Series(result, name="Participation Summary")

    # 4. Student Demographics

    def participation_by_college(self):
        return self.group_analysis("college", True)

    def participation_by_major(self):
        return self.group_analysis("first_major", True)

    def participation_by_class_level(self):
        return self.group_analysis("outbound_class_level")

    # 5. Geographic Analysis

    def participation_by_country(self):
        return self.group_analysis("program_country", True)

    def participation_by_region(self):
        return self.group_analysis("program_region")

    # 6. Program Analysis

    def participation_by_program_type(self):
        return self.group_analysis("program_type")

    def participation_by_category(self):
        return self.group_analysis("program_category")

    def participation_by_mode(self):
        return self.group_analysis("mode_of_participation")

    # 7. Application Analysis

    def applications_by_status(self):

        self.validate_columns([
            "application_status",
            "application_id"
        ])

        return (
            self.data
            .groupby("application_status", dropna=False)
            .agg(applications=("application_id", "nunique"))
            .reset_index()
            .sort_values("applications", ascending=False)
        )

    # 8. Year-over-Year Analysis

    def participation_by_year(self):

        result = self.group_analysis("program_year", True)

        result["program_year"] = pd.to_numeric(
            result["program_year"], errors="coerce"
        )

        result = result.sort_values("program_year")

        result["student_change"] = result["students"].diff()

        result["student_growth_percent"] = (
            result["students"]
            .pct_change(fill_method=None)
            .mul(100)
            .round(2)
        )

        return result

    # 9. Academic Analysis

    def average_gpa_by_college(self):

        self.validate_columns(["college", "sdsu_gpa", "user_id"])

        return (
            self.data
            .groupby("college", dropna=False)
            .agg(
                average_gpa=("sdsu_gpa", "mean"),
                students=("user_id", "nunique")
            )
            .reset_index()
            .sort_values("average_gpa", ascending=False)
        )
