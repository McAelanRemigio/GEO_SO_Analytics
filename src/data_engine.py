
from pathlib import Path
from time import perf_counter

import pandas as pd


class StudyAbroadDataEngine:

    def __init__(self, filepath=None, dataframe=None):

        if filepath is None and dataframe is None:
            raise ValueError("Provide a filepath or dataframe.")

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

        if not filepath.exists():
            raise FileNotFoundError(filepath)

        start = perf_counter()

        if filepath.suffix.lower() == ".csv":
            df = pd.read_csv(filepath)

        elif filepath.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(filepath)

        else:
            raise ValueError("Unsupported file format.")

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
            raise TypeError("Expected a pandas DataFrame.")

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
            "missing_values": self.data.isna().sum().to_dict(),
            "duplicates": int(self.data.duplicated().sum()),
            "memory_mb": round(
                self.data.memory_usage(deep=True).sum() / 1024**2, 3
            )
        }

    def validate_columns(self, columns):

        missing = [c for c in columns if c not in self.data.columns]

        if missing:
            raise ValueError(f"Missing columns: {missing}")

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
            self.data.columns = [
                str(c).strip().lower().replace(" ", "_")
                for c in self.data.columns
            ]

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

        for col in convert_dates or []:
            self.validate_columns([col])
            self.data[col] = pd.to_datetime(
                self.data[col], errors="coerce"
            )

        for col in convert_numeric or []:
            self.validate_columns([col])
            self.data[col] = pd.to_numeric(
                self.data[col], errors="coerce"
            )

        elapsed = perf_counter() - start

        self.metrics["transformation_seconds"] = elapsed

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

            if isinstance(value, dict):

                if "isnull" in value:
                    mask = series.isna() if value["isnull"] else series.notna()

                else:
                    numeric = pd.to_numeric(series, errors="coerce")
                    mask = pd.Series(True, index=self.data.index)

                    if "min" in value:
                        mask &= numeric >= value["min"]

                    if "max" in value:
                        mask &= numeric <= value["max"]

                self.data = self.data[mask]

            elif isinstance(value, (list, tuple, set)):
                self.data = self.data[self.data[col].isin(value)]

            else:
                self.data = self.data[self.data[col] == value]

        elapsed = perf_counter() - start

        self.metrics["filtering_seconds"] = (
            self.metrics.get("filtering_seconds", 0) + elapsed
        )

        self.history.append({
            "operation": "filter",
            "conditions": conditions,
            "records": len(self.data),
            "seconds": elapsed
        })

        return self

    def search(self, column, keyword, case_sensitive=False):

        self.validate_columns([column])

        start = perf_counter()

        mask = self.data[column].astype("string").str.contains(
            str(keyword),
            case=case_sensitive,
            na=False,
            regex=False
        )

        self.data = self.data[mask]

        elapsed = perf_counter() - start

        self.history.append({
            "operation": "search",
            "column": column,
            "keyword": keyword,
            "records": len(self.data),
            "seconds": elapsed
        })

        return self

    # 5. Data Sorting

    def sort(self, by, ascending=True, inplace=True):

        columns = [by] if isinstance(by, str) else list(by)

        self.validate_columns(columns)

        start = perf_counter()

        result = self.data.sort_values(
            by=columns,
            ascending=ascending,
            na_position="last"
        )

        elapsed = perf_counter() - start

        self.metrics["sorting_seconds"] = (
            self.metrics.get("sorting_seconds", 0) + elapsed
        )

        self.history.append({
            "operation": "sort",
            "columns": columns,
            "seconds": elapsed
        })

        if inplace:
            self.data = result
            return self

        return result.copy()

    # 6. Grouping and Aggregating

    def group_by(self, columns, aggregations=None):

        columns = [columns] if isinstance(columns, str) else list(columns)

        self.validate_columns(columns)

        if aggregations is None:

            aggregations = {}

            defaults = {
                "applications": ("application_id", "nunique"),
                "unique_students": ("user_id", "nunique"),
                "distinct_programs": ("program_id", "nunique")
            }

            for name, (col, operation) in defaults.items():
                if col in self.data.columns:
                    aggregations[name] = (col, operation)

            if not aggregations:
                aggregations["records"] = (self.data.columns[0], "size")

        start = perf_counter()

        result = (
            self.data
            .groupby(columns, dropna=False)
            .agg(**{
                name: (col, operation)
                for name, (col, operation) in aggregations.items()
            })
            .reset_index()
        )

        elapsed = perf_counter() - start

        self.metrics["grouping_seconds"] = (
            self.metrics.get("grouping_seconds", 0) + elapsed
        )

        self.history.append({
            "operation": "group_by",
            "columns": columns,
            "seconds": elapsed
        })

        return result

    # 7. Data Management

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

    # 8. Metrics and History

    def get_metrics(self):
        return self.metrics.copy()

    def get_history(self):
        return pd.DataFrame(self.history)

    def get_record_count(self):
        return len(self.data)
