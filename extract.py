import pandas as pd
import numpy as np 


#  read  tyeh file using the pandas 
df = pd.read_csv("weatherAUS.csv")

#  providing the size of the file 
size = np.shape(df)
print(size)

# providing the information for the dataset structure  
inf = df.info()
print(inf)


#   providing the first 5 values 

# f_5_ = pd.head(df) --> why this is wrong ? but te below is right 

f_5 = df.head()
print(f_5)


#  providing the mean , std etc
desc = df.describe() 
print(desc)

print(df.isnull().sum())