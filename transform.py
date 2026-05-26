import pandas as pd
import logging

logging.basicConfig(
    filename= "pipeline1.log", 
    format= '%(asctime)s %(setlevel)s : %(message)s',
    filemode = 'w'
    )

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def clean(df):
    logger.info("starting the transformation....")
    # Step 1: find and drop columns > 40% missing
    # Step 2: fill numeric columns with median
    # Step 3: fill text columns with "Unknown"

    logger.info("transformationcomplete.")
    return  df

if __name__ == "__main__":
    from extract import extract
    df_raw = extract("weatherAUS.csv")
    df_clean = clean(df_raw)
    print(df_clean.isnull().sum())  # should show all zeros