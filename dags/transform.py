import pandas as pd
import logging
import os  

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
      # check if columns exist before  creating new features
    possible_max_cols = ['maxtemp','max_temp' , 'maxTemp', 'max Temp' , 'temp_max' ]
    possible_min_cols = ['mintemp','min_temp', 'mintemp', 'min temp', 'temp_min']

    max_col = None
    min_col = None

    for col in possible_max_cols:
        if col in df.columns:
            max_col = col
            break
    
    for col in possible_min_cols:
        if col in df.columns:
            min_col = col
            break

    # create only if both temperature columns exist
    if max_col and min_col:
        df['temp_range'] = df[max_col] - df[min_col]
        logger.info(f"Created 'temp_range' feature using {max_col} and {min_col}")

        df['is_hot_day'] = df[max_col] > 35
        logger.info(f"Created 'is_hot_day' feature (True when {max_col} > 35)")
    else:
        logger.warning(f"Could not find temperature columns. Found max: {max_col}, min: {min_col}")

    if 'month' in df.columns:
        season_map = {
            12: 'Summer', 1: 'Summer', 2: 'Summer',
            3: 'Autumn', 4: 'Autumn', 5: 'Autumn',
            6: 'Winter', 7: 'Winter', 8: 'Winter',
            9: 'Spring', 10: 'Spring', 11: 'Spring'
        }
        df['season'] = df['month'].map(season_map)
        logger.info("Created 'season' column from month")
    else:
        logger.warning("'month' column not found - cannot create 'season' feature")

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

def save_parquet(df, output_path ,csv_path=None):
    logger.info(f"Saving to Parquet: {output_path}")

    # Task A: save to parquet
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # Save to parquet (no index)
        df.to_parquet(output_path, index=False, engine='pyarrow')
        logger.info(f"Successfully saved DataFrame with {len(df)} rows to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save parquet file: {e}")
        raise

    # Task B: read back and verify row count
    try:
        df_verify = pd.read_parquet(output_path)
        original_rows = len(df)
        verified_rows = len(df_verify)
        
        if original_rows == verified_rows:
            logger.info(f"Row count verification PASSED: {original_rows} rows saved and verified")
        else:
            logger.error(f"Row count verification FAILED: Original {original_rows}, Verified {verified_rows}")
            raise ValueError("Row count mismatch after save/load")
    except Exception as e:
        logger.error(f"Failed to verify parquet file: {e}")
        raise
    # Task C: log file size comparison (need original CSV path too)

    if csv_path and os.path.exists(csv_path):
        try:
            # Get file sizes in bytes
            csv_size = os.path.getsize(csv_path)
            parquet_size = os.path.getsize(output_path)
            
            # Convert to MB for readability
            csv_size_mb = csv_size / (1024 * 1024)
            parquet_size_mb = parquet_size / (1024 * 1024)
            
            # Calculate compression ratio
            compression_ratio = (1 - parquet_size / csv_size) * 100
            
            logger.info("=" * 50)
            logger.info("FILE SIZE COMPARISON")
            logger.info(f"CSV file size:     {csv_size_mb:.2f} MB")
            logger.info(f"Parquet file size: {parquet_size_mb:.2f} MB")
            logger.info(f"Space saved:       {compression_ratio:.1f}% ({csv_size_mb - parquet_size_mb:.2f} MB)")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.warning(f"Could not compare file sizes: {e}")
    else:
        if csv_path:
            logger.warning(f"CSV file not found for size comparison: {csv_path}")
        else:
            logger.info("No CSV path provided for size comparison")

    # Task D: confirm key column dtypes survived

    try:
        # Define expected dtypes for key columns (adjust based on your dataset)
        key_columns = {
            'date': 'datetime64[us]',  # or 'datetime64[ns]'
            'location': 'str',  # or 'string'
            'mintemp': 'float64',
            'maxtemp': 'float64',
            'rainfall': 'float64',
            'temp_range': 'float64',  # engineered feature
            'is_hot_day': 'bool',
            'season': 'object'
        }

        # Check which key columns exist in the DataFrame
        existing_keys = {col: dtype for col, dtype in key_columns.items() if col in df.columns}
        
        if existing_keys:
            logger.info("Verifying datatype preservation for key columns:")
            dtype_mismatches = []
            
            for col, expected_dtype in existing_keys.items():
                actual_dtype = df_verify[col].dtype
                
                # Special handling for datetime types (they might be 'datetime64[ns]' vs 'datetime64[us]')
                if 'datetime64' in str(expected_dtype) and 'datetime64' in str(actual_dtype):
                    status = "✓"
                    logger.debug(f"  {col}: {actual_dtype} (matches datetime type)")
                elif str(actual_dtype) == expected_dtype or actual_dtype == expected_dtype:
                    status = "✓"
                    logger.debug(f"  {col}: {actual_dtype} (matches)")
                else:
                    status = "✗"
                    dtype_mismatches.append((col, expected_dtype, actual_dtype))
                    logger.warning(f"  {col}: Expected {expected_dtype}, got {actual_dtype}")

            if dtype_mismatches:
                logger.warning(f"Found {len(dtype_mismatches)} datatype mismatches")
            else:
                logger.info("All key column datatypes preserved successfully!")
        else:
            logger.info("No key columns found for dtype verification")
            
    except Exception as e:
        logger.warning(f"Could not verify datatypes: {e}")

    logger.info("Parquet save complete.")
    return output_path

if __name__ == "__main__":
    from extract import extract
    df_raw = extract("weatherAUS.csv")
    df_clean = clean(df_raw)
    df_final = fix_schema(df_clean)
    print(df_final[['date', 'mintemp', 'maxtemp', 'temp_range', 'is_hot_day', 'season']].head(10))


     # Save to Parquet
    save_parquet(
        df_final, 
        output_path="data/weather_cleaned.parquet",
        csv_path="weatherAUS.csv"  # Original CSV for size comparison
    )
    
    
    # print(df_clean.isnull().sum().sum())  # should show all zeros