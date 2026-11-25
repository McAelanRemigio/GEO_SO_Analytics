"""
Study Abroad Analytics Engine

Central configuration settings for data management,
validation, and Study Abroad analytics.
"""


# 1. Package Information

VERSION = "1.0.0"

AUTHOR = "Study Abroad Analytics Project"

DESCRIPTION = (
    "A Python tool for organizing and analyzing "
    "study abroad data."
)


# 2. Supported File Formats

SUPPORTED_FILE_FORMATS = [
    ".csv",
    ".xlsx",
    ".xls"
]


# 3. Column Normalization Settings

NORMALIZE_COLUMNS = True

STRIP_TEXT_VALUES = True

LOWERCASE_COLUMNS = True

REPLACE_SPACES_WITH_UNDERSCORES = True


# 4. Student Identification Columns

STUDENT_ID_COLUMN = "user_id"

APPLICATION_ID_COLUMN = "application_id"

PROGRAM_ID_COLUMN = "program_id"


# 5. Student Demographic Columns

DEMOGRAPHIC_COLUMNS = [
    "college",
    "first_major",
    "outbound_class_level"
]


# 6. Program Information Columns

PROGRAM_COLUMNS = [
    "program_id",
    "program_country",
    "program_region",
    "program_year",
    "program_type",
    "program_category",
    "mode_of_participation"
]


# 7. Application Information Columns

APPLICATION_COLUMNS = [
    "application_id",
    "application_status"
]


# 8. Academic Information Columns

ACADEMIC_COLUMNS = [
    "sdsu_gpa"
]


# 9. Required Analytics Columns

REQUIRED_ANALYTICS_COLUMNS = [
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


# 10. Optional Analytics Columns

OPTIONAL_ANALYTICS_COLUMNS = [
    "program_id",
    "program_region",
    "first_major",
    "outbound_class_level",
    "sdsu_gpa"
]


# 11. Date & Numeric Columns

DATE_COLUMNS = [
    "application_date"
]

NUMERIC_COLUMNS = [
    "sdsu_gpa",
    "program_year"
]


# 12. GPA Settings

GPA_COLUMN = "sdsu_gpa"

GPA_MIN = 0.0

GPA_MAX = 4.0

# 13. YoY Settings

YEAR_COLUMN = "program_year"

YEAR_GROWTH_DECIMAL_PLACES = 2


# 14. Validation Settings

CHECK_DUPLICATES = True

CHECK_MISSING_VALUES = True

CHECK_REQUIRED_COLUMNS = True

CHECK_DATA_TYPES = True

CHECK_GPA_RANGE = True

CHECK_STUDENT_IDS = True

CHECK_APPLICATION_IDS = True


# 15. Default Dataframe Settings

DEFAULT_ENCODING = "utf-8"

DEFAULT_MISSING_VALUES = [
    "",
    "NA",
    "N/A",
    "NULL",
    "null"
]
