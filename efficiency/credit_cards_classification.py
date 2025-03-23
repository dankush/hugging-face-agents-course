import os
import pandas as pd
import re

# Define the paths to the Excel files
input_files = [
    "/Users/dankushpro/Downloads/transaction-details_export_1742482494398.xlsx"
    ,"/Users/dankushpro/Downloads/פירוט עסקאות וזיכויים.xlsx"
]

# Define the expected columns (final standardized names)
expected_columns = [
    "תאריך עסקה", "שם בית העסק", "4 ספרות אחרונות של כרטיס האשראי",
    "סכום חיוב", "תאריך חיוב", "סוג עסקה"
]

# Mapping of possible column names (variations in English or Hebrew) to expected names.
column_mapping = {
    # English names
    r"(?i)^date$": "תאריך עסקה",
    r"(?i)^description$": "שם בית העסק",
    r"(?i)^card$": "4 ספרות אחרונות של כרטיס האשראי",
    r"(?i)^amount$": "סכום חיוב",
    r"(?i)^charge\s*date$": "תאריך חיוב",
    r"(?i)^type$": "סוג עסקה",
    # Hebrew names and variations
    r"(?i)^תאריך\s*$": "תאריך עסקה",
    r"(?i)^תאריך\s*עסקה$": "תאריך עסקה",
    r"(?i)^תאריך\s*\n\s*עסקה$": "תאריך עסקה",
    r"(?i)^שם\s*בית\s*עסק$": "שם בית העסק",
    r"(?i)^סכום\b": "סכום חיוב",
    r"(?i)^כרטיס$": "4 ספרות אחרונות של כרטיס האשראי",
    r"(?i)^מועד\s*חיוב$": "תאריך חיוב",
    r"(?i)^מועד\b": "תאריך חיוב",
    r"(?i)^סוג\s*עסקה$": "סוג עסקה",
    r"(?i)^סוג\s*\n\s*עסקה$": "סוג עסקה",
    # Handle headers with line breaks and quotes:
    r"(?i)^סכום\s*\n\s*בש״?ח$": "סכום חיוב",
    r"(?i)^מועד\s*\n\s*חיוב$": "תאריך חיוב"
}


def detect_header_row(df: pd.DataFrame) -> int:
    """
    Scans the first 20 rows for keywords (in both English and Hebrew) to detect the header row.
    """
    expected_keywords = [
        "date", "description", "card", "amount", "charge", "type",
        "תאריך", "בית", "עסק", "סכום", "כרטיס", "חיוב", "סוג"
    ]
    for i in range(min(20, len(df))):
        row = df.iloc[i].astype(str).str.strip().tolist()
        matches = sum(any(keyword.lower() in cell.lower() for cell in row) for keyword in expected_keywords)
        if matches >= 2:
            print(f"Header detected at row {i}: {row}")
            return i
    print("No header detected in the first 20 rows.")
    return None


def standardize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renames DataFrame columns using regex-based mapping.
    """
    new_columns = {}
    for col in df.columns:
        clean_col = str(col).strip().replace("\n", " ")
        renamed = clean_col  # default to original if no pattern matches
        for pattern, replacement in column_mapping.items():
            if re.search(pattern, clean_col):
                renamed = replacement
                break
        new_columns[col] = renamed
    df.rename(columns=new_columns, inplace=True)
    # Drop duplicate columns (keep the first occurrence)
    df = df.loc[:, ~df.columns.duplicated()]
    return df


def safe_float(val):
    """
    Attempts to convert val to a float. Returns 0.0 if conversion fails.
    """
    try:
        return float(str(val).replace("₪", "").replace(",", "").strip())
    except Exception:
        return 0.0


def load_and_clean_excel(file_path: str) -> pd.DataFrame:
    """
    Loads an Excel file (without assuming the first row is the header),
    detects and sets the header row, renames columns, and retains only the expected columns.
    Also converts date columns and cleans numeric and string data.
    """
    try:
        print(f"\nLoading file: {file_path}")
        # Load the file without a header
        df = pd.read_excel(file_path, engine='openpyxl', header=None)
        header_row = detect_header_row(df)
        if header_row is None:
            print(f"Could not detect header row in file: {file_path}")
            print("First 5 rows:")
            print(df.head().to_string())
            return None

        # Set the detected header and drop rows above it
        df.columns = df.iloc[header_row].astype(str).str.strip()
        df = df.drop(range(header_row + 1)).reset_index(drop=True)
        # Clean headers by removing line breaks
        df.columns = df.columns.str.replace('\n', ' ').str.strip()

        print(f"Columns before renaming: {df.columns.tolist()}")
        df = standardize_headers(df)
        print(f"Columns after renaming: {df.columns.tolist()}")

        # Ensure all expected columns exist; if missing, add them with defaults.
        for col in expected_columns:
            if col not in df.columns:
                df[col] = 0.0 if col == "סכום חיוב" else ""

        # Retain only the expected columns
        df = df[expected_columns]

        # Convert date columns to datetime format (day-first)
        if "תאריך עסקה" in df.columns:
            df["תאריך עסקה"] = pd.to_datetime(df["תאריך עסקה"], errors='coerce', dayfirst=True)
        if "תאריך חיוב" in df.columns:
            df["תאריך חיוב"] = pd.to_datetime(df["תאריך חיוב"], errors='coerce', dayfirst=True)

        # Clean specific columns
        if "שם בית העסק" in df.columns:
            df["שם בית העסק"] = df["שם בית העסק"].astype(str).str.strip()
        if "4 ספרות אחרונות של כרטיס האשראי" in df.columns:
            # For each cell, if length > 4, take the last 4; otherwise, leave as is.
            df["4 ספרות אחרונות של כרטיס האשראי"] = df["4 ספרות אחרונות של כרטיס האשראי"].astype(str).str.strip().apply(
                lambda x: x if len(x) == 4 else x[-4:] if len(x) > 4 else x
            )
        if "סכום חיוב" in df.columns:
            df["סכום חיוב"] = df["סכום חיוב"].apply(safe_float)
        if "סוג עסקה" in df.columns:
            df["סוג עסקה"] = df["סוג עסקה"].astype(str).str.strip()

        # Fill NaN values in string columns with empty strings
        for col in df.columns:
            if col != "סכום חיוב" and df[col].dtype == "object":
                df[col] = df[col].fillna("")

        return df

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None


def merge_datasets(input_files: list, output_file: str):
    """
    Loads, cleans, and merges multiple Excel files.
    Prints overall statistics and saves the merged DataFrame to a CSV file.
    """
    all_data = []
    for file in input_files:
        df = load_and_clean_excel(file)
        if df is not None:
            all_data.append(df)

    if all_data:
        merged_df = pd.concat(all_data, ignore_index=True)
        if "תאריך עסקה" in merged_df.columns:
            merged_df = merged_df.sort_values(by="תאריך עסקה", na_position='last')
        merged_df = merged_df[expected_columns]

        # Print statistics
        print("\n=== Data Overview ===")
        print(f"Total Transactions: {len(merged_df)}")
        print(f"Columns in final dataset: {list(merged_df.columns)}")
        print("\n=== First 5 Transactions ===")
        print(merged_df.head())
        print("\n=== Summary Statistics ===")
        numeric_cols = merged_df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            print(merged_df[numeric_cols].describe())
        else:
            print("No numeric columns for summary statistics.")
        if "שם בית העסק" in merged_df.columns:
            print(f"\nUnique business names: {merged_df['שם בית העסק'].nunique()}")
        if "סכום חיוב" in merged_df.columns:
            print(f"Total amount charged: {merged_df['סכום חיוב'].sum():.2f}")
        if "תאריך עסקה" in merged_df.columns:
            min_date = merged_df['תאריך עסקה'].min()
            max_date = merged_df['תאריך עסקה'].max()
            min_date_str = min_date.strftime('%Y-%m-%d') if pd.notna(min_date) else "N/A"
            max_date_str = max_date.strftime('%Y-%m-%d') if pd.notna(max_date) else "N/A"
            print(f"Date range: {min_date_str} to {max_date_str}")

        # Save merged data to CSV
        merged_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n✅ Merged data saved to: {output_file}")
    else:
        print("⚠ No data was loaded. Please check the file paths and formats.")


if __name__ == "__main__":
    output_csv = "merged_transactions.csv"
    merge_datasets(input_files, output_csv)