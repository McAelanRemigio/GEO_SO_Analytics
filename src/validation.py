"""
Study Abroad Analytics Engine

Validates exported Study Abroad datasets.

Checks dataset structure, required columns, missing values,
duplicates, data types, identifiers, and academic values.
"""

import pandas as pd

from . import config


class StudyAbroadValidator:

    def __init__(self, dataframe):

        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError(
                "Expected a pandas DataFrame."
            )

        self.data = dataframe.copy(deep=True)

        self.results = []

    # 1. Validation Utilities

    def validate_columns(self, columns):

        missing = [
            col for col in columns
            if col not in self.data.columns
        ]

        return {
            "valid": len(missing) == 0,
            "missing_columns": missing
        }

    def _record_result(
        self,
        category,
        check,
        passed,
        message,
        details=None
    ):

        self.results.append({
            "category": category,
            "check": check,
            "passed": bool(passed),
            "message": message,
            "details": details
        })

    # 2. Structural Validation

    def validate_structure(self):

        required = config.REQUIRED_ANALYTICS_COLUMNS

        result = self.validate_columns(required)

        self._record_result(
            category="structure",
            check="required_columns",
            passed=result["valid"],
            message=(
                "All required columns are present."
                if result["valid"]
                else "Required columns are missing."
            ),
            details=result["missing_columns"]
        )

        duplicate_columns = (
            self.data.columns[
                self.data.columns.duplicated()
            ].tolist()
        )

        self._record_result(
            category="structure",
            check="duplicate_columns",
            passed=len(duplicate_columns) == 0,
            message=(
                "No duplicate column names found."
                if not duplicate_columns
                else "Duplicate column names detected."
            ),
            details=duplicate_columns
        )

        return self

    # 3. Missing Value Validation

    def validate_missing_values(self):

        missing = self.data.isna().sum()

        total_missing = int(missing.sum())

        missing_columns = {
            col: int(count)
            for col, count in missing.items()
            if count > 0
        }

        self._record_result(
            category="completeness",
            check="missing_values",
            passed=total_missing == 0,
            message=(
                "No missing values found."
                if total_missing == 0
                else f"{total_missing} missing values detected."
            ),
            details=missing_columns
        )

        # Check critical identifiers separately

        for col in [
            config.STUDENT_ID_COLUMN,
            config.APPLICATION_ID_COLUMN
        ]:

            if col not in self.data.columns:
                continue

            count = int(self.data[col].isna().sum())

            self._record_result(
                category="completeness",
                check=f"{col}_missing",
                passed=count == 0,
                message=(
                    f"No missing values in {col}."
                    if count == 0
                    else f"{count} missing values in {col}."
                ),
                details={"missing_records": count}
            )

        return self

    # 4. Duplicate Validation 

    def validate_duplicates(self):

        duplicate_count = int(
            self.data.duplicated().sum()
        )

        self._record_result(
            category="duplicates",
            check="duplicate_records",
            passed=duplicate_count == 0,
            message=(
                "No duplicate records found."
                if duplicate_count == 0
                else f"{duplicate_count} duplicate records found."
            ),
            details={
                "duplicate_records": duplicate_count
            }
        )

        # Check duplicate application identifiers

        if config.APPLICATION_ID_COLUMN in self.data.columns:

            application_ids = self.data[
                config.APPLICATION_ID_COLUMN
            ].dropna()

            duplicate_applications = int(
                application_ids.duplicated().sum()
            )

            self._record_result(
                category="duplicates",
                check="duplicate_application_ids",
                passed=duplicate_applications == 0,
                message=(
                    "Application IDs are unique."
                    if duplicate_applications == 0
                    else (
                        f"{duplicate_applications} repeated "
                        "application IDs found."
                    )
                ),
                details={
                    "repeated_application_ids": (
                        duplicate_applications
                    )
                }
            )

        return self

    # 5. Datatype Validation 

    def validate_data_types(self):

        expected_numeric = config.NUMERIC_COLUMNS

        expected_dates = config.DATE_COLUMNS

        for col in expected_numeric:

            if col not in self.data.columns:
                continue

            converted = pd.to_numeric(
                self.data[col],
                errors="coerce"
            )

            invalid = (
                self.data[col].notna()
                & converted.isna()
            )

            invalid_count = int(invalid.sum())

            self._record_result(
                category="data_types",
                check=f"{col}_numeric",
                passed=invalid_count == 0,
                message=(
                    f"{col} contains valid numeric values."
                    if invalid_count == 0
                    else (
                        f"{invalid_count} nonnumeric values "
                        f"found in {col}."
                    )
                ),
                details={
                    "invalid_values": invalid_count
                }
            )

        for col in expected_dates:

            if col not in self.data.columns:
                continue

            converted = pd.to_datetime(
                self.data[col],
                errors="coerce"
            )

            invalid = (
                self.data[col].notna()
                & converted.isna()
            )

            invalid_count = int(invalid.sum())

            self._record_result(
                category="data_types",
                check=f"{col}_date",
                passed=invalid_count == 0,
                message=(
                    f"{col} contains valid dates."
                    if invalid_count == 0
                    else (
                        f"{invalid_count} invalid dates "
                        f"found in {col}."
                    )
                ),
                details={
                    "invalid_dates": invalid_count
                }
            )

        return self

    #  6. GPA Validation

    def validate_gpa(self):

        col = config.GPA_COLUMN

        if col not in self.data.columns:
            self._record_result(
                category="academic",
                check="gpa_range",
                passed=False,
                message=f"GPA column '{col}' is missing.",
                details=None
            )

            return self

        gpa = pd.to_numeric(
            self.data[col],
            errors="coerce"
        )

        invalid = (
            gpa.notna()
            & (
                (gpa < config.GPA_MIN)
                | (gpa > config.GPA_MAX)
            )
        )

        invalid_count = int(invalid.sum())

        self._record_result(
            category="academic",
            check="gpa_range",
            passed=invalid_count == 0,
            message=(
                "All numeric GPA values are within range."
                if invalid_count == 0
                else (
                    f"{invalid_count} GPA values fall "
                    "outside the configured range."
                )
            ),
            details={
                "invalid_gpa_count": invalid_count,
                "minimum_allowed": config.GPA_MIN,
                "maximum_allowed": config.GPA_MAX
            }
        )

        return self

    # 7. Student Identifier Validation

    def validate_student_ids(self):

        col = config.STUDENT_ID_COLUMN

        if col not in self.data.columns:
            self._record_result(
                category="identifiers",
                check="student_ids",
                passed=False,
                message=f"Student ID column '{col}' is missing.",
                details=None
            )

            return self

        missing = int(
            self.data[col].isna().sum()
        )

        unique = int(
            self.data[col].nunique()
        )

        self._record_result(
            category="identifiers",
            check="student_ids",
            passed=missing == 0,
            message=(
                "Student identifiers are populated."
                if missing == 0
                else f"{missing} student identifiers are missing."
            ),
            details={
                "unique_students": unique,
                "missing_student_ids": missing
            }
        )

        return self

    # Run All Validations

    def validate_all(self):

        self.results = []

        self.validate_structure()

        self.validate_missing_values()

        self.validate_duplicates()

        self.validate_data_types()

        self.validate_gpa()

        self.validate_student_ids()

        return self.get_report()

    # 9. Validation Report

    def get_report(self):

        return pd.DataFrame(self.results)

    def get_summary(self):

        report = self.get_report()

        if report.empty:
            return {
                "total_checks": 0,
                "passed": 0,
                "failed": 0,
                "overall_status": "NOT RUN"
            }

        total = len(report)

        passed = int(report["passed"].sum())

        failed = total - passed

        return {
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "overall_status": (
                "PASSED"
                if failed == 0
                else "ISSUES FOUND"
            )
        }

    def get_data(self):

        return self.data.copy(deep=True)
