"""
Study Abroad Analytics Engine

Generic data management engine.

Handles importing, inspecting, transforming, filtering,
searching, sorting, grouping, and managing datasets.
"""

from pathlib import Path
from time import perf_counter

import pandas as pd


class StudyAbroadDataEngine:

    def __init__(self, filepath=None, dataframe=None):

        if filepath is None and dataframe is None:
            raise ValueError(
                "Provide a filepath or dataframe."
            )

        self.filepath = None
        self.original_data = None
        self.data = None
        self.metrics = {}
        self.history = []

        if dataframe is not None:
            self.load_dataframe(dataframe)

        else:
            self.load_report(filepath)

    # 1. Load Data

    def load_report(self, filepath):

        filepath = Path(filepath)

        if not filepath.is_file():
            raise FileNotFoundError(filepath)

        start = perf_counter()

        extension = filepath.suffix.lower()

        if extension == ".csv":
            df = pd.read_csv(filepath)

        elif extension in [".xlsx", ".xls"]:
            df = pd.read_excel(filepath)

        else:
            raise ValueError(
                "Unsupported file format. "
                "Use CSV, XLSX, or XLS."
            )

        elapsed = perf_counter() - start

        self.filepath = filepath

        self.load_dataframe(df)

        self.metrics["loading_seconds"] = elapsed
        self.metrics["source_file"] = filepath.name

        self.history.append({
            "operation": "load",
            "records": len(df),
            "seconds": elapsed
        })

        return self

    def load_dataframe(self, dataframe):

        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError(
                "Expected a pandas DataFrame."
            )

        self.original_data = dataframe.copy(deep=True)
        self.data = dataframe.copy(deep=True)

        self.metrics["original_records"] = len(dataframe)
        self.metrics["original_columns"] = len(dataframe.columns)

        return self

    # 2. Data Inspection

    def inspect(self):

        return {
            "records": len(self.data),

            "columns": list(self.data.columns),

            "missing_values": (
                self.data.isna().sum().to_dict()
            ),

            "duplicates": int(
                self.data.duplicated().sum()
            ),

            "memory_mb": round(
                self.data.memory_usage(deep=True).sum()
                / 1024**2,
                3
            )
        }

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

    # 3. Data Transformation

    def transform(
        self,
        normalize_columns=True,
        strip_text=True,
        convert_dates=None,
        convert_numeric=None
    ):

        start = perf_counter()

        if normalize_columns:

            normalized = [
                str(col).strip().lower().replace(" ", "_")
                for col in self.data.columns
            ]

            if len(normalized) != len(set(normalized)):
                raise ValueError(
                    "Column normalization created duplicate "
                    "column names. Check the original headers."
                )

            self.data.columns = normalized

        # Validate requested conversion columns first
        date_columns = convert_dates or []
        numeric_columns = convert_numeric or []

        self.validate_columns(
            date_columns + numeric_columns
        )

        # Strip whitespace from text columns
        if strip_text:

            cols = self.data.select_dtypes(
                include=["object", "string"]
            ).columns

            for col in cols:

                self.data[col] = (
                    self.data[col]
                    .astype("string")
                    .str.strip()
                    .replace("", pd.NA)
                )

        # Convert date columns
        for col in date_columns:

            self.data[col] = pd.to_datetime(
                self.data[col],
                errors="coerce"
            )

        # Convert numeric columns
        for col in numeric_columns:

            self.data[col] = pd.to_numeric(
                self.data[col],
                errors="coerce"
            )

        elapsed = perf_counter() - start

        self.metrics["transformation_seconds"] = (
            self.metrics.get("transformation_seconds", 0)
            + elapsed
        )

        self.history.append({
            "operation": "transform",
            "records": len(self.data),
            "seconds": elapsed
        })

        return self

    # 4. Data Filtering

    def filter(self, **conditions):

        start = perf_counter()

        for col, value in conditions.items():

            self.validate_columns([col])

            series = self.data[col]

            # Handle missing values
            if value is None:
                mask = series.isna()

            elif isinstance(value, dict):

                if "isnull" in value:

                    if set(value) != {"isnull"}:
                        raise ValueError(
                            "Use isnull separately from "
                            "numeric filter conditions."
                        )

                    if not isinstance(value["isnull"], bool):
                        raise ValueError(
                            "isnull must be True or False."
                        )

                    mask = (
                        series.isna()
                        if value["isnull"]
                        else series.notna()
                    )

                else:

                    if not value or not set(value).issubset(
                        {"min", "max"}
                    ):
                        raise ValueError(
                            "Numeric filters must use "
                            "'min' and/or 'max'."
                        )

                    numeric = pd.to_numeric(
                        series,
                        errors="coerce"
                    )

                    mask = pd.Series(
                        True,
                        index=self.data.index
                    )

                    for bound in ["min", "max"]:

                        if bound not in value:
                            continue

                        limit = pd.to_numeric(
                            value[bound],
                            errors="coerce"
                        )

                        if pd.isna(limit):
                            raise ValueError(
                                f"Invalid numeric {bound} "
                                f"value for column '{col}'."
                            )

                        if bound == "min":
                            mask &= numeric >= limit

                        else:
                            mask &= numeric <= limit

                    mask = mask.fillna(False)

            # Handle multiple possible values
            elif isinstance(value, (list, tuple, set)):

                mask = series.isin(value)

            # Handle exact matches
            else:

                mask = series == value

            self.data = self.data.loc[mask].copy()

        elapsed = perf_counter() - start

        self.metrics["filtering_seconds"] = (
            self.metrics.get("filtering_seconds", 0)
            + elapsed
        )

        self.history.append({
            "operation": "filter",
            "conditions": conditions,
            "records": len(self.data),
            "seconds": elapsed
        })

        return self

    # 5. Data Search

    def search(
        self,
        column,
        keyword,
        case_sensitive=False
    ):

        self.validate_columns([column])

        start = perf_counter()

        mask = (
            self.data[column]
            .astype("string")
            .str.contains(
                str(keyword),
                case=case_sensitive,
                na=False,
                regex=False
            )
        )

        self.data = self.data.loc[mask].copy()

        elapsed = perf_counter() - start

        self.history.append({
            "operation": "search",
            "column": column,
            "keyword": keyword,
            "records": len(self.data),
            "seconds": elapsed
        })

        return self

    # 6. Data Sorting

    def sort(
        self,
        by,
        ascending=True,
        inplace=True
    ):

        columns = (
            [by]
            if isinstance(by, str)
            else list(by)
        )

        self.validate_columns(columns)

        start = perf_counter()

        result = self.data.sort_values(
            by=columns,
            ascending=ascending,
            na_position="last"
        )

        elapsed = perf_counter() - start

        self.metrics["sorting_seconds"] = (
            self.metrics.get("sorting_seconds", 0)
            + elapsed
        )

        self.history.append({
            "operation": "sort",
            "columns": columns,
            "seconds": elapsed
        })

        if inplace:

            self.data = result.copy()

            return self

        return result.copy()

    # 7. Grouping & Aggregation

    def group_by(
        self,
        columns,
        aggregations=None
    ):

        columns = (
            [columns]
            if isinstance(columns, str)
            else list(columns)
        )

        self.validate_columns(columns)

        if aggregations is None:

            aggregations = {
                "records": (columns[0], "size")
            }

        for name, specification in aggregations.items():

            if (
                not isinstance(specification, (tuple, list))
                or len(specification) != 2
            ):
                raise ValueError(
                    "Each aggregation must contain "
                    "(column, operation)."
                )

            self.validate_columns([specification[0]])

        start = perf_counter()

        result = (
            self.data
            .groupby(
                columns,
                dropna=False
            )
            .agg(**{
                name: (col, operation)
                for name, (col, operation)
                in aggregations.items()
            })
            .reset_index()
        )

        elapsed = perf_counter() - start

        self.metrics["grouping_seconds"] = (
            self.metrics.get("grouping_seconds", 0)
            + elapsed
        )

        self.history.append({
            "operation": "group_by",
            "columns": columns,
            "seconds": elapsed
        })

        return result

    # 8. Data Management

    def reset(self):

        self.data = self.original_data.copy(deep=True)

        self.history.append({
            "operation": "reset",
            "records": len(self.data)
        })

        return self

    def get_data(self):

        return self.data.copy(deep=True)

    def get_original_data(self):

        return self.original_data.copy(deep=True)

    # 9. Metrics & History

    def get_metrics(self):

        return self.metrics.copy()

    def get_history(self):

        return pd.DataFrame(self.history)

    def get_record_count(self):

        return len(self.data)
