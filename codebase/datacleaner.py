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
    df = df[df["NACE"] != "0"] # if not a sector we remove it
    df = df[df["LEI"].ne(PLACEHOLDER)]
    return df

def buildMatrix(df):
    # turns bank into table with one row per bank, one column per sector, filled with the exposure amount
    matrix = df.pivot_table(
        index="LEI",       # row
        columns="NACE",   # column
        values="Value",        # value
        aggfunc="sum",          # if bank has more than one row for the same sector, add them up
        fill_value=0.0,         # if a bank has no exposure to a sector, put 0 instead of leaving it blank
    )

    # pivot_table sorts columns as text so re-sort changesthem as numbers instead
    reSort = sorted(matrix.columns, key=int)
    matrix = matrix[reSort]

    return matrix

# bank lookup
def loadMetadata(bankID):
    # read the "List of Institutions"
    inst = pd.read_excel(
        f"data/TR_Metadata.xlsx",
        sheet_name="List of Institutions",
        header=1, #skip 1st row
    )

    # keep columns we actually need
    inst = inst[["LEI_Code", "Name", "Country", "Country_code"]]

    # keep banks in our exposure matrix
    mask = inst["LEI_Code"].isin(bankID)                    # True/False: is this LEI in our list?
    matchBanks = inst[mask]                                # keep only the True rows
    matchBanks = matchBanks.reset_index(drop=True)     # renumber rows 0,1,2... cleanly

    return matchBanks

if __name__ == "__main__":
    df = filterExpose()
    print(df.head())
    print(len(df))
    matrix = buildMatrix(df)
    print(matrix.shape)
    print(matrix.head())
    meta = pd.read_excel("data/TR_Metadata.xlsx", sheet_name=None)  # None = load every sheet
    print(meta.keys())