import pandas as pd
import logging

# logging.basicConfig(
#     filename = "pipeline1.log", 
#     format = '%(asctime)s %(setlevel)s : %(message)s',
#     filemode = 'w'
#     )

# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# File handler
file_handler = logging.FileHandler("pipeline.log", mode='a')
file_handler.setLevel(logging.DEBUG)

# Shared format for both
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)


def clean(df):

    logger.info("starting the transformation....")

     # Step 1: find and drop columns > 40% missing ✅
    missing_pct = df.isnull().sum() / len(df) * 100
    cols_to_drop = missing_pct[missing_pct > 40].index
    df = df.drop(columns = cols_to_drop)
    logger.info(f"Dropped {len(cols_to_drop)} columns: {list(cols_to_drop)}")

    # Step 2: fill numeric columns with median ✅
    numeric_cols = df.select_dtypes(include=['int64' , 'float64']).columns
    for col in numeric_cols:
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val)
    logger.info(f"Filled numeric columns: {len(numeric_cols)} columns")


    # Step 3: fill text columns with "Unknown" ✅
    text_cols = df.select_dtypes(include=['object', 'string']).columns
    for col in text_cols:
        df[col] = df[col].fillna("Unknown")
    logger.info(f"Filled text columns: {len(text_cols)} columns")

    # Optional: Log remaining missing values
    remaining_nulls = df.isnull().sum().sum()
    if remaining_nulls > 0:
        logger.warning(f"Still have {remaining_nulls} missing values after cleaning")
    else:
        logger.info("All missing values have been filled!")
    
    logger.info("transformation complete.")
    return df

def fix_schema(df) : 

    logger.info("Fixing the names and data types...")

    # Task A — Standardise column names    --> adding a space block 
    original_cols = df.columns.tolist()
    df.columns = df.columns.str.lower()  # lowercase
    df.columns = df.columns.str.strip()  # remove leading/trailing spaces
    df.columns = df.columns.str.replace(' ', '_')  # spaces to underscores
    logger.info(f"Renamed columns: {len(original_cols)} to {len(df.columns)} columns")

   # Task B — Fix the date column (more comprehensive)
    date_col = None
    # Look for common date column names
    for col in df.columns:
        col_lower = col.lower()
        if col_lower in ['date', 'datetime', 'timestamp', 'time', 'obs_date', 'observation_date']:
            date_col = col
            break
        elif 'date' in col_lower or 'time' in col_lower:
            date_col = col
            # Don't break yet - maybe there's a more specific match
            # We'll take the first one found
    
    if date_col:
        try:
            # First try to convert
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce', format='mixed')
            
            # Check conversion success
            null_count = df[date_col].isnull().sum()
            total_count = len(df[date_col])
            
            if null_count > 0:
                logger.warning(f"Date column '{date_col}': {null_count}/{total_count} values couldn't be converted")
            
            # Add date components as integer columns (useful for analysis)
            if not df[date_col].isnull().all():
                df['year'] = df[date_col].dt.year.astype('Int64')  # Int64 handles NaN
                df['month'] = df[date_col].dt.month.astype('Int64')
                df['day'] = df[date_col].dt.day.astype('Int64')
                df['day_of_week'] = df[date_col].dt.dayofweek.astype('Int64')
                logger.info(f"Added derived date columns: year, month, day, day_of_week")
        except Exception as e:
            logger.error(f"Failed to convert date column '{date_col}': {e}")
    else:
        logger.warning("No date column found - looking for any datetime-like column...")
        # Try to auto-detect datetime columns
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    test_conversion = pd.to_datetime(df[col].dropna().head(10), errors='raise')
                    if len(test_conversion) > 0:
                        date_col = col
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                        logger.info(f"Auto-detected date column: '{col}'")
                        break
                except:
                    continue
    # Task C — Fix numeric columns stored as strings

    # Task C — Fix numeric columns stored as strings (improved version)
    numeric_converted = []
    for col in df.columns:
        if col == date_col:
            continue
            
        # Try to convert if it's object/string type
        if df[col].dtype in ['object', 'string']:
            # Peek at non-null values to see if they look numeric
            non_null = df[col].dropna()
            if len(non_null) > 0:
                # Check if column seems numeric (allowing for commas, currency symbols, etc.)
                sample = non_null.head(100).astype(str)
                # Clean the sample for checking (remove commas, currency symbols, etc.)
                cleaned = sample.str.replace(r'[$,%]', '', regex=True).str.strip()
                is_numeric = cleaned.str.match(r'^-?\d*\.?\d+$').all()
                
                if is_numeric:
                    try:
                        # Remove any remaining non-numeric characters and convert
                        df[col] = df[col].astype(str).str.replace(r'[$,%]', '', regex=True)
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                        numeric_converted.append(col)
                        logger.debug(f"Converted column '{col}' to numeric")
                    except Exception as e:
                        logger.warning(f"Failed to convert column '{col}': {e}")
    
    if numeric_converted:
        logger.info(f"Converted {len(numeric_converted)} string columns to numeric: {numeric_converted}")
    logger.info(f"Schema fixed . Columns now: {list(df.columns)}")
    return df

if __name__ == "__main__":
    from extract import extract
    df_raw = extract("weatherAUS.csv")
    df_clean = clean(df_raw)
    df_final = fix_schema(df_clean)
    print(df_final.dtypes)
    # print(df_clean.isnull().sum().sum())  # should show all zeros