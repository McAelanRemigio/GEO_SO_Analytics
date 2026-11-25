# Study Abroad Analytics

A Python package for independently processing, validating, and analyzing exported Study Abroad reports.

The goal of this project is to make Study Abroad data easier to organize and understand without depending on the institution's original reporting system. It provides tools for loading exported data, cleaning and filtering records, validating data quality, and generating summaries of student participation.

## Features

- **Data loading:** Import Study Abroad reports from CSV and Excel files, or load an existing pandas DataFrame.
- **Data inspection:** Review columns, record counts, and basic information about a dataset.
- **Data transformation:** Normalize column names, clean text values, and convert columns to dates or numeric values.
- **Data filtering and searching:** Filter records by values or ranges and search across the dataset.
- **Data organization:** Sort, group, and reset data.
- **Study Abroad analytics:** Analyze participation by college, major, class level, country, region, program type, category, and participation mode.
- **Application analysis:** Summarize application statuses and participation trends over time.
- **GPA analysis:** Calculate average GPA by college.
- **Data validation:** Check required columns, missing values, duplicate records, data types, student IDs, application IDs, and GPA values.

## Project structure

```text
study_abroad_analytics_project/
│
├── study_abroad_analytics/
│   ├── __init__.py
│   ├── config.py
│   ├── data_engine.py
│   ├── validation.py
│   └── analytics_engine.py
│
├── tests/
│   ├── test_data_engine.py
│   └── test_analytics_engine.py
│
├── README.md
└── pyproject.toml
```

## Requirements

- Python 3.9 or later
- pandas
- openpyxl for `.xlsx` Excel files
- xlrd for `.xls` Excel files

## Installation

Clone or download this project, then open a terminal in the project directory.

Install the package and its core dependencies:

```bash
pip install -e .
```

To install the testing and Excel extras:

```bash
pip install -e ".[dev,excel]"
```

## Quick start

### Load and inspect a report

```python
import pandas as pd

from study_abroad_analytics import StudyAbroadDataEngine

# Load a report from a CSV file
engine = StudyAbroadDataEngine(filepath="study_abroad_report.csv")

# Inspect the dataset
print(engine.inspect())

# View the data
print(engine.get_data())
```

You can also start with a pandas DataFrame:

```python
import pandas as pd

from study_abroad_analytics import StudyAbroadDataEngine

df = pd.read_csv("study_abroad_report.csv")

engine = StudyAbroadDataEngine(dataframe=df)
```

### Clean and transform data

```python
engine.transform(
    normalize_columns=True,
    strip_text=True
)
```

Column normalization makes column names easier to work with. For example, `Program Country` becomes `program_country`.

You can also convert selected columns:

```python
engine.transform(
    convert_numeric=["sdsu_gpa", "program_year"],
    convert_dates=["application_date"]
)
```

Use the column names that actually exist in your report.

### Filter records

```python
# Filter by college
engine.filter({"college": "Business"})

# Filter by program year
engine.filter({
    "program_year": {
        "min": 2022,
        "max": 2025
    }
})

# Restore the original dataset
engine.reset()
```

### Run Study Abroad analytics

```python
from study_abroad_analytics import StudyAbroadAnalyticsEngine

analytics = StudyAbroadAnalyticsEngine(
    filepath="study_abroad_report.csv"
)

# Review participation totals
print(analytics.participation_summary())

# Participation by college
print(analytics.participation_by_college())

# Participation by country
print(analytics.participation_by_country())

# Participation by year
print(analytics.participation_by_year())

# Average GPA by college
print(analytics.average_gpa_by_college())
```

The analytics methods depend on the expected column names being present in your report. Review the required columns in `config.py` and validate your dataset before running analyses.

### Validate a report

```python
from study_abroad_analytics import (
    StudyAbroadDataEngine,
    StudyAbroadValidator
)

engine = StudyAbroadDataEngine(
    filepath="study_abroad_report.csv"
)

validator = StudyAbroadValidator(engine.get_data())

report = validator.validate_all()

print(report)
print(validator.get_summary())
```

Validation results help identify potential data-quality issues. Some findings, such as repeated application IDs, may be legitimate depending on how the source report is structured. Review them in context rather than automatically deleting records.

## Running tests

Install the development dependencies:

```bash
pip install -e ".[dev,excel]"
```

Run the complete test suite:

```bash
pytest
```

Run an individual test file:

```bash
pytest tests/test_data_engine.py -v
```

```bash
pytest tests/test_analytics_engine.py -v
```

## Important data considerations

Before interpreting results, understand what one row represents in the exported report.

For example, a report may contain:
- One row per student
- One row per application
- One row per program participation

These are different measures. A student who submits multiple applications may appear more than once. For that reason, the package distinguishes between record counts, unique student counts, and application counts where appropriate.

Also review:
- Whether student and application IDs are populated.
- Whether GPA values use a 0–4.0 scale.
- Whether program years are stored consistently.
- Whether repeated application IDs are expected in the source report.
- Whether column names match the package's expected names.

## Current development scope

This project is intended to be a practical, independent analytics tool for exported Study Abroad reports. The initial focus is reliable data loading, cleaning, validation, and descriptive analysis. More advanced statistical analysis, visualizations, and automated reporting can be added as the project develops.

## License

TBD
