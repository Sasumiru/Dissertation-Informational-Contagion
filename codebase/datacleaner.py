import os
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity #iimports
TEST1 = "test1" 
DATA = "data" #
PLACEHOLDER = "XXXXXXXXXXXXXX" 

def filterExpose():
    column = ["LEI_Code", "Period", "Item", "NACE_codes", "Amount"] #defining the columns that match the csv
    strType = {
        "LEI_Code": str,
        "Period": str,
        "Item": str,
        "NACE_codes": str,
    }
    df = pd.read_csv(f"data/tr_cre.csv", usecols=column, dtype=strType) #reading the data
    df = df.rename(columns={"LEI_Code": "LEI", "NACE_codes": "NACE", "Amount": "Value"}) #shorter names

    df["Value"] = pd.to_numeric(df["Value"], errors="coerce").fillna(0) #if number isnt number = 0

    startItem = df["Item"] == "2521301" #starting item in the csv file
    startPeriod = df["Period"] == "202506" #starting period in the csv file

    df = df[startItem & startPeriod] 
    df = df[df["NACE"] != 0] # if not a sector we remove it
    df = df[df["LEI"].ne(PLACEHOLDER)]
    return df

if __name__ == "__main__":
    df = filterExpose()
    print(df.head())
    print(len(df))