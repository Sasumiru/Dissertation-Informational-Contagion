import pandas as pd


df = pd.read_csv("data/tr_cre.csv", dtype=str)
print(df.columns.tolist())


sub = df[(df["Item"] == "2521301") & (df["Period"] == "202506") & (df["NACE_codes"] != "0")]
print(sub.groupby(["LEI_Code", "NACE_codes"]).size().value_counts())
print(sub["Perf_Status"].value_counts())
print(sub.groupby(["LEI_Code", "NACE_codes"])["Perf_Status"].nunique().value_counts())
print(sub[["Perf_Status", "Label"]].drop_duplicates())


sub["Amount"] = pd.to_numeric(sub["Amount"], errors="coerce").fillna(0)
wide = sub.pivot_table(index=["LEI_Code", "NACE_codes"], columns="Perf_Status", values="Amount", aggfunc="sum")
print((wide["0"] >= wide[["2", "4", "5"]].max(axis=1)).mean())
print(wide.sum().round(0))

print(wide[wide["0"] < wide[["2", "4", "5"]].max(axis=1)])