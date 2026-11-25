"""
Study Abroad Analytics Engine

Analyzes Study Abroad participation, student demographics,
academic characteristics, and program trends.
"""

import pandas as pd

from .data_engine import StudyAbroadDataEngine


class StudyAbroadAnalyticsEngine:

    def __init__(self, filepath=None, dataframe=None):

        if filepath is None and dataframe is None:
            raise ValueError(
                "Provide a filepath or dataframe."
            )

        self.engine = StudyAbroadDataEngine(
            filepath=filepath,
            dataframe=dataframe
        )

        self.data = self.engine.get_data()

    # 1. Data Preparation & Management

    def refresh(self):

        self.data = self.engine.get_data()

        return self

    def get_data(self):

        return self.data.copy(deep=True)

    def validate_columns(self, columns):

        missing = [
            col for col in columns
            if col not in self.data.columns
        ]

        if missing:
            raise ValueError(
                f"Missing columns: {missing}"
            )

        return True

    # Wrapper methods keep both engines synchronized

    def transform(self, **kwargs):

        self.engine.transform(**kwargs)

        return self.refresh()

    def filter(self, **conditions):

        self.engine.filter(**conditions)

        return self.refresh()

    def search(self, column, keyword, **kwargs):

        self.engine.search(
            column,
            keyword,
            **kwargs
        )

        return self.refresh()

    def sort(self, by, **kwargs):

        self.engine.sort(
            by,
            **kwargs
        )

        return self.refresh()

    def reset(self):

        self.engine.reset()

        return self.refresh()

    # 2. Metrics & History

    def get_metrics(self):

        return self.engine.get_metrics()

    def get_history(self):

        return self.engine.get_history()

    def get_record_count(self):

        return len(self.data)

    # 3. Reusable Analysis Method

    def group_analysis(
        self,
        group_column,
        include_applications=False
    ):

        columns = [
            group_column,
            "user_id"
        ]

        if include_applications:
            columns.append("application_id")

        self.validate_columns(columns)

        aggregations = {
            "students": ("user_id", "nunique")
        }

        if include_applications:

            aggregations["applications"] = (
                "application_id",
                "nunique"
            )

        return (
            self.data
            .groupby(
                group_column,
                dropna=False
            )
            .agg(**aggregations)
            .reset_index()
            .sort_values(
                "students",
                ascending=False
            )
        )

    # 4. Participation Metrics

    def participation_summary(self):

        required = [
            "application_id",
            "user_id",
            "college",
            "program_country",
            "program_year",
            "application_status",
            "program_type",
            "program_category",
            "mode_of_participation"
        ]

        self.validate_columns(required)

        result = {

            "total_records": len(self.data),

            "total_applications": (
                self.data["application_id"].nunique()
            ),

            "unique_students": (
                self.data["user_id"].nunique()
            ),

            "unique_programs": (
                self.data["program_id"].nunique()
                if "program_id" in self.data.columns
                else None
            ),

            "countries": (
                self.data["program_country"].nunique()
            ),

            "academic_colleges": (
                self.data["college"].nunique()
            )
        }

        return pd.Series(
            result,
            name="Participation Summary"
        )

    # 5. Student Demographics

    def participation_by_college(self):

        return self.group_analysis(
            "college",
            include_applications=True
        )

    def participation_by_major(self):

        return self.group_analysis(
            "first_major",
            include_applications=True
        )

    def participation_by_class_level(self):

        return self.group_analysis(
            "outbound_class_level"
        )

    # 6. Geographic Analysis

    def participation_by_country(self):

        return self.group_analysis(
            "program_country",
            include_applications=True
        )

    def participation_by_region(self):

        return self.group_analysis(
            "program_region"
        )

    # 7. Program Analysis

    def participation_by_program_type(self):

        return self.group_analysis(
            "program_type"
        )

    def participation_by_category(self):

        return self.group_analysis(
            "program_category"
        )

    def participation_by_mode(self):

        return self.group_analysis(
            "mode_of_participation"
        )

    # 8. Application Analysis

    def applications_by_status(self):

        self.validate_columns([
            "application_status",
            "application_id"
        ])

        return (
            self.data
            .groupby(
                "application_status",
                dropna=False
            )
            .agg(
                applications=(
                    "application_id",
                    "nunique"
                )
            )
            .reset_index()
            .sort_values(
                "applications",
                ascending=False
            )
        )

    # YoY Analysis

    def participation_by_year(self):

        result = self.group_analysis(
            "program_year",
            include_applications=True
        )

        result["program_year"] = pd.to_numeric(
            result["program_year"],
            errors="coerce"
        )

        result = result.sort_values(
            "program_year",
            na_position="last"
        ).reset_index(drop=True)

        # Identify the previous available reporting year
        previous_year = result["program_year"].shift(1)

        previous_students = result["students"].shift(1)

        # Only compare consecutive calendar years
        consecutive_year = (
            result["program_year"] - previous_year
        ) == 1

        result["student_change"] = (
            result["students"] - previous_students
        ).where(consecutive_year)

        # Avoid division by zero
        valid_growth = (
            consecutive_year
            & previous_students.ne(0)
        )

        result["student_growth_percent"] = (
            (
                result["students"] / previous_students - 1
            ) * 100
        ).where(valid_growth).round(2)

        return result

    # 10. Academic Analysis

    def average_gpa_by_college(self):

        self.validate_columns([
            "college",
            "sdsu_gpa",
            "user_id"
        ])

        data = self.data.copy(deep=True)

        data["sdsu_gpa"] = pd.to_numeric(
            data["sdsu_gpa"],
            errors="coerce"
        )

        return (
            data
            .groupby(
                "college",
                dropna=False
            )
            .agg(
                average_gpa=(
                    "sdsu_gpa",
                    "mean"
                ),

                students=(
                    "user_id",
                    "nunique"
                )
            )
            .reset_index()
            .sort_values(
                "average_gpa",
                ascending=False,
                na_position="last"
            )
        )
