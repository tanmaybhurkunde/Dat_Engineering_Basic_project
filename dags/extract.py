# import pandas as pd
# import numpy as np 

# def extract(): 
#     #  read  tyeh file using the pandas 
#     df = pd.read_csv("weatherAUS.csv")

#     #  providing the size of the file 
#     size = np.shape(df)
#     print(size)

#     # providing the information for the dataset structure  
#     inf = df.info()
#     print(inf)

#     #   providing the first 5 values 
    
#     # f_5_ = pd.head(df) --> why this is wrong ? but te below is right 
#     f_5 = df.head()
#     print(f_5)

#     #  providing the mean , std etc
#     desc = df.describe() 
#     print(desc)

#     print(df.isnull().sum())

# extract()

import pandas as pd
import  logging
#   setting the logging confiiguration ------------------
# logging.basicConfig(
#     filename = "pipeline.log",
#     format =' %(asctime)s %(levelname)s :  %(message)s' ,
#     filemode='a'
# )

# Send logs to BOTH console and file
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

# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)

# logger.debug("debug")
# logger.info("info")
# logger.warning("warning")
# logger.error("error")
# logger.critical("critical")

# -------------------------------------------------------

def extract(filepath):
    # print(f"[EXTRACT] Loading file: {filepath}")
    logger.info(f"Loading file : {filepath}")
    
    try:
        df = pd.read_csv(filepath, encoding='utf-8')
    except FileNotFoundError:
        # print(f"[EXTRACT] Error: File '{filepath}' not found. Check your path.")
        logger.error(f"File '{filepath}' not found. Check your path.")
        return None
    except Exception as e:
        # print(f"[EXTRACT] Unexpected error while reading file: {e}")
        logger.error(f"Unexpected error while reading file: {e}")
        return None

    # print(f"[EXTRACT] Successfully loaded {df.shape[0]} rows and {df.shape[1]} columns")
    logger.info(f"Successfully loaded {df.shape[0]} rows and {df.shape[1]} columns")

    total_missing = df.isnull().sum().sum()


    # ---------------------------

    missing_pct = (total_missing / df.size) * 100

    if missing_pct > 10:
        logger.warning(f"High missing data: {missing_pct:.1f}% of dataset is null")
    else:
        logger.info(f"Missing data acceptable: {missing_pct:.1f}%")

    # print(f"[EXTRACT] Total missing values across dataset: {total_missing}")
    # logger.warning(f"Total missing values: {total_missing}")

    # print(f"[EXTRACT] Extract complete.")
    logger.info("Extract complete.")
    return df

# if __name__ == "__main__":
#     df = extract("wrong_file.csv")   # deliberate wrong path

#     if df is not None:
#         print(df.head())

if __name__ == "__main__":
    df = extract("weatherAUS.csv")
    if df is not None:
        print(df.head())